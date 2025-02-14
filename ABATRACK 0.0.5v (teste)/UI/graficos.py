import time
import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import mplcursors

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
        
        # Ativar tooltips
        self.cursor = mplcursors.cursor(self.line, hover=True)
        self.cursor.connect("add", self.show_tooltip)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def atualizarGrafico(self, novo_dado=None):
        if novo_dado is not None:
            try:
                self.y_data.append(float(novo_dado))  # Adiciona o novo dado à lista y_data
                self.line.set_ydata(self.y_data)
                self.line.set_xdata(range(len(self.y_data)))
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()
            except ValueError as e:
                self.mostrarAviso("Erro ao converter dado para float", str(e))

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

    def mostrarAviso(self, titulo, mensagem):
        aviso = QMessageBox()
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle(titulo)
        aviso.setText(mensagem)
        aviso.exec()

    def show_tooltip(self, sel):
        x, y = sel.target
        sel.annotation.set_text(f"Temperatura: {y}°C \nTempo: {x}s")
        sel.annotation.get_bbox_patch().set(fc="green", alpha=0.2)  # Define a cor de fundo e a opacidade
        sel.annotation.arrow_patch.set(arrowstyle="wedge,tail_width=0.5", fc="white", alpha=0)