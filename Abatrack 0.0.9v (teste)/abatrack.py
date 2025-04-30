import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'integracao'))

from UI.UI2 import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "imgs/AbaTrack.ico")))
    janela = MainWindow()
    janela.show()
    app.exec()