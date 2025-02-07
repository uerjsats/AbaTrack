import os
import sys
from datetime import datetime  
import time  
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsDropShadowEffect, QFileDialog, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap
import serial.tools.list_ports

# Adicione o diretório 'integracao' ao sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integracao'))

from aplicacao.use_cases import *
from dominio.entidades import *
from integracao.leitor_serial import *
from integracao.graficos import GraficoDinamico  

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
        self.setWindowOpacity(0.95)
        
        # Caminho relativo para o ícone e a imagem
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "imgs/AbaTrack.ico")
        image_path = os.path.join(base_path, "imgs/AbaTrack.png")
        
        self.setWindowIcon(QIcon(icon_path))
        self.resize(600, 700)  # Define o tamanho inicial da janela, mas permite redimensionamento

        # Cria o layout para adicionar a imagem logo abaixo da barra superior
        self.layoutImagem = QVBoxLayout()

        # Cria o QLabel para a imagem
        self.imagemTitulo = QLabel(self)
        self.imagemTitulo.setScaledContents(True)
        self.imagemTitulo.setFixedSize(179, 55)
        pixmap = QPixmap(image_path)  # Substitua pelo caminho da sua imagem
        self.imagemTitulo.setPixmap(pixmap)
        self.imagemTitulo.setGraphicsEffect(QGraphicsDropShadowEffect())

        # Layout para centralizar a imagem
        self.layoutImagemCentral = QHBoxLayout()
        self.layoutImagemCentral.addStretch()
        self.layoutImagemCentral.addWidget(self.imagemTitulo)
        self.layoutImagemCentral.addStretch()

        # Adiciona a imagem ao layout
        self.layoutImagem.addLayout(self.layoutImagemCentral)

        # Instâncias dos componentes da aplicação
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino="COM3", baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.threadLeitura = None

        # Widget central para aplicar o layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)


        # Grafico pra mostrar dados
        self.graficoDinamico = GraficoDinamico(self.repositorio.pacotesDados)
        self.graficoDinamico.setFixedSize(680, 400)

        # Layout para centralizar o gráfico
        self.layoutGraficoCentral = QHBoxLayout()
        self.layoutGraficoCentral.addStretch()
        self.layoutGraficoCentral.addWidget(self.graficoDinamico)
        self.layoutGraficoCentral.addStretch()

        self.layout.addLayout(self.layoutImagem)
        self.layout.addLayout(self.layoutGraficoCentral)

        # Layout para centralizar os widgets
        self.layoutCentralizado = QHBoxLayout()
        self.layoutCentralizado.addStretch()

        # ComboBox pra seleção da porta
        self.comboPorta = QComboBox(self)
        self.comboPorta.addItems(self.listarPortas())
        self.comboPorta.currentTextChanged.connect(self.escolherPorta)
        self.comboPorta.setFixedSize(150, 25) 
        self.layoutCentralizado.addWidget(self.comboPorta)

        # ComboBox pra selecionar baud rate
        self.comboBaudRate = QComboBox(self)
        self.comboBaudRate.addItems(["9600", "115200"])
        self.comboBaudRate.currentTextChanged.connect(self.escolherBaudRate)
        self.comboBaudRate.setFixedSize(150, 25)  
        self.layoutCentralizado.addWidget(self.comboBaudRate)

        self.layoutCentralizado.addStretch()
        self.layout.addLayout(self.layoutCentralizado)

        # Layout para centralizar os botões
        self.layoutBotoes = QHBoxLayout()
        self.layoutBotoes.addStretch()

        # Botão pra conectar ao Arduino
        self.botaoConectar = QPushButton("Conectar", self)
        self.botaoConectar.clicked.connect(self.pressionarConectar)
        self.botaoConectar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoConectar)

        # Botão pra desconectar do Arduino
        self.botaoDesconectar = QPushButton("Desconectar", self)
        self.botaoDesconectar.clicked.connect(self.pressionarDesconectar)
        self.botaoDesconectar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoDesconectar)

        # Botão pra salvar dados no TXT
        self.botaoSalvar = QPushButton("Salvar Dados", self)
        self.botaoSalvar.clicked.connect(self.salvarDados)
        self.botaoSalvar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoSalvar)

        # Botão pra salvar o gráfico em PNG
        self.botaoSalvarGrafico = QPushButton("Salvar Gráfico", self)
        self.botaoSalvarGrafico.clicked.connect(self.salvarGrafico)
        self.botaoSalvarGrafico.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoSalvarGrafico)

        self.layoutBotoes.addStretch()
        self.layout.addLayout(self.layoutBotoes)

        # Aplicar estilo CSS aos botões
        self.aplicarEstilo()

        # Configurar o temporizador para atualizar as portas COM disponíveis
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizarPortas)
        self.timer.start(1000)  # Atualiza a cada 1 segundo

    def aplicarEstilo(self):
        estilo = """
        QPushButton {
            background-color: #63A32E; /* Verde */
            border: none;
            color: white;
            padding: 2px 10px;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            margin: 2px 2px;
        }
        QPushButton:hover {
            background-color: white;
            color: black;
            border: 2px solid #4CAF50;
        }
        """
        self.botaoConectar.setStyleSheet(estilo)
        self.botaoDesconectar.setStyleSheet(estilo)
        self.botaoSalvar.setStyleSheet(estilo)
        self.botaoSalvarGrafico.setStyleSheet(estilo)

    def listarPortas(self):
        portas = serial.tools.list_ports.comports()
        return [porta.device for porta in portas]

    def atualizarPortas(self):
        portas_atuais = self.listarPortas()
        portas_combo = [self.comboPorta.itemText(i) for i in range(self.comboPorta.count())]

        if portas_atuais != portas_combo:
            self.comboPorta.clear()
            self.comboPorta.addItems(portas_atuais)

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
            self.configs.portaArduino = self.comboPorta.currentText()  # Atualiza a porta com a seleção atual
            self.adaptador.conectar()
            self.botaoConectar.setEnabled(False)
            self.botaoDesconectar.setEnabled(True)
            self.iniciarLeitura()
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            self.pressionarDesconectar()

    def pressionarDesconectar(self):
        self.adaptador.desconectar()
        self.botaoConectar.setEnabled(True)
        self.botaoDesconectar.setEnabled(False)
        if self.threadLeitura != None:
            self.threadLeitura.parar()
            print("Desconectado do Arduino.")
        else:
            print("Nenhum arduino foi conectado ainda.")

    def salvarDados(self):
        salvarDadosTXT(self.repositorio)

    def salvarGrafico(self):
        try:
            now = datetime.now()  
            formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"grafico_{formatted_time}.png"
            save_path = os.path.join(os.getcwd(), default_filename)  # Salva no diretório atual
            self.graficoDinamico.figure.savefig(save_path)
            print(f"Gráfico salvo em: {save_path}")
        except Exception as e:
            print(f"Erro ao salvar gráfico: {e}")

    def iniciarLeitura(self):
        if self.threadLeitura is None or not self.threadLeitura.isRunning():
            self.threadLeitura = LeitorSerialThread(self.adaptador)
            self.threadLeitura.dadoRecebido.connect(self.graficoDinamico.atualizarGrafico)
            self.threadLeitura.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MainWindow()
    janela.show()
    app.exec()
