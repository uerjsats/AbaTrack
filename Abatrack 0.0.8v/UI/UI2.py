import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGraphicsDropShadowEffect, QMessageBox, QCheckBox, QStackedWidget, QInputDialog, QMenu, QFrame, QSpacerItem, QSizePolicy, QLineEdit, QActionGroup)
from PyQt5.QtCore import QTimer, QSettings, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView  # Corrigido
import serial.tools.list_ports
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from PIL import Image, ImageOps
import folium

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
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AbaTrack")
        self.setWindowOpacity(0.95)
        self.setMinimumSize(700, 800)  # Define o tamanho mínimo da janela

        # Instancias dos objetos
        self.repositorio = RepositorioTelemetria()
        self.configs = ConfigsComunicacao(portaArduino=None, baudRate=9600)
        self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
        self.thread = None
        self.dadosRecebidos = False  # Variável de controle para verificar se houve leitura na serial

        # Adiciona a barra de menu
        self.menuBar = self.menuBar()
        self.criarMenu()

        # Adiciona o título "AbaTrack" na barra de menu
        self.adicionarTituloMenu()

        # Aplica estilo à barra de menu
        self.aplicarEstiloMenuBar()

        # Widget central
        central_widget = QWidget(self)
        central_widget.setStyleSheet("background-color: #1C1C1C;")  # Define a cor de fundo
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

        # Layout para os botões de navegação
        self.layoutBotoesNavegacao = QHBoxLayout()
        self.layoutBotoesNavegacao.addStretch(50)

        # Botão para Tela 1
        self.botaoTela1 = QPushButton("", self)
        self.botaoTela1.setFixedSize(45, 25)  
        icon_path_tela1 = os.path.join(base_path, "imgs", "icon_tela1.png")  # Caminho para a imagem PNG
        self.botaoTela1.setIcon(QIcon(icon_path_tela1))  
        self.botaoTela1.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela1)

        # Botão para Tela 2
        self.botaoTela2 = QPushButton("", self)
        self.botaoTela2.setFixedSize(45, 25)  
        icon_path_tela2 = os.path.join(base_path, "imgs", "icon_tela2.png")  # Caminho para a imagem PNG
        self.botaoTela2.setIcon(QIcon(icon_path_tela2))  
        self.botaoTela2.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela2)

        # Botão para Tela 3
        self.botaoTela3 = QPushButton("", self)
        self.botaoTela3.setFixedSize(45, 25)  
        icon_path_tela3 = os.path.join(base_path, "imgs", "icon_tela3.png")  # Caminho para a imagem PNG
        self.botaoTela3.setIcon(QIcon(icon_path_tela3)) 
        self.botaoTela3.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.layoutBotoesNavegacao.addWidget(self.botaoTela3)

        # Adiciona o layout dos botões de navegação ao layout principal
        self.layout.addLayout(self.layoutBotoesNavegacao)

        # Cria o QStackedWidget para gerenciar as diferentes telas
        self.stackedWidget = QStackedWidget(self)

        # Tela 1
        self.tela1 = QWidget()
        layoutTela1 = QVBoxLayout(self.tela1)

        # Cria um layout horizontal para os gráficos ficarem lado a lado
        layoutGraficos = QHBoxLayout()

        # Gráfico Temperatura x Tempo
        self.graficoDinamico = GraficoDinamicoGenerico("Temperatura (°C) x Tempo (s)", "Tempo (s)", "Temperatura (°C)", self.repositorio.tempo, self.repositorio.dadosTemperatura)
        self.graficoDinamico.setFixedSize(500, 300)
        layoutGraficos.addWidget(self.graficoDinamico)

        # Gráfico Pressão x Tempo
        self.graficoPressaoTemp = GraficoDinamicoGenerico("Pressão (Pa) x Tempo (s)", "Tempo (s)", "Pressão (hPa)", self.repositorio.tempo, self.repositorio.pressao)
        self.graficoPressaoTemp.setFixedSize(500, 300)
        layoutGraficos.addWidget(self.graficoPressaoTemp)

        # Gráfico Altitude x Tempo
        self.graficoAltTemp = GraficoDinamicoGenerico("Altitude (m) x Tempo (s)", "Tempo (s)", "Altitude (m)", self.repositorio.tempo1, self.repositorio.altitude)
        self.graficoAltTemp.setFixedSize(500, 300)
        layoutGraficos.addWidget(self.graficoAltTemp)

        # Cria um widget para encapsular o layout de gráficos
        widgetGraficos = QWidget()
        widgetGraficos.setLayout(layoutGraficos)

        # Adiciona um QSpacerItem antes do widget de gráficos para centralizá-lo
        layoutTela1.addSpacerItem(QSpacerItem(0, 90, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Adiciona o widget de gráficos ao layout
        layoutTela1.addWidget(widgetGraficos)

        # Adiciona um QSpacerItem depois do widget de gráficos para centralizá-lo
        layoutTela1.addSpacerItem(QSpacerItem(0, 90, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.stackedWidget.addWidget(self.tela1)

        # Tela 2
        self.tela2 = QWidget()
        layoutTela2 = QHBoxLayout(self.tela2)  # Alterado para QHBoxLayout

        # Cria o container GPS
        self.containerGPS = QFrame()
        self.containerGPS.setStyleSheet("""
            background-color: #A34B2E;
            border-radius: 10px;
            color: white;
            padding: 10px;
        """)
        self.containerGPS.setFixedSize(400, 200)

        # Adiciona sombra ao containerGPS
        shadow_effect_gps = QGraphicsDropShadowEffect()
        shadow_effect_gps.setBlurRadius(10)
        shadow_effect_gps.setOffset(5, 5)
        self.containerGPS.setGraphicsEffect(shadow_effect_gps)

        layoutContainerGPS = QVBoxLayout(self.containerGPS)

        # Cria o QLabel para os dados do GPS
        self.labelDadosGPS = QLabel("Latitude:\n\nLongitude:\n\nSats:")
        self.labelDadosGPS.setStyleSheet("font-size: 13px;")  # Aumenta a fonte para 16px
        layoutContainerGPS.addWidget(self.labelDadosGPS)

        # Adiciona o containerGPS ao layout da tela 2
        layoutTela2.addWidget(self.containerGPS)

        # Adiciona o mapa offline
        self.mapaView = QWebEngineView()
        mapa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mapa.html')
        self.mapaView.setUrl(QtCore.QUrl.fromLocalFile(mapa_path))
        self.mapaView.setFixedSize(800, 400)  # Ajuste o tamanho conforme necessário

        # Adiciona o mapa ao layout da tela 2
        layoutTela2.addWidget(self.mapaView)

        self.stackedWidget.addWidget(self.tela2)

        # Tela 3
        self.tela3 = QWidget()
        layoutTela3 = QVBoxLayout(self.tela3)

        layoutTela3.setContentsMargins(200, 50, 50, 50)

        # Adiciona o cubo 3D
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=8)
        self.view.setFixedSize(800, 400)  # Define o tamanho do widget 3D
        layoutTela3.addWidget(self.view)

        # Cria o cubo 3D
        self.cube = gl.GLMeshItem(meshdata=self.create_cube(), smooth=False, color=(0.686, 0.145, 0.733, 1), shader='shaded', drawEdges=True)
        self.view.addItem(self.cube)

        # Cria o container Gyro
        self.containerGyro = QFrame()
        self.containerGyro.setStyleSheet("""
            background-color: #243482;
            border-radius: 10px;
            color: white;
            padding: 10px;
        """)
        self.containerGyro.setFixedSize(200, 200)

        # Adiciona sombra ao containerGyro
        shadow_effect_gyro = QGraphicsDropShadowEffect()
        shadow_effect_gyro.setBlurRadius(10)
        shadow_effect_gyro.setOffset(5, 5)
        self.containerGyro.setGraphicsEffect(shadow_effect_gyro)

        layoutContainerGyro = QVBoxLayout(self.containerGyro)

        # Cria o QLabel para os dados do Gyro
        self.labelDadosGyro = QLabel("Accel X:\n\nAccel Y:\n\nAccel Z:")
        self.labelDadosGyro.setStyleSheet("font-size: 13px;")  # Aumenta a fonte para 16px
        layoutContainerGyro.addWidget(self.labelDadosGyro)

        # Adiciona o containerGyro ao layout da Tela 3
        layoutTela3.addWidget(self.containerGyro, alignment=Qt.AlignmentFlag.AlignRight)

        # Adiciona margens ao layout da Tela 3 para alinhar o containerGyro
        layoutTela3.setContentsMargins(100, 100, 150, 200)

        self.stackedWidget.addWidget(self.tela3)

        # Adiciona o QStackedWidget ao layout horizontal
        self.layoutHorizontal.addWidget(self.stackedWidget)

        # Adiciona o layout horizontal ao layout principal
        self.layout.addLayout(self.layoutHorizontal)

        # Layout inferior para os botões de navegação e caixas de seleção
        self.layoutInferior = QVBoxLayout()
        self.layoutInferior.addStretch()  # Empurra o conteúdo para o fundo

        # Primeiro adiciona o frame estilizado dos dados do rádio
        self.containerDadosdoRadio = QFrame()
        self.containerDadosdoRadio.setStyleSheet("""
            background-color: #173905;
            border-radius: 10px;
            color: white;
            padding: 10px;
        """)
        self.containerDadosdoRadio.setFixedSize(250, 120)

        # Adiciona sombra ao containerDadosdoRadio
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(5, 5)
        self.containerDadosdoRadio.setGraphicsEffect(shadow_effect)

        layoutContainerRadio = QVBoxLayout(self.containerDadosdoRadio)

        # Cria o QLabel para os dados do rádio
        self.labelDadosdoRadio = QLabel("Número de Pacotes:\nRSSI:\nTamanho do Pacote:")
        layoutContainerRadio.addWidget(self.labelDadosdoRadio)

        # Adiciona margens ao layout
        layoutContainerRadio.setContentsMargins(10, 10, 10, 10)

        self.layoutInferior.addWidget(self.containerDadosdoRadio, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Adiciona a caixa de texto e o botão para enviar comandos via Serial
        layoutComandos = QHBoxLayout()
        layoutComandos.setContentsMargins(0, 0, 0, 0)  
        layoutComandos.setSpacing(1)  

        self.inputComando = QLineEdit(self)
        self.inputComando.setPlaceholderText("Digite o comando")
        self.inputComando.setFixedSize(700, 30)
        self.inputComando.setStyleSheet("""
            QLineEdit {
                color: white; /* Cor do texto */
                border: 1px solid #ccc; /* Contorno suave */
                border-radius: 5px; /* Bordas arredondadas */
                padding: 5px; /* Espaçamento interno */
            }
            QLineEdit:focus {
                border: 1px solid #63A32E; /* Contorno verde quando focado */
            }
        """)
        self.inputComando.returnPressed.connect(self.enviarComandoSerial)
        layoutComandos.addWidget(self.inputComando)

        #self.botaoEnviarComando = QPushButton("Enviar", self)
        #self.botaoEnviarComando.setFixedSize(100, 30)  
        #self.botaoEnviarComando.clicked.connect(self.enviarComandoSerial)
        #layoutComandos.addWidget(self.botaoEnviarComando)

        layoutComandos.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.layoutInferior.addLayout(layoutComandos)
        
        # Em seguida o label para os dados dos pacotes
        self.labelPacotesBrutos = QLabel("Dados dos pacotes recebidos: ")
        self.labelPacotesBrutos.setStyleSheet("color: white;")  # Adiciona esta linha

        # Layout horizontal para o label dos pacotes
        self.layoutBotoesEPacotes = QHBoxLayout()
        self.layoutBotoesEPacotes.addWidget(self.labelPacotesBrutos, alignment=Qt.AlignmentFlag.AlignLeft)

        # Adiciona o layoutBotoesEPacotes ao layoutInferior
        self.layoutInferior.addLayout(self.layoutBotoesEPacotes)

        # Adiciona o layout inferior ao layout principal
        self.layout.addLayout(self.layoutInferior)

        # Adiciona margens ao layout inferior para afastar o containerDadosdoRadio da borda da janela
        self.layoutInferior.setContentsMargins(20, 20, 20, 20)

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
        self.dadosRecebidos = True  # Atualiza a variável de controle
        self.labelPacotesBrutos.setText("Dados dos pacotes recebidos: " + ":".join(map(str, ultimoPacoteDados)))

    def atualizarLabelDadosdoRadio(self, numeroDePacotes):
        if self.repositorio.numerodepacotes:  
            ultimo_pacote = self.repositorio.numerodepacotes[-1]
            rssi = self.repositorio.RSSI[-1]
            tamanho_pacote = self.repositorio.tamanhopacote[-1]
            self.labelDadosdoRadio.setText("Número de Pacotes: " + str(ultimo_pacote) + "\nRSSI: " + str(rssi) + "dBm"+"\nTamanho do Pacote: " + str(tamanho_pacote)+" bytes")

    def atualizarLabelDadosGPS(self, pacoteDadosGPS):
        latitude = self.repositorio.latitude[-1]
        longitude = self.repositorio.longitude[-1]
        sats = self.repositorio.sats[-1]
        self.labelDadosGPS.setText(f"Latitude: {latitude}\n\nLongitude: {longitude}\n\nSats: {sats}")        

    def atualizarLabelDadosGiro(self, pacoteGiro):
        # Atualiza a rotação do cubo 3D com base nos dados do sensor MPU6050
        roll = self.repositorio.gyrox[-1]
        pitch = self.repositorio.gyroy[-1]
        yaw = self.repositorio.gyroz[-1]

        self.cube.resetTransform()
        self.cube.rotate(roll, 1, 0, 0)
        self.cube.rotate(pitch, 0, 1, 0)
        self.cube.rotate(yaw, 0, 0, 1)

        # Atualiza o QLabel com os dados do Gyro
        self.labelDadosGyro.setText(f"Gyro X: {roll}\n\nGyro Y: {pitch}\n\nGyro Z: {yaw}")

    # Funções para iniciar e parar a leitura dos dados   
    def iniciarLeitura(self):
        if self.thread is None or not self.thread.isRunning():
            self.thread = ThreadPrincipal(self.adaptador)
            
            self.thread.ultimosSubdadosTemperaturaTempo.connect(self.graficoDinamico.atualizarGrafico)
            self.thread.ultimosSubdadosPressTemp.connect(self.graficoPressaoTemp.atualizarGrafico)
            self.thread.ultimosSubdadosAltTemp.connect(self.graficoAltTemp.atualizarGrafico)
            
            self.thread.ultimosDadosBrutos.connect(self.atualizarLabelDadoBruto)
            self.thread.dadosdoRadio.connect(self.atualizarLabelDadosdoRadio)
            self.thread.pacoteDadosGPS.connect(self.atualizarLabelDadosGPS)
            self.thread.pacoteGiro.connect(self.atualizarLabelDadosGiro)

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
            self.mostrarToast("Conectado com sucesso!")
        except Exception as e:
            self.mostrarAviso("Erro ao conectar", str(e))
            self.pressionarDesconectar()

    def mostrarToast(self, mensagem):
        toast = QLabel(mensagem, self)
        toast.setStyleSheet("""
            QLabel {
                background-color: #444;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        toast.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        toast.setGeometry(self.geometry().center().x() - 100, self.geometry().center().y() - 50, 200, 50)
        toast.show()

        QTimer.singleShot(2000, toast.close)  # Fecha o toast após 3 segundos

    # Funções para salvar os dados e o gráfico
    def salvarDados(self):
        salvarDadosTXT(self.repositorio)
        self.mostrarAviso("Aviso", "Dados Salvos.")

    def salvarGraficoTemperaturaxTempo(self):
        try:
            now = datetime.now()  
            formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"grafico_{formatted_time}.png"
            save_path = os.path.join(os.getcwd(), default_filename)  # Salva no diretório atual
            self.graficoDinamico.figure.savefig(save_path)

            # Inverte as cores da imagem
            image = Image.open(save_path)
            inverted_image = ImageOps.invert(image.convert("RGB"))
            inverted_image.save(save_path)

            self.mostrarAvisoGrafico("Sucesso", f"Gráfico salvo em: {save_path}")
        except Exception as e:
            self.mostrarAvisoGrafico("Erro ao salvar gráfico", str(e))
    
    def salvarGraficoPressaoxTemperatura(self):
        try:
            now = datetime.now()  
            formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"grafico_{formatted_time}.png"
            save_path = os.path.join(os.getcwd(), default_filename)  # Salva no diretório atual
            self.graficoPressaoTemp.figure.savefig(save_path)

            # Inverte as cores da imagem
            image = Image.open(save_path)
            inverted_image = ImageOps.invert(image.convert("RGB"))
            inverted_image.save(save_path)

            self.mostrarAvisoGrafico("Sucesso", f"Gráfico salvo em: {save_path}")
        except Exception as e:
            self.mostrarAvisoGrafico("Erro ao salvar gráfico", str(e))
    
    def salvarGraficoAltTemp(self):
        try:
            now = datetime.now()  
            formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            default_filename = f"grafico_{formatted_time}.png"
            save_path = os.path.join(os.getcwd(), default_filename)  # Salva no diretório atual
            self.graficoAltTemp.figure.savefig(save_path)

            # Inverte as cores da imagem
            image = Image.open(save_path)
            inverted_image = ImageOps.invert(image.convert("RGB"))
            inverted_image.save(save_path)

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
            padding: 15px; /* Adiciona padding para centralizar o texto */
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

        # Cria o submenu Salvar gráficos
        submenuSalvarGraficos = menuArquivo.addMenu("Salvar Gráficos")

        acaoSalvarGraficoTemp = submenuSalvarGraficos.addAction("Salvar Gráfico Temperatura")
        acaoSalvarGraficoTemp.triggered.connect(self.salvarGraficoTemperaturaxTempo)

        acaoSalvarGraficoPres = submenuSalvarGraficos.addAction("Salvar Gráfico Pressão")
        acaoSalvarGraficoPres.triggered.connect(self.salvarGraficoPressaoxTemperatura)

        acaoSalvarGraficoAlt = submenuSalvarGraficos.addAction("Salvar Gráfico Altitude")
        acaoSalvarGraficoAlt.triggered.connect(self.salvarGraficoAltTemp)

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
        QMessageBox.about(self, "Sobre", "AbaTrack 0.0.7v\nDesenvolvido pela equipe UERJ Sats.")

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


    # Janelas de Aviso
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

    # Função para criar um cubo 3D
    def create_cube(self):
        verts = np.array([
            [1, 1, 1],
            [1, 1, -1],
            [1, -1, 1],
            [1, -1, -1],
            [-1, 1, 1],
            [-1, 1, -1],
            [-1, -1, 1],
            [-1, -1, -1]
        ])

        faces = np.array([
            [0, 1, 2],
            [1, 3, 2],
            [4, 5, 6],
            [5, 7, 6],
            [0, 1, 4],
            [1, 5, 4],
            [2, 3, 6],
            [3, 7, 6],
            [0, 2, 4],
            [2, 6, 4],
            [1, 3, 5],
            [3, 7, 5]
        ])

        return gl.MeshData(vertexes=verts, faces=faces)

    def enviarComandoSerial(self):
        comando = self.inputComando.text()
        if comando:
            try:
                self.adaptador.enviarComando(comando)
                self.inputComando.clear()
                self.mostrarToast("Comando enviado com sucesso!")
            except Exception as e:
                self.mostrarAviso("Erro ao enviar comando", str(e))

    def closeEvent(self, event):
        if self.dadosRecebidos:  # Verifica se houve leitura na serial
            self.salvarDados()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)

