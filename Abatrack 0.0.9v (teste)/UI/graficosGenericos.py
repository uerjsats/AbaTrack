import time
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QCheckBox
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import mplcursors

class GraficoDinamicoGenerico(QWidget):
    def __init__(self, titulo: str, titulo_x: str, titulo_y: str, listaDadosX: list, listaDadosY: list):
        super().__init__()
        # PASSAGEM POR CÓPIA PRA NÃO DAR MERDA NO REPOSITÓRIO
        self.y_data = listaDadosY.copy()
        self.x_data = listaDadosX.copy()

        self.titulo_x = titulo_x
        self.titulo_y = titulo_y
        self.titulo = titulo
        self.erro_exibido = False  # Variável de controle para rastrear se o erro já foi exibido
        self.nao_mostrar_erro = False  # Variável de controle para "Não mostrar novamente"

        if len(listaDadosY) != len(listaDadosX):
            print(f"Aviso: erro nas quantidades de dados do grafico {titulo_x} x {titulo_y}.")
        self.janelaVisivel = 10

        # Criando figuras e eixos do Matplotlib
        self.figure, self.ax = plt.subplots()
        self.ax.set_title(titulo, fontsize=11, fontweight='bold', color="#D3D3D3")
        self.ax.grid(True, linestyle="--", alpha=0.7)
        self.ax.set_facecolor("#1C1C1C")
        self.figure.patch.set_facecolor("#1C1C1C")

        self.ax.tick_params(axis='x', colors='#D3D3D3')  
        self.ax.tick_params(axis='y', colors='#D3D3D3')

        self.ax.spines["left"].set_color("#D3D3D3")
        self.ax.spines["bottom"].set_color("#D3D3D3")
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.canvas = FigureCanvas(self.figure)
        
        self.line, = self.ax.plot(self.x_data, self.y_data, marker='o', linestyle='-', color='green', label="Valores")

        # Tooltips
        self.cursor = mplcursors.cursor(self.line, hover=True)
        self.cursor.connect("add", self.show_tooltip)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def atualizarGrafico(self, novoDadoX: float, novoDadoY: float):
        if novoDadoX is not None and novoDadoY is not None:
            try:
                self.y_data.append(novoDadoY)
                self.x_data.append(novoDadoX)

                self.line.set_xdata(self.x_data)
                self.line.set_ydata(self.y_data)

                # centralizar o gráfico no novo ponto adicionado
                if len(self.x_data) > 1:
                    x_centro = self.x_data[-1]
                    x_min = x_centro - self.janelaVisivel / 2
                    x_max = x_centro + self.janelaVisivel / 2
                    self.ax.set_xlim(x_min, x_max)

                # efeito rolagem e deixar visivel todos os pontos no gráfico
                if len(self.y_data) > 1:
                    y_min = min(self.y_data)
                    y_max = max(self.y_data)

                    if y_min == y_max:
                        y_min -= 0.1
                        y_max += 0.1

                    margem = (y_max - y_min) * 0.2
                    self.ax.set_ylim(y_min - margem, y_max + margem)
                
                
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()
            except ValueError as e:
                if not self.erro_exibido and not self.nao_mostrar_erro:
                    self.mostrarAviso("Erro ao converter dado para float", str(e))
                    self.erro_exibido = True

        self.line.set_data(self.x_data, self.y_data)

    def mostrarAviso(self, titulo, mensagem):
        aviso = QMessageBox()
        aviso.setIcon(QMessageBox.Icon.Warning)
        aviso.setWindowTitle(titulo)
        aviso.setText(mensagem)

        checkbox = QCheckBox("Não mostrar novamente")
        aviso.setCheckBox(checkbox)

        aviso.exec()

        if checkbox.isChecked():
            self.nao_mostrar_erro = True

    def show_tooltip(self, sel):
        x, y = sel.target
        sel.annotation.set_text(f"{y:.1f} {self.titulo_y}\n{x:.1f} {self.titulo_x}")
        sel.annotation.get_bbox_patch().set(fc="green", alpha=0.8)  # Define a cor de fundo e a opacidade
        sel.annotation.arrow_patch.set(arrowstyle="wedge,tail_width=0.5", fc="white", alpha=0)