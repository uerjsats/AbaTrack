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
from integracao.adaptador_arduino import AdaptadorArduino
from integracao.thread_leitor_serial import ThreadLeituraSerial
from UI.graficos import GraficoDinamico
from UI.thread_leitor_repositorio import ThreadLeituraRepositorio
from UI.UI2 import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))
    janela = MainWindow()
    janela.show()
    app.exec()