"""Grava a telemetria dos sensores num CSV, um pacote por vez, assim que chega.

Antes a telemetria so ia para arquivo quando o usuario mandava salvar ou ao
fechar o AbaTrack: se o programa travasse ou a serial caisse (por exemplo
durante o teste de vibracao), o que ja tinha chegado se perdia. Aqui cada pacote
e gravado e forcado para o disco na hora, numa thread propria (a leitura da
serial e a janela nunca esperam o disco).

Um arquivo por execucao: dados_salvos/telemetria/telemetria_AAAA-MM-DD_HH-MM-SS.csv
"""

import csv
import os
import queue
import threading
import time
from datetime import datetime

from aplicacao.bateria import temperaturaBateriaMedia
from dominio.entidades import CAMPOS_PACOTE, INDICE_CAMPO
from integracao.armazenamento_imagens import diretorioImagens

CABECALHO = ("chegada_pc",) + tuple(c.chave for c in CAMPOS_PACOTE) + ("temp_bateria_media",)


def diretorioTelemetria():
    """dados_salvos/telemetria/ ao lado das pastas de imagens e do ADS-B."""
    return os.path.join(os.path.dirname(diretorioImagens()), "telemetria")


def esquemaMarkdown() -> str:
    linhas = [
        "# Telemetria dos sensores (CSV)",
        "",
        "Uma linha por pacote recebido, na ordem de chegada. Gravada assim que o pacote chega.",
        "",
        "| Coluna | Descricao | Unidade |",
        "|---|---|---|",
        "| chegada_pc | hora em que o PC recebeu o pacote (AAAA-MM-DD HH:MM:SS.mmm) | data e hora local |",
    ]
    for c in CAMPOS_PACOTE:
        linhas.append(f"| {c.chave} | {c.nome} | {c.unidade} |")
    linhas.append("| temp_bateria_media | media dos dois sensores de bateria; se um mandou -127 "
                  "(falha), vale so o outro; vazio se os dois falharam | °C |")
    return "\n".join(linhas) + "\n"


def _hora(epoch):
    try:
        return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    except (OverflowError, OSError, ValueError, TypeError):
        return ""


class LogTelemetria:
    def __init__(self, pasta=None, lote=100):
        pasta = pasta or diretorioTelemetria()
        os.makedirs(pasta, exist_ok=True)
        agora = datetime.now()
        self.caminho = os.path.join(pasta, f"telemetria_{agora.strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        self.erros = 0
        self._lote = lote
        self._fila = queue.Queue()
        arquivoEsquema = os.path.join(pasta, "ESQUEMA_telemetria.md")
        if not os.path.exists(arquivoEsquema):
            try:
                with open(arquivoEsquema, "w", encoding="utf-8") as f:
                    f.write(esquemaMarkdown())
            except OSError:
                pass
        self._thread = threading.Thread(target=self._executar, name="log-telemetria", daemon=True)
        self._thread.start()

    # ------------------------------------------------------------- API
    def registrar(self, pacote, chegada=None):
        """Enfileira um pacote (lista de valores na ordem de CAMPOS_PACOTE)."""
        self._fila.put((time.time() if chegada is None else chegada, list(pacote)))

    def descarregar(self):
        """Espera tudo o que ja foi enfileirado chegar ao arquivo."""
        self._fila.join()

    def fechar(self):
        self._fila.put(None)
        self._thread.join(10)

    # ---------------------------------------------------------- thread
    def _linha(self, chegada, pacote):
        valores = list(pacote)[:len(CAMPOS_PACOTE)]
        valores += [""] * (len(CAMPOS_PACOTE) - len(valores))
        media = temperaturaBateriaMedia(valores[INDICE_CAMPO["temp_bateria1"]],
                                        valores[INDICE_CAMPO["temp_bateria2"]])
        return [_hora(chegada)] + valores + ["" if media is None else round(media, 2)]

    def _executar(self):
        arquivo = open(self.caminho, "w", newline="", encoding="utf-8")
        escritor = csv.writer(arquivo)
        escritor.writerow(CABECALHO)
        arquivo.flush()

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
                    escritor.writerow(self._linha(*item))
                except Exception as e:  # um pacote ruim nao pode derrubar o log
                    self.erros += 1
                    print(f"Erro ao gravar a telemetria: {e}")
            try:
                arquivo.flush()
                os.fsync(arquivo.fileno())   # sobrevive a queda do programa ou do computador
            except OSError as e:
                self.erros += 1
                print(f"Erro ao forcar a telemetria para o disco: {e}")
            for _ in itens:
                self._fila.task_done()
        arquivo.close()
