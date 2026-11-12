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
        self.deteccoes = []
        # Missao ADS-B (mensagens ORANGE: da base)
        self.aeronaves = {}           # icao24 -> ultimo RegistroAeronave
        self.trilhas = {}             # icao24 -> deque dos ultimos RegistroAeronave
        self.registrosAdsb = []       # todos os RegistroAeronave, sem duplicados
        self.chavesAdsb = set()       # (sessao, seq) ja guardados, para ignorar repeticoes
        self.statusOrange = None      # dict do ultimo STATUS
        self.opstateOrange = None     # dict do ultimo OPSTATE
        self.eventosOrange = []       # (chegada, tipo, args)
        self.confirmacoesOrange = []  # (chegada, "ACK" ou "NAK", comando, args)
        self.sessaoOrange = 0         # numero da sessao, de ACK,START,<n>

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
        self.deteccao = None  # DeteccaoAeronave associada (missao secundaria)

    @property
    def tamanho(self):
        return len(self.dadosJpeg)

class DeteccaoAeronave:
    """Aeronave clandestina detectada pela missao secundaria (o OBC so envia
    essa situacao). indiceFoto e o photo_index do ESP32, quando a linha o traz
    (o VEREDITO nao traz: None). latitude e longitude sao as do ADS-B
    consultado. imagem e preenchida quando a foto dessa deteccao chega.
    """
    def __init__(self, indiceFoto, latitude: float, longitude: float, horario):
        self.indiceFoto = indiceFoto
        self.latitude = latitude
        self.longitude = longitude
        self.horario = horario
        self.imagem = None  # ImagemTelemetria associada


TAMANHO_TRILHA = 120  # posicoes guardadas por aeronave para desenhar o rastro


class RegistroAeronave:
    """Uma linha AC do Orange: estado de uma aeronave num instante.

    ts e a hora do Orange (epoch) e chegada a hora em que o PC recebeu a linha.
    rumo vem do ADS-B (opcional); se faltar, o AbaTrack o estima entre duas
    posicoes e marca rumoEstimado.
    """
    def __init__(self, seq: int, ts: float, icao24: str, latitude: float,
                 longitude: float, altitudeFt: int, velocidadeKt: int,
                 rumo=None, chegada=None, sessao: int = 0):
        self.seq = seq
        self.ts = ts
        self.icao24 = icao24
        self.latitude = latitude
        self.longitude = longitude
        self.altitudeFt = altitudeFt
        self.velocidadeKt = velocidadeKt
        self.rumo = rumo
        self.rumoEstimado = False
        self.chegada = chegada
        self.sessao = sessao

    @property
    def latencia(self):
        """Segundos entre o registro no Orange e a chegada no PC (None sem relogio)."""
        return None if self.chegada is None else self.chegada - self.ts


class ConfigsComunicacao: 
    def __init__(self, portaArduino, baudRate):
        self.portaArduino = portaArduino
        self.baudRate = baudRate
    
    def __str__(self):
        return (f"Porta: {self.portaArduino} Baud Rate: {self.baudRate}")