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
        self.tempbateria1 = []
        self.tempbateria2 = []
        self.voltage = []
        self.current = []

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