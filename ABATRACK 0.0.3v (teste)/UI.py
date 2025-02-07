import os
import sys
import time
from aplicacao.use_cases import *
from dominio.entidades import *
from integracao.leitor_serial import *
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import (QIcon, QPixmap)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import serial.tools.list_ports

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

class GraficoDinamico(QWidget):
    def __init__(self, listaDados):
        super().__init__()

        self.y_data = listaDados
        self.x_data = list(range(len(listaDados)))
        self.janelaVisivel = 10

        # Criando a figura e os eixos do Matplotlib
        self.figure, self.ax = plt.subplots()
        self.ax.set_title("Temperatura", fontsize=14, fontweight='bold', color="#333333")
        self.ax.set_xlabel("Segundos", fontsize=10, fontweight='bold', color="#555555")
        self.ax.set_ylabel("Celsius", fontsize=10, fontweight='bold', color="#555555")
        self.ax.grid(True, linestyle="--", alpha=0.7)
        self.ax.set_facecolor("#f5f5f5")
        self.figure.patch.set_facecolor("#f5f5f5")

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.canvas = FigureCanvas(self.figure)
        
        self.line, = self.ax.plot(self.x_data, self.y_data, marker='o', linestyle='-', color='green', label="Valores")
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Timer para att o gráfico (cada 0.5s)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizarGrafico)
        self.timer.start(500)

    def atualizarGrafico(self):
        self.x_data = list(range(len(self.y_data)))

        self.line.set_data(self.x_data, self.y_data)

        # Ajusta os limites do eixo X para manter o efeito de "rolagem"
        if len(self.y_data) > self.janelaVisivel:
            inicio = len(self.y_data) - self.janelaVisivel
            fim = len(self.y_data)
        else:
            inicio = 0
            fim = max(self.janelaVisivel, len(self.y_data))  
        self.ax.set_xlim(inicio, fim)

        # Ajusta os limites do eixo Y para centralizar os novos dados
        if self.y_data:
            y_min = min(self.y_data)
            y_max = max(self.y_data)
            if y_min == y_max:
                margem = 1
                self.ax.set_ylim(y_min - margem, y_max + margem)
            else:
                margem = (y_max - y_min) * 0.2
                self.ax.set_ylim(y_min - margem, y_max + margem)

        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()


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
        self.setFixedSize(700, 700)

        # Cria o layout para adicionar a imagem logo abaixo da barra superior
        self.layoutImagem = QVBoxLayout()

        # Cria o QLabel para a imagem
        self.imagemTitulo = QLabel(self)
        self.imagemTitulo.setScaledContents(True)
        self.imagemTitulo.resize(179,55)
        self.imagemTitulo.setGeometry(260, 0, 179, 55)
        pixmap = QPixmap(image_path)  # Substitua pelo caminho da sua imagem
        self.imagemTitulo.setPixmap(pixmap)
        self.imagemTitulo.setGraphicsEffect(QGraphicsDropShadowEffect())

        # Adiciona a imagem ao layout
        self.layoutImagem.addWidget(self.imagemTitulo)

        # Instâncias dos componentes da aplicação
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino="COM3", baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.threadLeitura = None

        # Widget central para aplicar o layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.labelVazia = QLabel()
        self.labelVazia.setFixedSize(100, 65)
        self.layout.addWidget(self.labelVazia)

        # Grafico pra mostrar dados
        self.graficoDinamico = GraficoDinamico(self.repositorio.pacotesDados)
        self.graficoDinamico.setFixedSize(680, 435)
        self.layout.addWidget(self.graficoDinamico)

        # ComboBox pra seleção da porta
        self.comboPorta = QComboBox(self)
        self.comboPorta.addItems(self.listarPortas())
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
            padding: 5px 10px;
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
