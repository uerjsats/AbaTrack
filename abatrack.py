import os
import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# 1. Força o Windows a associar o ícone ao processo na barra de tarefas
try:
    myappid = 'uerjsats.abatrack.telemetry.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Caminho dos módulos
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integracao'))

from UI.UI2 import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 2. Determina o caminho base dinâmico (Dev vs PyInstaller)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, "imgs", "AbaTrack.ico")
    
    # Define o ícone no app
    app.setWindowIcon(QIcon(icon_path))
    
    janela = MainWindow()
    # 3. Garante que a janela principal receba o ícone diretamente
    janela.setWindowIcon(QIcon(icon_path))
    
    janela.show()
    app.exec()