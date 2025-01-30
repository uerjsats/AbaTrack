import sys
import random
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QTimer

class GraficoDinamico(QWidget):
    def __init__(self, dados, janela_visivel=10):
        super().__init__()

        self.y_data = dados
        self.x_data = list(range(len(dados)))
        self.janela_visivel = janela_visivel

        # Criando a figura e os eixos do Matplotlib
        self.figure, self.ax = plt.subplots()
        self.ax.grid(True)
        self.canvas = FigureCanvas(self.figure)

        self.line, = self.ax.plot(self.x_data, self.y_data, marker='o', linestyle='-', color='b', label="Valores")

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Timer para atualizar o gráfico periodicamente
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_grafico)
        self.timer.start(500)

    def atualizar_grafico(self):
        self.x_data = list(range(len(self.y_data)))

        self.line.set_data(self.x_data, self.y_data)

        # Ajusta os limites do eixo X para manter o efeito de "rolagem"
        if len(self.y_data) > self.janela_visivel:
            inicio = len(self.y_data) - self.janela_visivel
            fim = len(self.y_data)
        else:
            inicio = 0
            fim = max(self.janela_visivel, len(self.y_data))  

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

        self.canvas.draw()  # Redesenha o gráfico

class MainWindow(QMainWindow):
    def __init__(self, dados):
        super().__init__()
        self.setWindowTitle("Gráfico Dinâmico com Rolagem")

        # Criando o widget do gráfico e definindo como central
        self.grafico = GraficoDinamico(dados)
        self.setCentralWidget(self.grafico)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Vetor com dados externos
    dados_externos = []

    window = MainWindow(dados_externos)
    window.show()

    # Adição de valores de forma externa (programar para ler do monitor serial)
    def adicionar_valor_externo():
        novo_valor = random.randint(0, 10)  # Gera um valor aleatório
        dados_externos.append(novo_valor)

    # Timer para adicionar novos valores automaticamente (apenas para teste)
    timer_adicionar = QTimer()
    timer_adicionar.timeout.connect(adicionar_valor_externo)
    timer_adicionar.start(1000)  # Adiciona um novo valor a cada 1 segundo

    sys.exit(app.exec())