class RepositorioTelemetria:
    def __init__(self):
        self.pacotesDados = []
        self.dadosTemperatura = []
        self.tempo = []
        self.tempo1 = []
        self.pressao = []
        self.altitude = []
        self.numerodepacotes = []
        self.RSSI = []
        self.tamanhopacote = []
        self.latitude = []
        self.longitude = []
        self.sats = []

    def __str__(self):
        if self.pacotesDados:
            return "\n".join(self.pacotesDados)
        else:
            return "Nenhum dado registrado no repositorio."

class ConfigsComunicacao: 
    def __init__(self, portaArduino, baudRate):
        self.portaArduino = portaArduino
        self.baudRate = baudRate
    
    def __str__(self):
        return (f"Porta: {self.portaArduino} Baud Rate: {self.baudRate}")