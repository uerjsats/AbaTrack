from collections import namedtuple

# Esquema do pacote de telemetria: UMA fonte da verdade para a ordem dos campos.
# Cada campo diz em quais listas do RepositorioTelemetria o valor e guardado.
# Ao inserir um campo novo, basta coloca-lo aqui na posicao certa (e criar a
# lista no repositorio); o resto do software e o README seguem a mesma ordem.
Campo = namedtuple("Campo", ["chave", "nome", "unidade", "listas"])

CAMPOS_PACOTE = (
    Campo("tempo", "Tempo", "s (segundos)", ("tempo", "tempo1")),
    Campo("temperatura", "Temperatura", "°C", ("dadosTemperatura",)),
    Campo("umidade", "Umidade", "%", ("umidade",)),
    Campo("altitude", "Altitude", "m (metros)", ("altitude", "altitude1")),
    Campo("pressao", "Pressão", "Pa (Pascal)", ("pressao", "pressao1")),
    Campo("latitude", "Latitude", "graus decimais", ("latitude",)),
    Campo("longitude", "Longitude", "graus decimais", ("longitude",)),
    Campo("satelites", "Número de Satélites", "quantidade", ("sats",)),
    Campo("roll", "Roll (Giro X)", "graus", ("roll",)),
    Campo("pitch", "Pitch (Giro Y)", "graus", ("pitch",)),
    Campo("yaw", "Yaw (Giro Z)", "graus", ("yaw",)),
    Campo("angulo_ldr", "Ângulo LDR", "graus", ("anguloldr",)),
    Campo("temp_bateria1", "Temperatura Bateria 1", "°C", ("tempbateria1",)),
    Campo("temp_bateria2", "Temperatura Bateria 2", "°C", ("tempbateria2",)),
    Campo("tensao", "Tensão", "V", ("voltage",)),
    Campo("corrente", "Corrente", "A", ("current",)),
    Campo("num_pacotes", "Número de Pacotes", "quantidade", ("numerodepacotes",)),
    Campo("rssi", "RSSI", "dBm (sinal do rádio)", ("RSSI",)),
    Campo("tamanho_pacote", "Tamanho do Pacote", "bytes", ("tamanhopacote",)),
)

# chave do campo -> posicao no vetor do pacote (tabela hash em vez de indices magicos)
INDICE_CAMPO = {campo.chave: i for i, campo in enumerate(CAMPOS_PACOTE)}


class RepositorioTelemetria:
    def __init__(self):
        self.pacotesDados = []
        self.dadosTemperatura = []
        self.tempo = []
        self.tempo1 = []
        self.umidade = []
        self.pressao = []
        self.pressao1 = []
        self.altitude = []
        self.altitude1 = []
        self.numerodepacotes = []
        self.RSSI = []
        self.tamanhopacote = []
        self.latitude = []
        self.longitude = []

        # NOVO: armazena a velocidade calculada a partir do GPS.
        # Unidade recomendada: km/h.
        self.velocidade = []

        self.sats = []
        self.roll = []
        self.pitch = []
        self.yaw = []
        self.anguloldr = []
        self.tempbateria1 = []
        self.tempbateria2 = []
        self.voltage = []
        self.current = []
        self.imagens = []

    def __str__(self):
        if self.pacotesDados:
            return "\n".join(self.pacotesDados)
        else:
            return "Nenhum dado registrado no repositorio."


class ImagemTelemetria:
    """Imagem JPEG recebida da estacao de solo.

    indicePacote e a posicao, em RepositorioTelemetria.pacotesDados, do ultimo
    pacote de telemetria recebido quando a imagem chegou (None se ainda nao
    havia nenhum). Serve para saber onde o satelite estava nesse momento.
    """

    def __init__(self, dadosJpeg: bytes, horario, caminho=None, indicePacote=None):
        self.dadosJpeg = dadosJpeg
        self.horario = horario
        self.caminho = caminho
        self.indicePacote = indicePacote

    @property
    def tamanho(self):
        return len(self.dadosJpeg)


class ConfigsComunicacao:
    def __init__(self, portaArduino, baudRate):
        self.portaArduino = portaArduino
        self.baudRate = baudRate

    def __str__(self):
        return f"Porta: {self.portaArduino} Baud Rate: {self.baudRate}"
