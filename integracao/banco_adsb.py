"""Banco SQLite do ADS-B: tudo o que o Orange manda, gravado como chegou.

Um arquivo por execucao em dados_salvos/adsb/. A gravacao roda numa thread
propria (a leitura da serial nunca espera o disco), em lotes, com WAL. Cada
linha ORANGE: tambem vai para a tabela log_cru, para a analise poder ser
refeita do zero (HLR-SW-02: dados estruturados, documentados e reproduziveis).
O esquema esta descrito em TABELAS e e gravado em ESQUEMA_adsb.md ao lado.
"""

import os
import queue
import sqlite3
import threading
from datetime import datetime

from integracao.armazenamento_imagens import diretorioImagens

VERSAO_ESQUEMA = 1

# tabela -> [(coluna, tipo SQL, descricao)]. Fonte unica do esquema e da documentacao.
TABELAS = {
    "meta": [
        ("chave", "TEXT PRIMARY KEY", "nome do metadado"),
        ("valor", "TEXT", "valor do metadado"),
    ],
    "aeronaves": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("sessao", "INTEGER NOT NULL", "sessao do Orange (de ACK,START,<n>); 0 se nenhuma foi vista"),
        ("seq", "INTEGER NOT NULL", "contador da linha AC; recomeca a cada START"),
        ("ts", "REAL NOT NULL", "hora do registro no Orange (epoch, segundos); so confiavel se o relogio foi acertado com TIME"),
        ("chegada", "REAL NOT NULL", "hora em que o PC recebeu a linha (epoch, segundos)"),
        ("icao24", "TEXT NOT NULL", "endereco ICAO da aeronave (6 hex)"),
        ("lat", "REAL NOT NULL", "latitude em graus"),
        ("lon", "REAL NOT NULL", "longitude em graus"),
        ("alt_ft", "INTEGER", "altitude em pes"),
        ("gs_kt", "INTEGER", "velocidade em nos"),
        ("rumo_graus", "REAL", "rumo em graus (0 a 360); do ADS-B ou estimado entre duas posicoes"),
        ("rumo_estimado", "INTEGER", "1 se o rumo foi calculado pelo AbaTrack, 0 se veio do ADS-B"),
    ],
    "status_orange": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("estado", "TEXT", "IDLE ou RUNNING"),
        ("modo", "INTEGER", "0 grava e transmite, 1 so grava"),
        ("uptime_s", "INTEGER", "tempo desde que o script do Orange subiu"),
        ("temp_cpu_c", "REAL", "temperatura da CPU do Orange"),
        ("msgs_rx", "INTEGER", "mensagens recebidas pelo receptor"),
        ("msgs_validas", "INTEGER", "mensagens validas"),
        ("aeronaves", "INTEGER", "aeronaves distintas na sessao"),
        ("ac_enviados", "INTEGER", "linhas AC escritas na serial do Orange"),
        ("lat_media_ms", "REAL", "latencia media decodificacao para serial (ms)"),
        ("lat_max_ms", "REAL", "latencia maxima decodificacao para serial (ms)"),
        ("descartados_fila", "INTEGER", "registros descartados na fila do Orange (campo opcional)"),
        ("descartados_tx", "INTEGER", "linhas descartadas na fila da serial (campo opcional)"),
        ("msgs_ident", "INTEGER", "mensagens de identificacao (campo opcional)"),
        ("msgs_pos", "INTEGER", "mensagens de posicao (campo opcional)"),
        ("msgs_vel", "INTEGER", "mensagens de velocidade (campo opcional)"),
        ("relogio_ok", "INTEGER", "1 se o relogio do Orange foi acertado com TIME (campo opcional)"),
    ],
    "opstate": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("estado", "TEXT", "SEM_CONTATO, VIVO ou EXECUTANDO (visto pelo OBC)"),
        ("auto", "INTEGER", "1 se a missao autonoma esta ligada"),
        ("concluida", "INTEGER", "1 se a missao terminou"),
        ("ac_rx", "INTEGER", "linhas AC que o OBC recebeu do Orange"),
        ("ac_perdidos", "INTEGER", "linhas AC descartadas na fila do OBC"),
        ("linhas_ok", "INTEGER", "linhas validas lidas pelo OBC"),
        ("linhas_invalidas", "INTEGER", "linhas invalidas lidas pelo OBC"),
    ],
    "eventos": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("tipo", "TEXT", "BOOT, SDR_OK, SDR_ERR, DONE, OP_SILENCIO..."),
        ("args", "TEXT", "campos restantes, separados por virgula"),
    ],
    "confirmacoes": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("tipo", "TEXT", "ACK ou NAK"),
        ("comando", "TEXT", "comando confirmado ou recusado"),
        ("args", "TEXT", "campos restantes, separados por virgula"),
    ],
    "vereditos": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("lat", "REAL", "latitude da aeronave clandestina (ADS-B)"),
        ("lon", "REAL", "longitude da aeronave clandestina (ADS-B)"),
        ("foto", "INTEGER", "numero da foto, se a linha trouxer"),
    ],
    "log_cru": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT", "identificador da linha"),
        ("chegada", "REAL NOT NULL", "hora de chegada no PC (epoch)"),
        ("tipo", "TEXT", "tipo reconhecido ou INVALIDA"),
        ("valida", "INTEGER", "1 se a linha foi interpretada, 0 se estava malformada"),
        ("linha", "TEXT", "a linha ORANGE: exatamente como chegou"),
    ],
}

RESTRICOES = {"aeronaves": ["UNIQUE (sessao, seq)"]}

INDICES = (
    "CREATE INDEX IF NOT EXISTS idx_aeronaves_icao_ts ON aeronaves (icao24, ts)",
    "CREATE INDEX IF NOT EXISTS idx_aeronaves_chegada ON aeronaves (chegada)",
    "CREATE INDEX IF NOT EXISTS idx_log_cru_chegada ON log_cru (chegada)",
)


def criarTabelaSql(nome):
    colunas = [f"{c} {t}" for c, t, _ in TABELAS[nome]] + RESTRICOES.get(nome, [])
    return f"CREATE TABLE IF NOT EXISTS {nome} ({', '.join(colunas)})"


def esquemaMarkdown() -> str:
    """Dicionario de dados em Markdown, gerado de TABELAS."""
    linhas = ["# Banco de dados do ADS-B (AbaTrack)", "",
              f"Versao do esquema: {VERSAO_ESQUEMA}. Um arquivo `.db` (SQLite) por execucao.",
              "Horas em epoch (segundos desde 1970). `chegada` e a hora do PC; `ts` e a do Orange.", ""]
    for nome, colunas in TABELAS.items():
        linhas += [f"## {nome}", "", "| Coluna | Tipo | Descricao |", "| --- | --- | --- |"]
        linhas += [f"| `{c}` | {t} | {d} |" for c, t, d in colunas]
        extras = RESTRICOES.get(nome)
        if extras:
            linhas += ["", "Restricoes: " + "; ".join(extras) + ". Linhas repetidas (por exemplo, reenviadas pelo DUMP) sao ignoradas."]
        linhas.append("")
    return "\n".join(linhas)


def diretorioAdsb():
    """dados_salvos/adsb/ ao lado de dados_salvos/imagens/ (e do executavel)."""
    return os.path.join(os.path.dirname(diretorioImagens()), "adsb")


class BancoAdsb:
    def __init__(self, pasta, lote=200):
        os.makedirs(pasta, exist_ok=True)
        self.pasta = pasta
        agora = datetime.now()
        self.caminho = os.path.join(pasta, f"adsb_{agora.strftime('%Y-%m-%d_%H-%M-%S')}.db")
        self.erros = 0
        self._lote = lote
        self._fila = queue.Queue()
        arquivoEsquema = os.path.join(pasta, "ESQUEMA_adsb.md")
        if not os.path.exists(arquivoEsquema):
            with open(arquivoEsquema, "w", encoding="utf-8") as f:
                f.write(esquemaMarkdown())
        self._thread = threading.Thread(target=self._executar, args=(agora,),
                                        name="banco-adsb", daemon=True)
        self._thread.start()

    # ------------------------------------------------------------- API
    def registrar(self, msg, sessao=0):
        """Enfileira a mensagem; a gravacao acontece na thread do banco."""
        self._fila.put((msg, sessao))

    def descarregar(self):
        """Espera tudo o que ja foi enfileirado chegar ao arquivo."""
        self._fila.join()

    def fechar(self):
        self._fila.put(None)
        self._thread.join(10)

    # ---------------------------------------------------------- thread
    def _executar(self, criadoEm):
        con = sqlite3.connect(self.caminho)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        for nome in TABELAS:
            con.execute(criarTabelaSql(nome))
        for sql in INDICES:
            con.execute(sql)
        con.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", [
            ("versao_esquema", str(VERSAO_ESQUEMA)),
            ("software", "AbaTrack"),
            ("criado_em", criadoEm.isoformat(timespec="seconds")),
            ("origem", "linhas ORANGE: impressas pela base (firmware do OBC)"),
        ])
        con.commit()

        encerrar = False
        while not encerrar:
            itens = [self._fila.get()]
            while len(itens) < self._lote:
                try:
                    itens.append(self._fila.get_nowait())
                except queue.Empty:
                    break
            for item in itens:
                if item is None:
                    encerrar = True
                    continue
                try:
                    self._gravar(con, *item)
                except Exception as e:  # nao pode derrubar a thread
                    self.erros += 1
                    print(f"Erro ao gravar no banco do ADS-B: {e}")
            con.commit()
            # Passa o WAL para o .db a cada lote: o arquivo .db sozinho ja tem os
            # dados, entao pode ser copiado durante a missao sem o -wal.
            con.execute("PRAGMA wal_checkpoint(PASSIVE)")
            for _ in itens:
                self._fila.task_done()
        con.close()

    @staticmethod
    def _gravar(con, msg, sessao):
        d = msg.dados
        tipo = msg.tipo
        if tipo == "AC":
            con.execute(
                "INSERT OR IGNORE INTO aeronaves (sessao, seq, ts, chegada, icao24, lat, lon, "
                "alt_ft, gs_kt, rumo_graus, rumo_estimado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (sessao, d.seq, d.ts, msg.chegada, d.icao24, d.latitude, d.longitude,
                 d.altitudeFt, d.velocidadeKt, d.rumo, int(d.rumoEstimado)))
        elif tipo == "STATUS":
            colunas = [c for c, _, _ in TABELAS["status_orange"][2:]]
            con.execute(
                f"INSERT INTO status_orange (chegada, {', '.join(colunas)}) "
                f"VALUES (?{', ?' * len(colunas)})",
                (msg.chegada, *[d.get(c) for c in colunas]))
        elif tipo == "OPSTATE":
            colunas = [c for c, _, _ in TABELAS["opstate"][2:]]
            con.execute(
                f"INSERT INTO opstate (chegada, {', '.join(colunas)}) "
                f"VALUES (?{', ?' * len(colunas)})",
                (msg.chegada, *[d.get(c) for c in colunas]))
        elif tipo == "EVT":
            con.execute("INSERT INTO eventos (chegada, tipo, args) VALUES (?,?,?)",
                        (msg.chegada, d["tipo"], ",".join(d["args"])))
        elif tipo in ("ACK", "NAK"):
            con.execute("INSERT INTO confirmacoes (chegada, tipo, comando, args) VALUES (?,?,?,?)",
                        (msg.chegada, tipo, d["comando"], ",".join(d["args"])))
        elif tipo == "VEREDITO":
            con.execute(
                "INSERT INTO vereditos (chegada, lat, lon, foto) VALUES (?,?,?,?)",
                (msg.chegada, d.latitude, d.longitude, d.indiceFoto))
        con.execute("INSERT INTO log_cru (chegada, tipo, valida, linha) VALUES (?,?,?,?)",
                    (msg.chegada, tipo, 0 if tipo == "INVALIDA" else 1, msg.bruta))
