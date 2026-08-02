import csv
from datetime import datetime
import os
import sys

from aplicacao.use_cases import *
from dominio.entidades import *
from folium import Map, Marker
import folium
from integracao.adaptador_arduino import AdaptadorArduino
from integracao.salvar_graficos import salvarGrafico
import numpy as np
from PIL import Image, ImageOps
from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QActionGroup,
    QApplication,
    QCheckBox,
    QComboBox,
    QDesktopWidget,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import serial.tools.list_ports
from UI.graficosGenericos import GraficoDinamicoGenerico
from UI.tela_serial import TelaSerial
from UI.thread_main import ThreadPrincipal

# Adicione o diretório 'integracao' ao sys.path
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integracao')
)


class MainWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self.initUI()

  def initUI(self):
    self.setWindowTitle('AbaTrack')
    self.setWindowOpacity(1.0)

    # Configuração de tela e tamanho responsivo
    screen = self.screen() if self.screen() else QApplication.primaryScreen()
    tela = screen.availableGeometry()
    largura_monitor = tela.width()
    altura_monitor = tela.height()

    self.resize(int(largura_monitor * 0.85), int(altura_monitor * 0.85))
    self.setMinimumSize(800, 500)
    self.centralizarNaTela()

    # Instâncias dos objetos de dados
    self.repositorio = RepositorioTelemetria()
    self.configs = ConfigsComunicacao(portaArduino=None, baudRate=9600)
    self.adaptador = AdaptadorArduino(self.repositorio, self.configs)
    self.thread = None
    self.dadosRecebidos = False

    # Configuração das Barras de Menu
    self.menuBar = self.menuBar()
    self.criarMenu()
    self.adicionarTituloMenu()
    self.aplicarEstiloMenuBar()

    # Widget Central e Layout Principal Vertical
    central_widget = QWidget(self)
    central_widget.setStyleSheet('background-color: #1C1C1C;')
    self.setCentralWidget(central_widget)
    self.layoutPrincipal = QVBoxLayout(central_widget)

    # Ícone da janela
    base_path = os.path.dirname(os.path.dirname(__file__))
    self.icon_path = os.path.join(base_path, 'imgs', 'AbaTrack.ico')
    self.setWindowIcon(QIcon(self.icon_path))

    # ==================== BOTÕES DE NAVEGAÇÃO SUPERIORES ====================
    self.layoutBotoesNavegacao = QHBoxLayout()
    self.layoutBotoesNavegacao.addStretch(50)

    self.botaoTela1 = QPushButton('', self)
    self.botaoTela1.setFixedSize(45, 25)
    self.botaoTela1.setIcon(
        QIcon(os.path.join(base_path, 'imgs', 'icon_tela1.png'))
    )
    self.botaoTela1.clicked.connect(
        lambda: self.stackedWidget.setCurrentIndex(0)
    )
    self.layoutBotoesNavegacao.addWidget(self.botaoTela1)

    self.botaoTela2 = QPushButton('', self)
    self.botaoTela2.setFixedSize(45, 25)
    self.botaoTela2.setIcon(
        QIcon(os.path.join(base_path, 'imgs', 'icon_tela2.png'))
    )
    self.botaoTela2.clicked.connect(
        lambda: self.stackedWidget.setCurrentIndex(1)
    )
    self.layoutBotoesNavegacao.addWidget(self.botaoTela2)

    self.botaoTela3 = QPushButton('', self)
    self.botaoTela3.setFixedSize(45, 25)
    self.botaoTela3.setIcon(
        QIcon(os.path.join(base_path, 'imgs', 'icon_tela3.png'))
    )
    self.botaoTela3.clicked.connect(
        lambda: self.stackedWidget.setCurrentIndex(2)
    )
    self.layoutBotoesNavegacao.addWidget(self.botaoTela3)

    self.layoutPrincipal.addLayout(self.layoutBotoesNavegacao)

    # ==================== STACKED WIDGET (PÁGINAS) ====================
    self.stackedWidget = QStackedWidget(self)

     # ------------------- TELA 1 (Telemetria Principal) -------------------
    self.tela1 = QWidget()
    layoutTela1 = QVBoxLayout(self.tela1)
    layoutTela1.setContentsMargins(15, 15, 15, 15)
    layoutTela1.setSpacing(10)

    # 1. Gráficos em linha na parte superior
    self.graficoDinamico = GraficoDinamicoGenerico('Temperatura (°C) x Tempo (s)', 'Tempo (s)', 'Temperatura (°C)', self.repositorio.tempo, self.repositorio.dadosTemperatura)
    self.graficoPressaoTemp = GraficoDinamicoGenerico('Pressão (Pa) x Tempo (s)', 'Tempo (s)', 'Pressão (hPa)', self.repositorio.tempo, self.repositorio.pressao)
    self.graficoAltTemp = GraficoDinamicoGenerico('Altitude (m) x Tempo (s)', 'Tempo (s)', 'Altitude (m)', self.repositorio.tempo1, self.repositorio.altitude)

    layoutGraficos = QHBoxLayout()
    layoutGraficos.setSpacing(10)
    layoutGraficos.addWidget(self.graficoDinamico)
    layoutGraficos.addWidget(self.graficoPressaoTemp)
    layoutGraficos.addWidget(self.graficoAltTemp)
    
    # Adiciona os gráficos ocupando 75% da altura da tela (peso 3)
    layoutTela1.addLayout(layoutGraficos, stretch=5)

    # 2. Área Inferior da Tela 1 (Console + Card de Rádio)
    layoutInferiorTela1 = QHBoxLayout()
    layoutInferiorTela1.setSpacing(20)

    # Container Esquerdo: Comando + Console/Pacotes
    layoutConsoleComandos = QVBoxLayout()
    layoutConsoleComandos.setSpacing(8)

    self.inputComando = QLineEdit(self)
    self.inputComando.setPlaceholderText('Digite o comando serial...')
    self.inputComando.setMaximumWidth(550)
    self.inputComando.setStyleSheet("""
        QLineEdit {
            color: white; 
            border: 1px solid #444; 
            border-radius: 5px; 
            padding: 8px 12px; 
            font-size: 14px;
            background-color: #252525;
        }
        QLineEdit:focus { border: 1px solid #63A32E; }
    """)
    self.inputComando.returnPressed.connect(self.enviarComandoSerial)

    self.labelPacotesBrutos = QLabel('Dados dos pacotes recebidos: ')
    self.labelPacotesBrutos.setStyleSheet('color: white; font-size: 14px;')

    layoutConsoleComandos.addWidget(self.inputComando)
    layoutConsoleComandos.addWidget(self.labelPacotesBrutos)
    layoutConsoleComandos.addStretch() # Mantém o console alinhado ao topo deste container

    layoutInferiorTela1.addLayout(layoutConsoleComandos)

    # Container Direito: Card de Informações de Rádio (Verde)
    self.containerDadosdoRadio = QFrame()
    self.containerDadosdoRadio.setStyleSheet("""
        background-color: #173905; 
        border-radius: 10px; 
        color: white; 
        padding: 10px;
    """)
    self.containerDadosdoRadio.setFixedSize(240, 105)

    shadow_effect = QGraphicsDropShadowEffect()
    shadow_effect.setBlurRadius(8)
    shadow_effect.setOffset(3, 3)
    self.containerDadosdoRadio.setGraphicsEffect(shadow_effect)

    layoutContainerRadio = QVBoxLayout(self.containerDadosdoRadio)
    layoutContainerRadio.setContentsMargins(8, 8, 8, 8)
    
    self.labelDadosdoRadio = QLabel('<b>Número de Pacotes:</b> 0<br><b>RSSI:</b> 0 dBm<br><b>Tamanho:</b> 0 bytes')
    self.labelDadosdoRadio.setStyleSheet('font-size: 13px; color: white;')
    layoutContainerRadio.addWidget(self.labelDadosdoRadio)
    layoutInferiorTela1.addStretch()
    layoutInferiorTela1.addWidget(self.containerDadosdoRadio)

    # Parte inferior ocupa os 25% restantes da altura (peso 1)
    layoutTela1.addLayout(layoutInferiorTela1, stretch=1)
    layoutInferiorTela1.setAlignment(Qt.AlignmentFlag.AlignLeft)

    self.stackedWidget.addWidget(self.tela1)

    # ------------------- TELA 2 (GPS e Mapa) -------------------
    self.tela2 = QWidget()
    layoutTela2 = QHBoxLayout(self.tela2)

    self.containerGPS = QFrame()
    self.containerGPS.setStyleSheet("""
            background-color: #A34B2E; border-radius: 10px; color: white; padding: 10px;
        """)
    self.containerGPS.setFixedWidth(300)

    shadow_gps = QGraphicsDropShadowEffect()
    shadow_gps.setBlurRadius(10)
    shadow_gps.setOffset(5, 5)
    self.containerGPS.setGraphicsEffect(shadow_gps)

    layoutContainerGPS = QVBoxLayout(self.containerGPS)
    self.labelDadosGPS = QLabel(
        '<div style="text-align: center;"><b>Dados'
        ' GPS</b></div><br>Latitude:<br>Longitude:<br>Sats: '
    )
    self.labelDadosGPS.setStyleSheet('font-size: 15px;')
    layoutContainerGPS.addWidget(self.labelDadosGPS)
    layoutTela2.addWidget(self.containerGPS)

    self.mapaView = QWebEngineView()
    mapa_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'mapa.html'
    )
    self.mapaView.setUrl(QtCore.QUrl.fromLocalFile(mapa_path))
    layoutTela2.addWidget(self.mapaView)

    self.stackedWidget.addWidget(self.tela2)

    # ------------------- TELA 3 (Cubo 3D e Giro) -------------------
    self.tela3 = QWidget()
    layoutTela3 = QHBoxLayout(self.tela3)

    self.view = gl.GLViewWidget()
    self.view.setCameraPosition(distance=9)
    layoutTela3.addWidget(self.view, stretch=3)

    self.cube = gl.GLMeshItem(
        meshdata=self.create_cube(),
        smooth=False,
        color=(0.75, 0.75, 0.75, 1),
        shader='shaded',
        drawEdges=True,
    )
    self.view.addItem(self.cube)

    self.containerGyro = QFrame()
    self.containerGyro.setStyleSheet("""
            background-color: #243482; border-radius: 10px; color: white; padding: 10px;
        """)
    self.containerGyro.setFixedWidth(280)

    shadow_gyro = QGraphicsDropShadowEffect()
    shadow_gyro.setBlurRadius(10)
    shadow_gyro.setOffset(5, 5)
    self.containerGyro.setGraphicsEffect(shadow_gyro)

    layoutContainerGyro = QVBoxLayout(self.containerGyro)
    self.labelDadosGyro = QLabel(
        '<div style="text-align: center;"><b>Dados'
        ' Giro</b></div><br>Roll:<br>Pitch:<br>Yaw: '
    )
    self.labelDadosGyro.setStyleSheet('font-size: 15px;')
    layoutContainerGyro.addWidget(self.labelDadosGyro)

    layoutTela3.addWidget(self.containerGyro, stretch=1)
    self.stackedWidget.addWidget(self.tela3)

    # Adiciona o QStackedWidget no layout principal da janela
    self.layoutPrincipal.addWidget(self.stackedWidget)

    # Configurações de Timers e Notificações
    self.timer = QTimer(self)
    self.timer.timeout.connect(
        lambda: self.atualizarSubmenuPorta(
            self.menuConfiguracoes.findChild(QMenu, 'Porta')
        )
    )
    self.timer.start(1000)

    self.settings = QSettings('AbaTrack', 'AbaTrack')
    self.resetarAvisos()
    self.adaptador.erroDecodificacao.connect(
        lambda: self.mostrarAvisoErroBaud(
            'Erro de decodificação', 'Erro ao decodificar dados'
        )
    )

  def centralizarNaTela(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())

  def listarPortas(self):
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]

  def atualizarLabelDadoBruto(self, ultimoPacoteDados):
    self.dadosRecebidos = True
    self.labelPacotesBrutos.setText(
        'Dados dos pacotes recebidos: '
        + ':'.join(map(str, ultimoPacoteDados))
    )

  def atualizarLabelDadosdoRadio(self, numeroDePacotes):
    if self.repositorio.numerodepacotes:
      ultimo_pacote = int(self.repositorio.numerodepacotes[-1])
      rssi = int(self.repositorio.RSSI[-1])
      tamanho_pacote = int(self.repositorio.tamanhopacote[-1])
      self.labelDadosdoRadio.setText(
          f'<b>Número de Pacotes:</b> {ultimo_pacote}<br><b>RSSI:</b> {rssi}'
          f' dBm<br><b>Tamanho:</b> {tamanho_pacote} bytes'
      )

  def atualizarLabelDadosGPS(self, pacoteDadosGPS):
    latitude = self.repositorio.latitude[-1]
    longitude = self.repositorio.longitude[-1]
    sats = int(self.repositorio.sats[-1])
    self.labelDadosGPS.setText(
        f'<div style="text-align: center;"><b>Dados'
        f' GPS</b></div><br>Latitude: {latitude}<br>Longitude:'
        f' {longitude}<br>Sats: {sats}'
    )
    self.atualizarMapaOffline(latitude, longitude)

  def atualizarLabelDadosGiro(self, pacoteGiro):
    roll = self.repositorio.roll[-1]
    pitch = self.repositorio.pitch[-1]
    yaw = self.repositorio.yaw[-1]

    self.cube.resetTransform()
    self.cube.rotate(roll, 1, 0, 0)
    self.cube.rotate(pitch, 0, 1, 0)
    self.cube.rotate(yaw, 0, 0, 1)

    self.labelDadosGyro.setText(
        f'<div style="text-align: center;"><b>Dados'
        f' Giro</b></div><br>Roll: {roll}<br>Pitch: {pitch}<br>Yaw: {yaw}'
    )

  def iniciarLeitura(self):
    if self.thread is None or not self.thread.isRunning():
      self.thread = ThreadPrincipal(self.adaptador)
      self.thread.ultimosSubdadosTemperaturaTempo.connect(
          self.graficoDinamico.atualizarGrafico
      )
      self.thread.ultimosSubdadosPressTemp.connect(
          self.graficoPressaoTemp.atualizarGrafico
      )
      self.thread.ultimosSubdadosAltTemp.connect(
          self.graficoAltTemp.atualizarGrafico
      )

      self.thread.ultimosDadosBrutos.connect(self.atualizarLabelDadoBruto)
      self.thread.dadosdoRadio.connect(self.atualizarLabelDadosdoRadio)
      self.thread.pacoteDadosGPS.connect(self.atualizarLabelDadosGPS)
      self.thread.pacoteGiro.connect(self.atualizarLabelDadosGiro)

      self.thread.start()

  def pressionarDesconectar(self):
    self.adaptador.desconectar()
    if self.thread is not None:
      self.thread.stop()
      self.mostrarAvisoSemCheckbox('Desconexão', 'Desconectado do Arduino.')
    else:
      self.mostrarAvisoSemCheckbox(
          'Desconexão', 'Nenhum arduino foi conectado ainda.'
      )

  def pressionarConectar(self):
    try:
      self.adaptador.conectar()
      self.iniciarLeitura()
      self.mostrarToast('Conectado com sucesso!')
    except Exception as e:
      self.mostrarAviso('Erro ao conectar', str(e))
      self.pressionarDesconectar()

  def mostrarToast(self, mensagem):
    toast = QLabel(mensagem, self)
    toast.setStyleSheet(
        'background-color: #444; color: white; padding: 10px; border-radius:'
        ' 5px;'
    )
    toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
    toast.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
    )
    toast.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    toast.setGeometry(
        self.geometry().center().x() - 100,
        self.geometry().center().y() - 50,
        200,
        50,
    )
    toast.show()
    QTimer.singleShot(2000, toast.close)

  def salvarDados(self):
    salvarDadosTXT(self.repositorio)
    self.mostrarAviso('Aviso', 'Dados Salvos.')

  def salvarDadosCSV(self):
    try:
      now = datetime.now()
      formatted_time = now.strftime('%Y-%m-%d_%H-%M-%S')
      default_filename = f'dados_{formatted_time}.csv'
      save_path = os.path.join(os.getcwd(), default_filename)

      with open(save_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ['Tempo', 'Temperatura', 'Pressão', 'Altitude']
        )  # Cabeçalhos
        for i in range(len(self.repositorio.tempo)):
          writer.writerow([
              self.repositorio.tempo[i],
              self.repositorio.dadosTemperatura[i],
              self.repositorio.pressao[i],
              self.repositorio.altitude[i],
          ])

      self.mostrarAviso('Sucesso', f'Dados salvos em: {save_path}')
    except Exception as e:
      self.mostrarAviso('Erro ao salvar dados', str(e))

  def salvarImagemMapa(self):
    try:
      screenshot_path = os.path.join(os.getcwd(), 'mapa_screenshot.png')
      self.mapaView.grab().save(screenshot_path)
      self.mostrarAviso(
          'Sucesso', f'Imagem do mapa salva em: {screenshot_path}'
      )
    except Exception as e:
      self.mostrarAviso('Erro ao salvar imagem do mapa', str(e))

  def salvarHTMLMapa(self):
    try:
      mapa_path = os.path.join(
          os.path.dirname(os.path.abspath(__file__)), 'mapaatualizado.html'
      )
      save_path = os.path.join(os.getcwd(), 'mapa_atualizado.html')
      with open(mapa_path, 'r', encoding='utf-8') as original_file:
        html_content = original_file.read()
      with open(save_path, 'w', encoding='utf-8') as updated_file:
        updated_file.write(html_content)
      self.mostrarAviso('Sucesso', f'HTML do mapa salvo em: {save_path}')
    except Exception as e:
      self.mostrarAviso('Erro ao salvar HTML do mapa', str(e))

  def aplicarEstiloMenuBar(self):
    estilo_menu_bar = """
        QMenuBar { background-color: #63A32E; color: white; font-size: 13px; }
        QMenuBar::item { background-color: #63A32E; color: white; font-size: 16px; padding: 10px 15px; }
        QMenuBar::item:selected { background-color: #4CAF50; }
        QMenu { background-color: #1C1C1C; color: white; border: 1px solid #4CAF50; font-size: 14px; }
        QMenu::item { background-color: transparent; padding: 8px 20px; }
        QMenu::item:selected { background-color: #4CAF50; color: white; }
        """
    self.menuBar.setStyleSheet(estilo_menu_bar)

  def criarMenu(self):
    path_abatrack = os.path.join(os.path.dirname(__file__), '..')

    menuArquivo = self.menuBar.addMenu('Arquivo')
    acaoMonitorSerial = menuArquivo.addAction('Abrir Monitor Serial')
    acaoMonitorSerial.triggered.connect(self.abrirMonitorSerial)

    submenuSalvarDados = menuArquivo.addMenu('Salvar Dados')
    acaoSalvarTXT = submenuSalvarDados.addAction('Salvar em TXT')
    acaoSalvarTXT.triggered.connect(self.salvarDados)
    acaoSalvarCSV = submenuSalvarDados.addAction('Salvar em CSV')
    acaoSalvarCSV.triggered.connect(self.salvarDadosCSV)

    submenuSalvarGraficos = menuArquivo.addMenu('Salvar Gráficos')
    acaoSalvarGraficoTemp = submenuSalvarGraficos.addAction(
        'Salvar Gráfico Temperatura'
    )
    acaoSalvarGraficoTemp.triggered.connect(
        lambda: salvarGrafico_useCase(
            self.repositorio.tempo,
            self.repositorio.dadosTemperatura,
            'Tempos (s)',
            'Temperatura (°C)',
            os.path.join(path_abatrack, 'dados_salvos'),
            salvarGrafico,
        )
    )

    acaoSalvarGraficoPres = submenuSalvarGraficos.addAction(
        'Salvar Gráfico Pressão'
    )
    acaoSalvarGraficoPres.triggered.connect(
        lambda: salvarGrafico_useCase(
            self.repositorio.tempo,
            self.repositorio.dadosTemperatura,
            'Tempos (s)',
            'Pressão ()',
            os.path.join(path_abatrack, 'dados_salvos'),
            salvarGrafico,
        )
    )

    acaoSalvarGraficoAlt = submenuSalvarGraficos.addAction(
        'Salvar Gráfico Altitude'
    )
    acaoSalvarGraficoAlt.triggered.connect(
        lambda: salvarGrafico_useCase(
            self.repositorio.tempo,
            self.repositorio.dadosTemperatura,
            'Tempos (s)',
            'Altitude ()',
            os.path.join(path_abatrack, 'dados_salvos'),
            salvarGrafico,
        )
    )

    acaoSair = menuArquivo.addAction('Sair')
    acaoSair.triggered.connect(self.close)

    self.menuConfiguracoes = self.menuBar.addMenu('Configurações')
    submenuPorta = self.menuConfiguracoes.addMenu('Porta')
    submenuPorta.setObjectName('Porta')
    self.atualizarSubmenuPorta(submenuPorta)

    submenuBaudRate = self.menuConfiguracoes.addMenu('Baud Rate')
    submenuBaudRate.setObjectName('Baud Rate')
    self.atualizarSubmenuBaudRate(submenuBaudRate)

    acaoConectar = self.menuConfiguracoes.addAction('Conectar')
    acaoConectar.triggered.connect(self.pressionarConectar)
    acaoDesconectar = self.menuConfiguracoes.addAction('Desconectar')
    acaoDesconectar.triggered.connect(self.pressionarDesconectar)

    menuAjuda = self.menuBar.addMenu('Ajuda')
    acaoSobre = menuAjuda.addAction('Sobre')
    acaoSobre.triggered.connect(self.mostrarSobre)

    menuMapa = self.menuBar.addMenu('Mapa')
    acaoSalvarImagemMapa = menuMapa.addAction('Salvar Imagem do Mapa')
    acaoSalvarImagemMapa.triggered.connect(self.salvarImagemMapa)
    acaoSalvarHTMLMapa = menuMapa.addAction('Salvar HTML do Mapa')
    acaoSalvarHTMLMapa.triggered.connect(self.salvarHTMLMapa)

    submenuSelecionarMapa = menuMapa.addMenu('Selecionar Mapa')
    submenuSelecionarMapa.setObjectName('SelecionarMapa')
    self.atualizarSubmenuSelecionarMapa(submenuSelecionarMapa)

    self.menuBar.update()

  def atualizarSubmenuPorta(self, submenuPorta):
    if submenuPorta is not None:
      submenuPorta.clear()
      portas_disponiveis = self.listarPortas()
      acaoGroupPorta = QActionGroup(self)

      for porta in portas_disponiveis:
        acaoPorta = submenuPorta.addAction(porta)
        acaoPorta.setCheckable(True)
        acaoPorta.setChecked(porta == self.configs.portaArduino)
        acaoPorta.triggered.connect(
            lambda checked, p=porta: self.selecionarPorta(p)
        )
        acaoGroupPorta.addAction(acaoPorta)

  def atualizarSubmenuBaudRate(self, submenuBaudRate):
    if submenuBaudRate is not None:
      submenuBaudRate.clear()
      baud_rates = ['9600', '115200']
      acaoGroupBaudRate = QActionGroup(self)
      for baud_rate in baud_rates:
        acaoBaudRate = submenuBaudRate.addAction(baud_rate)
        acaoBaudRate.setCheckable(True)
        acaoBaudRate.setChecked(baud_rate == str(self.configs.baudRate))
        acaoBaudRate.triggered.connect(
            lambda checked, b=baud_rate: self.selecionarBaudRate(b)
        )
        acaoGroupBaudRate.addAction(acaoBaudRate)

  def selecionarPorta(self, porta):
    self.configs.portaArduino = porta
    submenuPorta = self.menuConfiguracoes.findChild(QMenu, 'Porta')
    self.atualizarSubmenuPorta(submenuPorta)

  def selecionarBaudRate(self, baud_rate):
    self.configs.baudRate = int(baud_rate)
    submenuBaudRate = self.menuConfiguracoes.findChild(QMenu, 'Baud Rate')
    self.atualizarSubmenuBaudRate(submenuBaudRate)

  def mostrarSobre(self):
    QMessageBox.about(
        self,
        'Sobre',
        'AbaTrack 1.0.11v\nDesenvolvido pelos membros da UERJ Sats: Thiago'
        ' Martins e Kataryne Cunha.\nQt: 5.15.2 PyQt5: 5.15.11',
    )

  def adicionarTituloMenu(self):
    titulo = QLabel('AbaTrack', self)
    titulo.setStyleSheet(
        'color: #FFF; font-family: "Jaini Purva"; font-size: 18px;'
        ' margin-left: 20px;'
    )

    base_path = os.path.dirname(os.path.dirname(__file__))
    image_path = os.path.join(base_path, 'imgs', 'abasat.png')
    imagem = QLabel(self)
    pixmap = QPixmap(image_path)
    if not pixmap.isNull():
      pixmap = pixmap.scaledToHeight(
          18, Qt.TransformationMode.SmoothTransformation
      )
      imagem.setPixmap(pixmap)

    layout = QHBoxLayout()
    layout.addWidget(titulo)
    layout.addWidget(imagem)
    layout.addStretch()

    widget = QWidget(self)
    widget.setLayout(layout)
    self.menuBar.setCornerWidget(widget, Qt.Corner.TopLeftCorner)

  def mostrarAvisoSalvarTxt(self, titulo, mensagem):
    if self.settings.value('mostrarAvisosSalvartxt', True, type=bool):
      aviso = QMessageBox()
      aviso.setIcon(QMessageBox.Icon.Warning)
      aviso.setWindowTitle(titulo)
      aviso.setText(mensagem)
      aviso.setWindowIcon(QIcon(self.icon_path))
      checkbox = QCheckBox('Não mostrar novamente')
      aviso.setCheckBox(checkbox)
      if (
          aviso.exec() == QMessageBox.StandardButton.Ok
          and checkbox.isChecked()
      ):
        self.settings.setValue('mostrarAvisosSalvartxt', False)

  def mostrarAvisoGrafico(self, titulo, mensagem):
    if self.settings.value('mostrarAvisosGrafico', True, type=bool):
      aviso = QMessageBox()
      aviso.setIcon(QMessageBox.Icon.Warning)
      aviso.setWindowTitle(titulo)
      aviso.setText(mensagem)
      aviso.setWindowIcon(QIcon(self.icon_path))
      checkbox = QCheckBox('Não mostrar novamente')
      aviso.setCheckBox(checkbox)
      if (
          aviso.exec() == QMessageBox.StandardButton.Ok
          and checkbox.isChecked()
      ):
        self.settings.setValue('mostrarAvisosGrafico', False)

  def mostrarAvisoErroBaud(self, titulo, mensagem):
    aviso = QMessageBox(self)
    aviso.setWindowTitle(titulo)
    aviso.setText(mensagem)
    aviso.setIcon(QMessageBox.Icon.Warning)
    aviso.setWindowIcon(QIcon(self.icon_path))
    aviso.exec()

  def mostrarAviso(self, titulo, mensagem):
    if self.settings.value('mostrarAvisos', True, type=bool):
      aviso = QMessageBox()
      aviso.setIcon(QMessageBox.Icon.Warning)
      aviso.setWindowTitle(titulo)
      aviso.setText(mensagem)
      aviso.setWindowIcon(QIcon(self.icon_path))
      checkbox = QCheckBox('Não mostrar novamente')
      aviso.setCheckBox(checkbox)
      if (
          aviso.exec() == QMessageBox.StandardButton.Ok
          and checkbox.isChecked()
      ):
        self.settings.setValue('mostrarAvisos', False)

  def mostrarAvisoSemCheckbox(self, titulo, mensagem):
    aviso = QMessageBox()
    aviso.setIcon(QMessageBox.Icon.Warning)
    aviso.setWindowTitle(titulo)
    aviso.setText(mensagem)
    aviso.setWindowIcon(QIcon(self.icon_path))
    aviso.exec()

  def mostrarAvisoDesconectar(self):
    aviso = QMessageBox(self)
    aviso.setWindowTitle('Desconectado')
    aviso.setText('O dispositivo foi desconectado com sucesso.')
    aviso.setIcon(QMessageBox.Icon.Information)
    aviso.setWindowIcon(QIcon(self.icon_path))
    aviso.exec()

  def resetarAvisos(self):
    self.settings.setValue('mostrarAvisos', True)
    self.settings.setValue('mostrarAvisosGrafico', True)
    self.settings.setValue('mostrarAvisosSalvartxt', True)
    self.settings.setValue('mostrarAvisosBaud', True)

  def create_cube(self):
    verts = np.array([
        [1, 1, 1],
        [1, 1, -1],
        [1, -1, 1],
        [1, -1, -1],
        [-1, 1, 1],
        [-1, 1, -1],
        [-1, -1, 1],
        [-1, -1, -1],
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
        [3, 7, 5],
    ])
    return gl.MeshData(vertexes=verts, faces=faces)

  def enviarComandoSerial(self):
    comando = self.inputComando.text()
    if comando:
      try:
        self.adaptador.enviarComando(comando)
        self.inputComando.clear()
        self.mostrarToast('Comando enviado com sucesso!')
      except Exception as e:
        self.mostrarAviso('Erro ao enviar comando', str(e))

  def closeEvent(self, event):
    if self.dadosRecebidos:
      self.salvarDados()
    event.accept()

  def resizeEvent(self, event):
    super().resizeEvent(event)

  def atualizarMapaOffline(self, latitude, longitude):
    try:
      js = f'atualizarPosicao({latitude}, {longitude});'
      self.mapaView.page().runJavaScript(js)
    except Exception as e:
      self.mostrarAviso('Erro ao atualizar o mapa', str(e))

  def atualizarSubmenuSelecionarMapa(self, submenuSelecionarMapa):
    if submenuSelecionarMapa is not None:
      submenuSelecionarMapa.clear()
      mapas_disponiveis = [
          ('Mapa Teste de Vôo', 'mapa.html'),
          ('Mapa IREC', 'mapa2.html'),
          ('Mapa CubeDesign', 'mapa3.html'),
      ]
      acaoGroupMapa = QActionGroup(self)
      for nome, arquivo in mapas_disponiveis:
        acaoMapa = submenuSelecionarMapa.addAction(nome)
        acaoMapa.setCheckable(True)
        acaoMapa.setChecked(arquivo == 'mapa.html')
        acaoMapa.triggered.connect(
            lambda checked, f=arquivo: self.selecionarMapaOffline(f)
        )
        acaoGroupMapa.addAction(acaoMapa)

  def selecionarMapaOffline(self, arquivo_mapa):
    try:
      mapa_path = os.path.join(
          os.path.dirname(os.path.abspath(__file__)), arquivo_mapa
      )
      self.mapaView.setUrl(QtCore.QUrl.fromLocalFile(mapa_path))
      self.mostrarToast(f'Mapa {arquivo_mapa} selecionado com sucesso!')
    except Exception as e:
      self.mostrarAviso('Erro ao selecionar o mapa', str(e))

  def abrirMonitorSerial(self):
    try:
      style = self.styleSheet()
      if style:
        self.tela_serial = TelaSerial(None, style_sheet=style)
      else:
        self.tela_serial = TelaSerial(None)
      self.tela_serial.show()
    except Exception as e:
      self.mostrarAviso('Erro', str(e))