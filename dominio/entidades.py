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
        return (f"Porta: {self.portaArduino} Baud Rate: {self.baudRate}")