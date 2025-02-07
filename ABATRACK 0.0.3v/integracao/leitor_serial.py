import serial 
from dominio.entidades import *
from aplicacao.use_cases import *

class AdaptadorArduino:
    def __init__(self, repositorio: RepositorioTelemetria, configs: ConfigsComunicacao):
        self.repositorio = repositorio
        self.configs = configs
        self.timeout = 1
        self.conexao = None

    def conectar(self):
        try:
            self.conexao = serial.Serial(self.configs.portaArduino, self.configs.baudRate, timeout=self.timeout)
            print(f"Conexão estabelecida na porta {self.configs.portaArduino} com baud rate {self.configs.baudRate}")
        except serial.SerialException as e:
            print(f"Falha ao conectar na porta {self.configs.portaArduino}: {e}")
            self.conexao = None
            
    def desconectar(self):
        if self.conexao:
            self.conexao.close()

    def lePacoteSerial(self):
        if not self.conexao or not self.conexao.is_open:
            print("Erro: conexão da serial não aberta.")
            return None
        try:
            linha = self.conexao.readline().decode("utf-8").strip()
            print(linha)
            if linha:
                return linha
        except serial.SerialException as e:
            print(f"Erro ao ler a serial: {e}")
            return None
        