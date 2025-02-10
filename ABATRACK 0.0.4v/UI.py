import os
import sys
from datetime import datetime  
import time  
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsDropShadowEffect, QFileDialog, QSpacerItem, QSizePolicy, QMessageBox, QCheckBox, QScrollArea, QStackedWidget)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSettings
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

        # Instâncias dos componentes da aplicação
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino="COM3", baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.threadLeitura = None

        # Widget central para aplicar o layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Adiciona a imagem ao layout principal
        self.layoutImagem = self.criarLayoutImagem(image_path)
        self.layout.addLayout(self.layoutImagem)

        # Layout horizontal para o QStackedWidget e os botões de navegação
        self.layoutHorizontal = QHBoxLayout()

        # Cria o QStackedWidget para gerenciar as diferentes telas
        self.stackedWidget = QStackedWidget(self)

        # Tela 1
        self.tela1 = QWidget()
        layoutTela1 = QVBoxLayout(self.tela1)

        # Grafico pra mostrar dados
        self.graficoDinamico = GraficoDinamico(self.repositorio.pacotesDados)
        self.graficoDinamico.setFixedSize(680, 400)

        # Layout para centralizar o gráfico
        self.layoutGraficoCentral = QHBoxLayout()
        self.layoutGraficoCentral.addStretch()
        self.layoutGraficoCentral.addWidget(self.graficoDinamico)
        self.layoutGraficoCentral.addStretch()

        layoutTela1.addLayout(self.layoutGraficoCentral)
        self.stackedWidget.addWidget(self.tela1)

        # Tela 2
        self.tela2 = QWidget()
        layoutTela2 = QVBoxLayout(self.tela2)
        layoutTela2.addStretch()
        self.stackedWidget.addWidget(self.tela2)

        # Tela 3
        self.tela3 = QWidget()
        layoutTela3 = QVBoxLayout(self.tela3)
        layoutTela3.addStretch()
        self.stackedWidget.addWidget(self.tela3)

        # Adiciona o QStackedWidget ao layout horizontal
        self.layoutHorizontal.addWidget(self.stackedWidget)

        # Layout para os botões de navegação
        self.layoutBotoesNavegacao = QVBoxLayout()
        self.layoutBotoesNavegacao.addStretch()

        # Botão para Tela 1
        self.botaoTela1 = QPushButton("1", self)
        self.botaoTela1.setFixedSize(45, 25)  # Metade do tamanho dos botões verdes
        self.botaoTela1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela1)

        # Botão para Tela 2
        self.botaoTela2 = QPushButton("2", self)
        self.botaoTela2.setFixedSize(45, 25)  # Metade do tamanho dos botões verdes
        self.botaoTela2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela2)

        # Botão para Tela 3
        self.botaoTela3 = QPushButton("3", self)
        self.botaoTela3.setFixedSize(45, 25)  # Metade do tamanho dos botões verdes
        self.botaoTela3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela3)

        self.layoutBotoesNavegacao.addStretch()

        # Adiciona o layout dos botões de navegação ao layout horizontal
        self.layoutHorizontal.addLayout(self.layoutBotoesNavegacao)

        # Adiciona o layout horizontal ao layout principal
        self.layout.addLayout(self.layoutHorizontal)

        # Layout horizontal para os botões de navegação e caixas de seleção
        self.layoutInferior = QVBoxLayout()

        # Layout horizontal para as caixas de seleção
        self.layoutCaixasSelecao = QHBoxLayout()

        # Adiciona um espaçador antes das caixas de seleção para centralizá-las
        self.layoutCaixasSelecao.addStretch()

        # ComboBox pra seleção da porta
        self.comboPorta = QComboBox(self)
        self.comboPorta.addItems(self.listarPortas())
        self.comboPorta.currentTextChanged.connect(self.escolherPorta)
        self.comboPorta.setFixedSize(150, 25) 
        self.layoutCaixasSelecao.addWidget(self.comboPorta)

        # Adiciona um espaçador entre as caixas de seleção
        self.layoutCaixasSelecao.addSpacing(20)  # Ajuste o valor conforme necessário

        # ComboBox pra selecionar baud rate
        self.comboBaudRate = QComboBox(self)
        self.comboBaudRate.addItems(["9600", "115200"])
        self.comboBaudRate.currentTextChanged.connect(self.escolherBaudRate)
        self.comboBaudRate.setFixedSize(150, 25)  
        self.layoutCaixasSelecao.addWidget(self.comboBaudRate)

        # Adiciona um espaçador depois das caixas de seleção para centralizá-las
        self.layoutCaixasSelecao.addStretch()

        self.layoutInferior.addLayout(self.layoutCaixasSelecao)

        # Layout horizontal para centralizar os botões
        self.layoutBotoes = QHBoxLayout()

        # Adiciona um espaçador antes dos botões para centralizá-los
        self.layoutBotoes.addStretch()

        # Botão pra conectar ao Arduino
        self.botaoConectar = QPushButton("Conectar", self)
        self.botaoConectar.clicked.connect(self.pressionarConectar)
        self.botaoConectar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoConectar)

        # Adiciona um espaçador entre os botões
        self.layoutBotoes.addSpacing(20)  # Ajuste o valor conforme necessário

        # Botão pra desconectar do Arduino
        self.botaoDesconectar = QPushButton("Desconectar", self)
        self.botaoDesconectar.clicked.connect(self.pressionarDesconectar)
        self.botaoDesconectar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoDesconectar)

        # Adiciona um espaçador entre os botões
        self.layoutBotoes.addSpacing(20)  # Ajuste o valor conforme necessário

        # Botão pra salvar dados no TXT
        self.botaoSalvar = QPushButton("Salvar Dados", self)
        self.botaoSalvar.clicked.connect(self.salvarDados)
        self.botaoSalvar.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoSalvar)

        # Adiciona um espaçador entre os botões
        self.layoutBotoes.addSpacing(20)  # Ajuste o valor conforme necessário

        # Botão pra salvar o gráfico em PNG
        self.botaoSalvarGrafico = QPushButton("Salvar Gráfico", self)
        self.botaoSalvarGrafico.clicked.connect(self.salvarGrafico)
        self.botaoSalvarGrafico.setFixedSize(150, 25)  
        self.layoutBotoes.addWidget(self.botaoSalvarGrafico)

        # Adiciona um espaçador depois dos botões para centralizá-los
        self.layoutBotoes.addStretch()

        self.layoutInferior.addLayout(self.layoutBotoes)

        # Adiciona o layout inferior ao layout principal
        self.layout.addLayout(self.layoutInferior)

        # Aplicar estilo CSS aos botões
        self.aplicarEstilo()

        # Configurar o temporizador para atualizar as portas COM disponíveis
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizarPortas)
        self.timer.start(1000)  # Atualiza a cada 1 segundo

        # Configurações para armazenar preferências do usuário
        self.settings = QSettings("AbaTrack", "AbaTrack")
        self.resetarAvisos()  

        self.adaptador.erroDecodificacao.connect(lambda: self.mostrarAvisoErroBaud("Erro de decodificação", "Erro ao decodificar dados"))

    def criarLayoutImagem(self, image_path):
        layoutImagem = QVBoxLayout()
        imagemTitulo = QLabel(self)
        imagemTitulo.setScaledContents(True)
        imagemTitulo.setFixedSize(179, 55)
        pixmap = QPixmap(image_path)
        imagemTitulo.setPixmap(pixmap)
        imagemTitulo.setGraphicsEffect(QGraphicsDropShadowEffect())

        layoutImagemCentral = QHBoxLayout()
        layoutImagemCentral.addStretch()
        layoutImagemCentral.addWidget(imagemTitulo)
        layoutImagemCentral.addStretch()

        layoutImagem.addLayout(layoutImagemCentral)
        return layoutImagem

    def resetarAvisos(self):
        self.settings.setValue("mostrarAvisos", True)
        self.settings.setValue("mostrarAvisosGrafico", True)
        self.settings.setValue("mostrarAvisosSalvartxt", True)
        self.settings.setValue("mostrarAvisosBaud", True)

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
            self.mostrarAviso("Erro ao conectar", str(e))
            self.pressionarDesconectar()

    def pressionarDesconectar(self):
        self.adaptador.desconectar()
        self.botaoConectar.setEnabled(True)
        self.botaoDesconectar.setEnabled(False)
        if self.threadLeitura != None:
            self.threadLeitura.parar()
            self.mostrarAvisoSemCheckbox("Desconexão", "Desconectado do Arduino.")
        else:
            self.mostrarAvisoSemCheckbox("Desconexão", "Nenhum arduino foi conectado ainda.")

    def salvarDados(self):
        salvarDadosTXT(self.repositorio)
        self.mostrarAviso("Aviso", "Dados Salvos.")

    def salvarGrafico(self):
        try:
            now = datetime.now()  
            formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"grafico_{formatted_time}.png"
            save_path = os.path.join(os.getcwd(), default_filename)  # Salva no diretório atual
            self.graficoDinamico.figure.savefig(save_path)
            self.mostrarAvisoGrafico("Sucesso", f"Gráfico salvo em: {save_path}")
        except Exception as e:
            self.mostrarAvisoGrafico("Erro ao salvar gráfico", str(e))

    def iniciarLeitura(self):
        if self.threadLeitura is None or not self.threadLeitura.isRunning():
            self.threadLeitura = LeitorSerialThread(self.adaptador)
            self.threadLeitura.dadoRecebido.connect(self.graficoDinamico.atualizarGrafico)
            self.threadLeitura.start()

    def mostrarAvisoSalvarTxt(self, titulo, mensagem):
        if self.settings.value("mostrarAvisosSalvartxt", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisosSalvartxt", False)

    def mostrarAvisoGrafico(self, titulo, mensagem):
        if self.settings.value("mostrarAvisosGrafico", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisosGrafico", False)
    
    def mostrarAvisoErroBaud(self, titulo, mensagem):
        if self.settings.value("mostrarAvisosBaud", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisosBaud", False)
    
    def mostrarAviso(self, titulo, mensagem):
        if self.settings.value("mostrarAvisos", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisos", False)

    def mostrarAvisoSemCheckbox(self, titulo, mensagem):
        aviso = QMessageBox()
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle(titulo)
        aviso.setText(mensagem)
        aviso.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))
        aviso.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))
    janela = MainWindow()
    janela.show()
    app.exec()
