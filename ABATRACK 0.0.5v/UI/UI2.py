import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsDropShadowEffect, QMessageBox, QCheckBox, QStackedWidget, QInputDialog, QMenu)
from PyQt6.QtCore import QTimer, QSettings, Qt
from PyQt6.QtGui import QIcon, QPixmap, QActionGroup
import serial.tools.list_ports

# Adicione o diretório 'integracao' ao sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integracao'))

from aplicacao.use_cases import *
from dominio.entidades import *
from integracao.adaptador_arduino import AdaptadorArduino
from UI.graficosGenericos import GraficoDinamicoGenerico
from UI.thread_main import ThreadPrincipal

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AbaTrack")
        self.resize(600, 700)
        self.setWindowOpacity(0.95)

        # Instancias dos objetos
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino=None, baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.thread = None

        # Adiciona a barra de menu
        self.menuBar = self.menuBar()
        self.criarMenu()

        # Adiciona o título "AbaTrack" na barra de menu
        self.adicionarTituloMenu()

        # Aplica estilo à barra de menu
        self.aplicarEstiloMenuBar()

        # Widget central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Logo Abasat :)
        # Pathing para as imgs
        base_path = os.path.dirname(os.path.dirname(__file__))
        self.icon_path = os.path.join(base_path, "imgs", "AbaTrack.ico")

        # Add imagens
        self.setWindowIcon(QIcon(self.icon_path))


        # Layout horizontal para o QStackedWidget e os botões de navegação
        self.layoutHorizontal = QHBoxLayout()

        # Cria o QStackedWidget para gerenciar as diferentes telas
        self.stackedWidget = QStackedWidget(self)

        # Tela 1
        self.tela1 = QWidget()
        layoutTela1 = QVBoxLayout(self.tela1)

        # Grafico pra mostrar dados
        self.graficoDinamico = GraficoDinamicoGenerico("Temperatura x Tempo", "Tempo (s)", "Temperatura (°C)", self.repositorio.dadosTemperatura, self.repositorio.tempo)  
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

        # Label para mostrar número de pacotes
        self.labelNumerodePacotes = QLabel()
        self.labelNumerodePacotes.setText("Número de Pacotes: ")
        layoutTela2.addWidget(self.labelNumerodePacotes)

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

        # Label para mostrar os pacotes brutos
        self.labelPacotesBrutos = QLabel()
        self.labelPacotesBrutos.setText("Pacotes recebidos: ")
        self.layoutInferior.addWidget(self.labelPacotesBrutos)

        # Adiciona o layout inferior ao layout principal
        self.layout.addLayout(self.layoutInferior)

        # Configurar o temporizador para atualizar as portas COM disponíveis
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.atualizarSubmenuPorta(self.menuConfiguracoes.findChild(QMenu, "Porta")))  # Adiciona a atualização do submenu Porta
        self.timer.start(1000)  # Atualiza a cada 1 segundo

        # Configurações para armazenar preferências do usuário
        self.settings = QSettings("AbaTrack", "AbaTrack")
        self.resetarAvisos()  

        self.adaptador.erroDecodificacao.connect(lambda: self.mostrarAvisoErroBaud("Erro de decodificação", "Erro ao decodificar dados"))

    # Inicializa a lista de portas COM disponíveis
    def listarPortas(self):
        portas = serial.tools.list_ports.comports()
        return [porta.device for porta in portas]
    
    # Funções para atualizar a interface gráfica
    def atualizarLabelDadoBruto(self, ultimoPacoteDados):
            self.labelPacotesBrutos.setText("Pacotes recebidos: "+":".join(map(str, ultimoPacoteDados)))

    def atualizarLabelNumeroPacotes(self,numeroDePacotes):
            if self.repositorio.numerodepacotes:  
                ultimo_pacote = self.repositorio.numerodepacotes[-1]
                self.labelNumerodePacotes.setText("Número de Pacotes: "+ str(ultimo_pacote))

    # Funções para iniciar e parar a leitura dos dados   
    def iniciarLeitura(self):
        if self.thread == None or not self.thread.isRunning():
            self.thread = ThreadPrincipal(self.adaptador)
            
            self.thread.ultimosSubdados.connect(self.graficoDinamico.atualizarGrafico)
            self.thread.ultimosDadosBrutos.connect(self.atualizarLabelDadoBruto)
            self.thread.numeroDePacotes.connect(self.atualizarLabelNumeroPacotes)

            self.thread.start()

    # Funções para conectar e desconectar o Arduino
    def pressionarDesconectar(self):
        self.adaptador.desconectar()

        if self.thread != None:
            self.thread.stop()

            self.mostrarAvisoSemCheckbox("Desconexão", "Desconectado do Arduino.")
        else:
            self.mostrarAvisoSemCheckbox("Desconexão", "Nenhum arduino foi conectado ainda.")

    def pressionarConectar(self):
        try:
            self.adaptador.conectar()

            self.iniciarLeitura()

        except Exception as e:
            self.mostrarAviso("Erro ao conectar", str(e))

            self.pressionarDesconectar()

    # Funções para salvar os dados e o gráfico
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

    #Configurações Menu Bar
    def aplicarEstiloMenuBar(self):
        estilo_menu_bar = """
        QMenuBar {
            background-color: #63A32E; /* Verde */
            color: white;
            font-size: 13px; /* Aumenta o tamanho da fonte */
            -webkit-text-stroke-width: 0.5px; /* Contorno preto */
            -webkit-text-stroke-color: #000;
        }
        QMenuBar::item {
            background-color: #63A32E; /* Verde */
            color: white;
            font-size: 16px; /* Aumenta o tamanho da fonte */
            -webkit-text-stroke-width: 0.5px; /* Contorno preto */
            -webkit-text-stroke-color: #000;
            padding: 12px; /* Adiciona padding para centralizar o texto */
            margin: 0px 4px; /* Adiciona margem para centralizar o texto */
            height: 50%; /* Ajusta a altura dos itens para serem da altura da menuBar */
            border-radius: 1; /* Borda quadrada */
        }
        QMenuBar::item:selected {
            background-color: #4CAF50; /* Verde mais escuro */
        }
        """
        self.menuBar.setStyleSheet(estilo_menu_bar)

    def criarMenu(self):
        # Cria o menu Arquivo
        menuArquivo = self.menuBar.addMenu("Arquivo")

        # Adiciona ações ao menu Arquivo
        acaoSalvar = menuArquivo.addAction("Salvar Dados")
        acaoSalvar.triggered.connect(self.salvarDados)

        acaoSalvarGrafico = menuArquivo.addAction("Salvar Gráfico")
        acaoSalvarGrafico.triggered.connect(self.salvarGrafico)

        acaoSair = menuArquivo.addAction("Sair")
        acaoSair.triggered.connect(self.close)

        # Cria o menu Configurações
        self.menuConfiguracoes = self.menuBar.addMenu("Configurações")

        # Cria o submenu Porta
        submenuPorta = self.menuConfiguracoes.addMenu("Porta")
        submenuPorta.setObjectName("Porta")
        self.atualizarSubmenuPorta(submenuPorta)

        # Cria o submenu Baud Rate
        submenuBaudRate = self.menuConfiguracoes.addMenu("Baud Rate")
        submenuBaudRate.setObjectName("Baud Rate")
        self.atualizarSubmenuBaudRate(submenuBaudRate)

        # Adiciona ações ao menu Configurações
        acaoConectar = self.menuConfiguracoes.addAction("Conectar")
        acaoConectar.triggered.connect(self.pressionarConectar)

        acaoDesconectar = self.menuConfiguracoes.addAction("Desconectar")
        acaoDesconectar.triggered.connect(self.pressionarDesconectar)

        # Cria o menu Ajuda
        menuAjuda = self.menuBar.addMenu("Ajuda")

        # Adiciona ações ao menu Ajuda
        acaoSobre = menuAjuda.addAction("Sobre")
        acaoSobre.triggered.connect(self.mostrarSobre)

    def atualizarSubmenuPorta(self, submenuPorta):
        if submenuPorta is not None:
            submenuPorta.clear()
            portas = self.listarPortas()
            acaoGroupPorta = QActionGroup(self)
            for porta in portas:
                acaoPorta = submenuPorta.addAction(porta)
                acaoPorta.setCheckable(True)
                acaoPorta.setChecked(porta == self.configs.portaArduino)
                acaoPorta.triggered.connect(lambda checked, p=porta: self.selecionarPorta(p))
                acaoGroupPorta.addAction(acaoPorta)

    def atualizarSubmenuBaudRate(self, submenuBaudRate):
        if submenuBaudRate is not None:
            submenuBaudRate.clear()
            baud_rates = ["9600", "115200"]
            acaoGroupBaudRate = QActionGroup(self)
            for baud_rate in baud_rates:
                acaoBaudRate = submenuBaudRate.addAction(baud_rate)
                acaoBaudRate.setCheckable(True)
                acaoBaudRate.setChecked(baud_rate == str(self.configs.baudRate))
                acaoBaudRate.triggered.connect(lambda checked, b=baud_rate: self.selecionarBaudRate(b))
                acaoGroupBaudRate.addAction(acaoBaudRate)

    def selecionarPorta(self, porta):
        self.configs.portaArduino = porta

        print(f"Porta selecionada: {porta}")
        submenuPorta = self.menuConfiguracoes.findChild(QMenu, "Porta")
        self.atualizarSubmenuPorta(submenuPorta)

    def selecionarBaudRate(self, baud_rate):
        self.configs.baudRate = int(baud_rate)
        
        print(f"Baud rate selecionado: {baud_rate}")
        submenuBaudRate = self.menuConfiguracoes.findChild(QMenu, "Baud Rate")
        self.atualizarSubmenuBaudRate(submenuBaudRate)

    def mostrarSobre(self):
        QMessageBox.about(self, "Sobre", "AbaTrack v0.0.5\nDesenvolvido pela equipe UERJ Sats.")

    def adicionarTituloMenu(self):
        
        # Cria o QLabel para o título
        titulo = QLabel("AbaTrack", self)
        estilo_titulo = """
        QLabel {
            color: #FFF;
            text-align: center;
            text-shadow: 2px 2px 15px rgba(0, 0, 0, 0.85);
            -webkit-text-stroke-width: 1px;
            -webkit-text-stroke-color: #000;
            font-family: "Jaini Purva";
            font-size: 18px;
            font-style: normal;
            font-weight: 400;
            line-height: normal;
            margin-left: 20px; /* Adiciona margem à esquerda para mover o título para a direita */
        }
        """
        titulo.setStyleSheet(estilo_titulo)

        # Carrega a imagem
        base_path = os.path.dirname(os.path.dirname(__file__))
        image_path = os.path.join(base_path, "imgs", "abasat.png")
        imagem = QLabel(self)
        pixmap = QPixmap(image_path)

        # Redimensiona a imagem para o tamanho do texto
        pixmap = pixmap.scaledToHeight(18, Qt.TransformationMode.SmoothTransformation)
        imagem.setPixmap(pixmap)

        # Cria um layout horizontal para alinhar o título e a imagem
        layout = QHBoxLayout()
        layout.addWidget(titulo)
        layout.addWidget(imagem)
        layout.addStretch()

        # Cria um widget para conter o layout
        widget = QWidget(self)
        widget.setLayout(layout)

        # Adiciona o widget à barra de menu
        self.menuBar.setCornerWidget(widget, Qt.Corner.TopLeftCorner)

    def mostrarAvisoSalvarTxt(self, titulo, mensagem):
        if self.settings.value("mostrarAvisosSalvartxt", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(self.icon_path))

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
            aviso.setWindowIcon(QIcon(self.icon_path))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisosGrafico", False)

    # Janelas de Aviso
    
    def mostrarAvisoErroBaud(self, titulo, mensagem):
        aviso = QMessageBox(self)
        aviso.setWindowTitle(titulo)
        aviso.setText(mensagem)
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowIcon(QIcon(self.icon_path))
        aviso.exec()
    
    def mostrarAviso(self, titulo, mensagem):
        if self.settings.value("mostrarAvisos", True, type=bool):
            aviso = QMessageBox()
            aviso.setIcon(QMessageBox.Icon.Warning)
            aviso.setWindowTitle(titulo)
            aviso.setText(mensagem)
            aviso.setWindowIcon(QIcon(self.icon_path))

            checkbox = QCheckBox("Não mostrar novamente")
            aviso.setCheckBox(checkbox)

            if aviso.exec() == QMessageBox.StandardButton.Ok and checkbox.isChecked():
                self.settings.setValue("mostrarAvisos", False)

    def mostrarAvisoSemCheckbox(self, titulo, mensagem):
        aviso = QMessageBox()
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle(titulo)
        aviso.setText(mensagem)
        aviso.setWindowIcon(QIcon(self.icon_path))
        aviso.exec()

    def mostrarAvisoDesconectar(self):
        aviso = QMessageBox(self)
        aviso.setWindowTitle("Desconectado")
        aviso.setText("O dispositivo foi desconectado com sucesso.")
        aviso.setIcon(QMessageBox.Icon.Information)
        aviso.setWindowIcon(QIcon(self.icon_path))
        aviso.exec()

    def resetarAvisos(self):
        self.settings.setValue("mostrarAvisos", True)
        self.settings.setValue("mostrarAvisosGrafico", True)
        self.settings.setValue("mostrarAvisosSalvartxt", True)
        self.settings.setValue("mostrarAvisosBaud", True)
