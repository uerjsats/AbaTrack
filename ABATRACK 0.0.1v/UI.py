import sys
import time
from aplicacao.use_cases import *
from dominio.entidades import *
from integracao.leitor_serial import *
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QLabel, QComboBox, QPushButton)
from PyQt6.QtCore import QThread, pyqtSignal

class LeitorSerialThread(QThread):
    dadoRecebido = pyqtSignal(str)  # Sinal para enviar os dados para a UI

    def __init__(self, adaptador):
        super().__init__()
        self.adaptador = adaptador
        self.rodando = True

    def run(self):
        while self.rodando:
            # Lê pacote da serial
            pacote = self.adaptador.lePacoteSerial()
            if pacote:
                self.dadoRecebido.emit(pacote) 
            time.sleep(0.5)

    def parar(self):
        self.rodando = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AbaTrack")
        self.setFixedSize(600, 400)

        # Instâncias dos componentes da aplicação
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino="COM3", baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.threadLeitura = None

        # Widget central para aplicar o layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Label pra mostrar dados
        self.labelDados = QLabel("Dados não recebidos", self)
        self.layout.addWidget(self.labelDados)

        # ComboBox pra seleção da porta
        self.comboPorta = QComboBox(self)
        self.comboPorta.addItems(["COM3", "COM2"])
        self.comboPorta.currentTextChanged.connect(self.escolherPorta)
        self.layout.addWidget(self.comboPorta)

        # ComboBox pra selecionar baud rate
        self.comboBaudRate = QComboBox(self)
        self.comboBaudRate.addItems(["9600", "115200"])
        self.comboBaudRate.currentTextChanged.connect(self.escolherBaudRate)
        self.layout.addWidget(self.comboBaudRate)

        # Botão pra conectar ao Arduino
        self.botaoConectar = QPushButton("Conectar", self)
        self.botaoConectar.clicked.connect(self.pressionarConectar)
        self.layout.addWidget(self.botaoConectar)

        # Botão pra desconectar do Arduino
        self.botaoDesconectar = QPushButton("Desconectar", self)
        self.botaoDesconectar.clicked.connect(self.pressionarDesconectar)
        self.layout.addWidget(self.botaoDesconectar)

        # Botão pra salvar dados no TXT
        self.botaoSalvar = QPushButton("Salvar Dados", self)
        self.botaoSalvar.clicked.connect(self.salvarDados)
        self.layout.addWidget(self.botaoSalvar)

    def escolherPorta(self):
        porta = self.comboPorta.currentText()
        if porta:
            self.configs.portaArduino = porta
            print(f"Porta selecionada: {porta}")

    def escolherBaudRate(self):
        baud_rate = self.comboBaudRate.currentText()
        if baud_rate.isdigit():
            self.configs.baudRate = int(baud_rate)
            print(f"Baud rate selecionado: {self.configs.baudRate}")

    def pressionarConectar(self):
        try:
            self.adaptador.conectar()
            self.botaoConectar.setEnabled(False)
            self.botaoDesconectar.setEnabled(True)
            print("Conectado ao Arduino.")
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            self.pressionarDesconectar()

    def pressionarDesconectar(self):
        self.adaptador.desconectar()
        self.botaoConectar.setEnabled(True)
        self.botaoDesconectar.setEnabled(False)
        print("Desconectado do Arduino.")

    def salvarDados(self):
        salvarDadosTXT(self.repositorio)

    def iniciarLeitura(self):
        self.adaptador.conectar()
        if self.threadLeitura is None or not self.threadLeitura.isRunning():
            self.threadLeitura = LeitorSerialThread(self.adaptador)
            self.threadLeitura.dadoRecebido.connect(self.atualizarLabel)
            self.threadLeitura.start()

    def atualizarLabel(self, dado):
        self.labelDados.setText(processarPacoteDeDados(dado))
        adicionarPacoteRepositorio(dado, self.repositorio)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MainWindow()
    janela.show()
    app.exec()
