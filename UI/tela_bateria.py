import math

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from aplicacao.bateria import sensorValido
from dominio.entidades import RepositorioTelemetria
from UI.graficosGenericos import GraficoDinamicoGenerico

COR_BATERIA = '#2E6F4E'
COR_BATERIA_ALERTA = '#B3261E'   # temperatura abaixo de 0 °C
COR_TENSAO = '#2E5E8A'
COR_CORRENTE = '#8A6A2E'
COR_POTENCIA = '#6A4C93'
COR_SATELITE = '#A34B2E'         # mesma cor do cartao do GPS


class CartaoDados(QFrame):
    """Cartao no estilo do painel de dados do GPS."""

    def __init__(self, titulo: str, cor: str):
        super().__init__()
        self.titulo = titulo
        self.setFixedHeight(175)
        self.definirCor(cor)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(10)
        sombra.setOffset(5, 5)
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        self.label = QLabel('')
        self.label.setStyleSheet('font-size: 15px;')
        self.label.setTextFormat(Qt.RichText)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.definirTexto('')

    def definirCor(self, cor: str):
        self.setStyleSheet(
            f'QFrame {{ background-color: {cor}; border-radius: 10px; color: white; padding: 6px; }}'
            'QLabel { background: transparent; padding: 0px; }'
        )

    def definirTexto(self, corpo: str):
        self.label.setText(
            f'<div style="text-align: center;"><b>{self.titulo}</b><br>{corpo}</div>'
        )


def _formatar(valor, casas, unidade):
    if valor is None or (isinstance(valor, float) and not math.isfinite(valor)):
        return '--'
    return f'{valor:.{casas}f} {unidade}'


def potencia(tensao, corrente):
    """Potencia em watts (V x A), ou None se algum dos dois nao e um numero."""
    try:
        valor = float(tensao) * float(corrente)
    except (TypeError, ValueError):
        return None
    return valor if math.isfinite(valor) else None


class TelaBateria(QWidget):
    """Monitoramento da bateria: 4 graficos e, embaixo, o ultimo valor de cada um."""

    def __init__(self, repositorio: RepositorioTelemetria, parent=None):
        super().__init__(parent)
        self.repositorio = repositorio
        self.minimaBateria = None
        self.maximaBateria = None
        self.minimaCorrente = None
        self.maximaCorrente = None

        self.graficoBateria = GraficoDinamicoGenerico(
            'Temperatura da bateria (°C) x Tempo (s)', 'Tempo (s)', 'Temperatura (°C)', [], [])
        self.graficoTensao = GraficoDinamicoGenerico(
            'Tensão (V) x Tempo (s)', 'Tempo (s)', 'Tensão (V)', [], [])
        self.graficoCorrente = GraficoDinamicoGenerico(
            'Corrente (A) x Tempo (s)', 'Tempo (s)', 'Corrente (A)', [], [])
        self.graficoSatelite = GraficoDinamicoGenerico(
            'Temperatura do satélite (°C) x Tempo (s)', 'Tempo (s)', 'Temperatura (°C)', [], [])
        # linha de referencia em 0 °C (aparece quando a faixa do grafico chega perto)
        self.graficoBateria.ax.axhline(0, color='#E53935', linestyle=':', linewidth=1)

        grade = QGridLayout()
        grade.setSpacing(10)
        grade.addWidget(self.graficoBateria, 0, 0)
        grade.addWidget(self.graficoTensao, 0, 1)
        grade.addWidget(self.graficoCorrente, 1, 0)
        grade.addWidget(self.graficoSatelite, 1, 1)

        self.cartaoBateria = CartaoDados('Temperatura da bateria', COR_BATERIA)
        self.cartaoTensao = CartaoDados('Tensão', COR_TENSAO)
        self.cartaoCorrente = CartaoDados('Corrente', COR_CORRENTE)
        self.cartaoPotencia = CartaoDados('Potência', COR_POTENCIA)
        self.cartaoSatelite = CartaoDados('Temperatura do satélite', COR_SATELITE)
        cartoes = QHBoxLayout()
        cartoes.setSpacing(15)
        for cartao in (self.cartaoBateria, self.cartaoTensao, self.cartaoCorrente,
                       self.cartaoPotencia, self.cartaoSatelite):
            cartoes.addWidget(cartao)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.addLayout(grade, stretch=1)
        layout.addLayout(cartoes)

        self._mostrarCartoesVazios()

    def _mostrarCartoesVazios(self):
        self.cartaoBateria.definirTexto('<br>Média: --<br>Máxima: --<br>Mínima: --')
        self.cartaoTensao.definirTexto('<br>--')
        self.cartaoCorrente.definirTexto('<br>Atual: --<br>Máxima: --<br>Mínima: --')
        self.cartaoPotencia.definirTexto('<br>--')
        self.cartaoSatelite.definirTexto('<br>--')

    # --------------------------------------------------------------- dados
    def atualizarBateria(self, tempo, tensao, corrente, mediaTemperatura):
        """Chamada a cada pacote. mediaTemperatura e NaN se os 2 sensores falharam."""
        self.graficoTensao.atualizarGrafico(tempo, tensao)
        self.graficoCorrente.atualizarGrafico(tempo, corrente)
        self.cartaoTensao.definirTexto(f'<br>{_formatar(tensao, 3, "V")}')
        if corrente is not None and math.isfinite(corrente):
            if self.minimaCorrente is None or corrente < self.minimaCorrente:
                self.minimaCorrente = corrente
            if self.maximaCorrente is None or corrente > self.maximaCorrente:
                self.maximaCorrente = corrente
        self.cartaoCorrente.definirTexto(
            f'<br>Atual: {_formatar(corrente, 3, "A")}<br>'
            f'Máxima: {_formatar(self.maximaCorrente, 3, "A")}<br>'
            f'Mínima: {_formatar(self.minimaCorrente, 3, "A")}'
        )
        self.cartaoPotencia.definirTexto(f'<br>{_formatar(potencia(tensao, corrente), 2, "W")}')

        temMedia = mediaTemperatura is not None and math.isfinite(mediaTemperatura)
        if temMedia:
            self.graficoBateria.atualizarGrafico(tempo, mediaTemperatura)
            if self.minimaBateria is None or mediaTemperatura < self.minimaBateria:
                self.minimaBateria = mediaTemperatura
            if self.maximaBateria is None or mediaTemperatura > self.maximaBateria:
                self.maximaBateria = mediaTemperatura

        r = self.repositorio
        sensor1 = r.tempbateria1[-1] if r.tempbateria1 else None
        sensor2 = r.tempbateria2[-1] if r.tempbateria2 else None
        detalhe = (
            f'Sensor 1: {_formatar(sensor1, 1, "°C") if sensorValido(sensor1) else "sem leitura"}<br>'
            f'Sensor 2: {_formatar(sensor2, 1, "°C") if sensorValido(sensor2) else "sem leitura"}'
        )
        media = mediaTemperatura if temMedia else None
        self.cartaoBateria.definirTexto(
            f'<br>Média: {_formatar(media, 1, "°C")}<br>'
            f'Máxima: {_formatar(self.maximaBateria, 1, "°C")}<br>'
            f'Mínima: {_formatar(self.minimaBateria, 1, "°C")}<br>{detalhe}'
        )
        # abaixo de 0 °C o cartao fica vermelho
        alerta = temMedia and mediaTemperatura < 0
        self.cartaoBateria.definirCor(COR_BATERIA_ALERTA if alerta else COR_BATERIA)

    def atualizarSatelite(self, tempo, temperatura):
        self.graficoSatelite.atualizarGrafico(tempo, temperatura)
        self.cartaoSatelite.definirTexto(f'<br>{_formatar(temperatura, 2, "°C")}')
