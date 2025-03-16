import serial 
from dominio.entidades import *
from aplicacao.use_cases import *
from PyQt6.QtCore import QObject, pyqtSignal

class AdaptadorArduino(QObject):
    erroDecodificacao = pyqtSignal(str)
    erroSerial = pyqtSignal(str)

    def __init__(self, repositorio: RepositorioTelemetria, configs: ConfigsComunicacao):
        super().__init__()
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
            return linha
        except UnicodeDecodeError as e:
            erro_msg = "Erro em formato de dados ou baud rate errada"
            print(erro_msg)
            self.erroDecodificacao.emit(erro_msg)
            return None
        except serial.SerialException as e:
            erro_msg = f"Erro ao ler a serial: {e}"
            print(erro_msg)
            self.erroSerial.emit(erro_msg)
            return None
        
    def enviarComando(self, comando):
        if self.conexao and self.conexao.is_open:
            self.conexao.write(comando.encode())
        else:
            raise Exception("Serial não está conectada")