import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout ,QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Teste de botões e labels")
        self.setFixedSize(800, 600)

        # Cria Widgets
        msgGrafico1 = QLabel("Gráfico 1")
        msgGrafico2 = QLabel("Gráfico 2")

        botaoGrafico1 = QPushButton("Botão 1")
        botaoGrafico1.clicked.connect(lambda: print("Botão 1 apertado."))
        botaoGrafico2 = QPushButton("Botão 2")
        botaoGrafico2.clicked.connect(lambda: print("Botão 2 apertado."))

        # Organiza os widgets num layout
        mainLayout = QHBoxLayout()
        layoutEsquerdo = QVBoxLayout()
        layoutDireito = QVBoxLayout()

        layoutEsquerdo.addWidget(msgGrafico1)
        layoutEsquerdo.addWidget(msgGrafico2)

        layoutDireito.addWidget(botaoGrafico1)
        layoutDireito.addWidget(botaoGrafico2)

        mainLayout.addLayout(layoutEsquerdo)
        mainLayout.addLayout(layoutDireito)

        # Cria um widget principal e adiciona o layout
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)

        # Adiciona o widget principal à janela principal
        self.setCentralWidget(centralWidget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())