"""Parser do protocolo de imagem emitido pela estacao de solo na serial.

    IMAGE_BEGIN
    SIZE:<n>
    <n bytes crus do JPEG>
    IMAGE_END

A mesma porta carrega telemetria (e debug) em texto intercalada com as imagens.
Por isso o JPEG e lido por CONTAGEM de bytes, nunca por linha: bytes como
'\\n', '\\r' ou ate a string "IMAGE_END" dentro do JPEG nao quebram nada.

Baseado em sat_protocol.py do repositorio Computador-de-bordo-2026.

Eventos (callback aoEvento(tipo, dado)):
    ('linha', str)            linha de texto fora de imagem (telemetria/debug)
    ('linha_invalida', None)  linha que nao e UTF-8 (lixo / baud rate errada)
    ('inicio', None)          detectou IMAGE_BEGIN
    ('tamanho', int)          tamanho anunciado da imagem
    ('progresso', (lidos, total))
    ('completa', bytes)       imagem completa
    ('erro', str)             protocolo invalido; o parser volta a procurar
"""

TAMANHO_MAXIMO_IMAGEM = 200000  # rejeita SIZE absurdo (ruido/dessincronia)
TAMANHO_MAXIMO_LINHA = 4096     # linha sem '\n' maior que isso e descartada

BUSCANDO = "BUSCANDO"                  # procurando IMAGE_BEGIN / repassando texto
ESPERANDO_TAMANHO = "ESPERANDO_TAMANHO"  # aguardando a linha SIZE:<n>
LENDO_BYTES = "LENDO_BYTES"            # lendo n bytes crus
ESPERANDO_FIM = "ESPERANDO_FIM"        # aguardando IMAGE_END


class ProtocoloImagem:
    def __init__(self, aoEvento=None):
        self.aoEvento = aoEvento
        self.estado = BUSCANDO
        self._buffer = bytearray()
        self._esperado = 0
        self._imagem = bytearray()

    @property
    def recebendoImagem(self):
        return self.estado != BUSCANDO

    def reiniciar(self):
        """Descarta tudo (usar ao abrir uma nova conexao)."""
        self._buffer.clear()
        self._resetarImagem()

    def abortar(self, motivo):
        """Abandona a imagem em andamento (ex.: timeout sem receber bytes)."""
        if self.recebendoImagem:
            self._emitir("erro", motivo)
            self._resetarImagem()

    def alimentar(self, dados: bytes):
        """Alimenta bytes em pedacos arbitrarios; devolve as imagens completas."""
        if dados:
            self._buffer.extend(dados)
        completas = []

        avancou = True
        while avancou:
            avancou = False

            if self.estado == LENDO_BYTES:
                faltam = self._esperado - len(self._imagem)
                if faltam > 0:
                    if not self._buffer:
                        break
                    pedaco = self._buffer[:faltam]
                    del self._buffer[:len(pedaco)]
                    self._imagem.extend(pedaco)
                    self._emitir("progresso", (len(self._imagem), self._esperado))
                    avancou = True
                if len(self._imagem) >= self._esperado:
                    self.estado = ESPERANDO_FIM
                    avancou = True
                continue

            # Estados baseados em linha
            bruto = self._proximaLinha()
            if bruto is None:
                break
            avancou = True
            linha = self._decodificar(bruto)

            if self.estado == BUSCANDO:
                self._tratarBusca(bruto, linha)
            elif self.estado == ESPERANDO_TAMANHO:
                self._tratarTamanho(linha)
            elif self.estado == ESPERANDO_FIM:
                imagem = self._tratarFim(linha)
                if imagem is not None:
                    completas.append(imagem)

        return completas

    # ------------------------------------------------------------ internos
    def _emitir(self, tipo, dado=None):
        if self.aoEvento is not None:
            self.aoEvento(tipo, dado)

    def _resetarImagem(self):
        self._esperado = 0
        self._imagem = bytearray()
        self.estado = BUSCANDO

    def _proximaLinha(self):
        """Remove e devolve a proxima linha crua (sem o '\\n'), ou None se ainda
        nao ha linha completa. Descarta lixo se a linha passar do limite."""
        indice = self._buffer.find(b"\n")
        if indice == -1:
            if len(self._buffer) > TAMANHO_MAXIMO_LINHA:
                self._buffer.clear()
                if self.estado == BUSCANDO:
                    self._emitir("linha_invalida")
                else:
                    self._emitir("erro", "linha de protocolo grande demais")
                    self._resetarImagem()
            return None
        bruto = bytes(self._buffer[:indice])
        del self._buffer[:indice + 1]
        return bruto

    @staticmethod
    def _resumo(linha):
        """Trecho curto e so-ASCII da linha, seguro para mensagens e console."""
        return ascii((linha or "")[:40])

    @staticmethod
    def _decodificar(bruto):
        try:
            return bruto.decode("utf-8").strip()
        except UnicodeDecodeError:
            return None

    def _tratarBusca(self, bruto, linha):
        if linha is None:
            self._emitir("linha_invalida")
        elif linha == "IMAGE_BEGIN":
            self._imagem = bytearray()
            self.estado = ESPERANDO_TAMANHO
            self._emitir("inicio")
        elif linha != "":
            self._emitir("linha", linha)

    def _tratarTamanho(self, linha):
        if linha is not None and linha.startswith("SIZE:"):
            try:
                n = int(linha[5:])
            except ValueError:
                n = -1
            if 0 < n <= TAMANHO_MAXIMO_IMAGEM:
                self._esperado = n
                self.estado = LENDO_BYTES
                self._emitir("tamanho", n)
                return
            self._emitir("erro", f"SIZE invalido: {self._resumo(linha)}")
        else:
            self._emitir("erro", f"esperava SIZE, veio: {self._resumo(linha)}")
        self._resetarImagem()
        # A linha inesperada pode ser texto util; nao a descarta.
        if linha and linha != "IMAGE_BEGIN":
            self._emitir("linha", linha)

    def _tratarFim(self, linha):
        if linha == "IMAGE_END":
            imagem = bytes(self._imagem)
            self._emitir("completa", imagem)
            self._resetarImagem()
            return imagem
        if linha == "":
            return None  # linha em branco antes do IMAGE_END e aceita
        self._emitir("erro", f"esperava IMAGE_END, veio: {self._resumo(linha)}")
        self._resetarImagem()
        if linha and linha != "IMAGE_BEGIN":
            self._emitir("linha", linha)
        return None
