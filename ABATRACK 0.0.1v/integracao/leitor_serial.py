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
            print(f"Conexão estabelecida. Porta: {self.configs.portaArduino} BaudRate: {self.configs.baudRate}")
        except serial.SerialException as e:
            print(f"Erro na conexão: {e}")

    def desconectar(self):
        if self.conexao:
            self.conexao.close()
            print("Conexão fechada")

    def lePacoteSerial(self):
        if not self.conexao or not self.conexao.is_open:
            print("Erro: conexão da serial não aberta.")
            return None
        try:
            linha = self.conexao.readline().decode("utf-8").strip()
            if linha:
                return linha
        except serial.SerialException as e:
            print(f"Erro ao ler a serial: {e}")
            return None
        