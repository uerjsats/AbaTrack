import collections
import time

import serial 
from dominio.entidades import *
from aplicacao.use_cases import *
from integracao.protocolo_imagem import ProtocoloImagem
from PyQt5.QtCore import QObject, pyqtSignal

# Linhas seguidas que nao sao UTF-8 antes de avisar "baud rate errada". O valor
# e alto para nao disparar ao conectar no meio de uma imagem (~80 quebras de linha).
LIMITE_LINHAS_INVALIDAS = 150
# Segundos sem receber bytes no meio de uma imagem antes de abandona-la.
TIMEOUT_IMAGEM = 5

def imprimirSeguro(texto):
    """print que nunca levanta, mesmo com caracteres que o console nao aceita."""
    try:
        print(texto)
    except (UnicodeEncodeError, OSError):
        pass

class AdaptadorArduino(QObject):
    erroDecodificacao = pyqtSignal(str)
    erroSerial = pyqtSignal(str)
    imagemRecebida = pyqtSignal(bytes)
    progressoImagem = pyqtSignal(int, int)
    erroImagem = pyqtSignal(str)

    def __init__(self, repositorio: RepositorioTelemetria, configs: ConfigsComunicacao):
        super().__init__()
        self.repositorio = repositorio
        self.configs = configs
        self.timeout = 1
        self.conexao = None
        self.protocolo = ProtocoloImagem(self._tratarEvento)
        self._linhas = collections.deque()
        self._linhasInvalidas = 0
        self._ultimoByte = time.monotonic()

    def conectar(self):
        if not self.configs.portaArduino:
            raise serial.SerialException("Nenhuma porta selecionada.")
        try:
            self.conexao = serial.Serial(self.configs.portaArduino, self.configs.baudRate, timeout=self.timeout)
            self.protocolo.reiniciar()
            self._linhas.clear()
            self._linhasInvalidas = 0
            print(f"Conexão estabelecida na porta {self.configs.portaArduino} com baud rate {self.configs.baudRate}")
        except serial.SerialException as e:
            print(f"Falha ao conectar na porta {self.configs.portaArduino}: {e}")
            self.conexao = None
            
    def desconectar(self):
        if self.conexao:
            self.conexao.close()

    def _tratarEvento(self, tipo, dado):
        if tipo == "linha":
            self._linhasInvalidas = 0
            self._linhas.append(dado)
        elif tipo == "linha_invalida":
            self._linhasInvalidas += 1
            if self._linhasInvalidas == LIMITE_LINHAS_INVALIDAS:
                erro_msg = "Erro em formato de dados ou baud rate errada"
                print(erro_msg)
                self.erroDecodificacao.emit(erro_msg)
        elif tipo == "progresso":
            self.progressoImagem.emit(*dado)
        elif tipo == "completa":
            self._linhasInvalidas = 0
            self.imagemRecebida.emit(dado)
        elif tipo == "erro":
            imprimirSeguro(f"Erro na imagem: {dado}")
            self.erroImagem.emit(dado)

    def lePacoteSerial(self):
        """Devolve a proxima linha de telemetria, ou None se nao chegou nenhuma
        em ate `timeout` segundos. Os bytes de imagem que vierem no meio do
        stream sao separados e entregues pelos sinais de imagem."""
        if not self.conexao or not self.conexao.is_open:
            print("Erro: conexão da serial não aberta.")
            return None

        try:
            limite = time.monotonic() + self.timeout
            while not self._linhas and time.monotonic() < limite:
                dados = self.conexao.read(max(1, self.conexao.in_waiting))
                agora = time.monotonic()
                if dados:
                    self._ultimoByte = agora
                    self.protocolo.alimentar(dados)
                elif (self.protocolo.recebendoImagem
                        and agora - self._ultimoByte > TIMEOUT_IMAGEM):
                    self.protocolo.abortar("timeout: imagem interrompida")

            if not self._linhas:
                return None
            linha = self._linhas.popleft()
            imprimirSeguro(linha)
            return linha

        except (serial.SerialException, OSError) as e:
            erro_msg = f"Erro ao ler a serial: {e}"
            print(erro_msg)
            self.erroSerial.emit(erro_msg)
            return None
        
    def enviarComando(self, comando):
        if self.conexao and self.conexao.is_open:
            self.conexao.write(comando.encode())
        else:
            raise Exception("Serial não está conectada")