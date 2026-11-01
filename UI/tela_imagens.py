import os
import subprocess
import sys
from datetime import datetime

from PIL import Image
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from aplicacao.tratamento_imagem import abrirJpeg, aplicarTratamento
from aplicacao.use_cases import telemetriaDaImagem
from dominio.entidades import ImagemTelemetria, RepositorioTelemetria

TAMANHO_MINIATURA = 72

ESTILO = """
    QFrame#painelLateral { background-color: #252525; border-radius: 10px; }
    QLabel { color: white; font-size: 13px; background-color: transparent; }
    QLabel#titulo { font-size: 15px; font-weight: bold; }
    QLabel#visor { background-color: #000000; border-radius: 10px; color: #888; }
    QCheckBox { color: white; font-size: 13px; background-color: transparent; }
    QPushButton {
        color: white; background-color: #3a3a3a; border: 1px solid #555;
        border-radius: 5px; padding: 6px 10px; font-size: 13px;
    }
    QPushButton:hover { border: 1px solid #63A32E; }
    QPushButton:disabled { color: #777; }
    QProgressBar {
        border: 1px solid #444; border-radius: 5px; text-align: center;
        color: white; background-color: #252525;
    }
    QProgressBar::chunk { background-color: #63A32E; border-radius: 4px; }
    QListWidget {
        background-color: #1C1C1C; border: 1px solid #444; color: white;
        font-size: 12px;
    }
    QListWidget::item:selected { background-color: #63A32E; color: white; }
"""


def pilParaPixmap(imagem: Image.Image) -> QPixmap:
    rgb = imagem.convert('RGB')
    largura, altura = rgb.size
    qimagem = QImage(rgb.tobytes(), largura, altura, 3 * largura,
                     QImage.Format_RGB888)
    return QPixmap.fromImage(qimagem.copy())


class TelaImagens(QWidget):

    """Aba de imagens: so mostra e trata o que esta em repositorio.imagens."""

    def __init__(self, repositorio: RepositorioTelemetria, pastaImagens: str,
                 parent=None):
        super().__init__(parent)
        self.repositorio = repositorio
        self.pastaImagens = pastaImagens
        self.linhas = []        # ImagemTelemetria de cada linha do historico
        self.atual = None       # ImagemTelemetria selecionada
        self.pilAtual = None    # JPEG decodificado (None se corrompido)
        self.totalErros = 0

        self.setStyleSheet(ESTILO)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # ------------------------- visor (esquerda)
        colunaVisor = QVBoxLayout()
        self.visor = QLabel('Nenhuma imagem recebida ainda.')
        self.visor.setObjectName('visor')
        self.visor.setAlignment(Qt.AlignCenter)
        self.visor.setMinimumSize(320, 240)
        colunaVisor.addWidget(self.visor, stretch=1)

        self.labelInfo = QLabel('')
        self.labelInfo.setAlignment(Qt.AlignCenter)
        colunaVisor.addWidget(self.labelInfo)

        self.barraProgresso = QProgressBar()
        self.barraProgresso.setFormat('Aguardando imagem')
        self.barraProgresso.setValue(0)
        colunaVisor.addWidget(self.barraProgresso)
        layout.addLayout(colunaVisor, stretch=3)

        # ------------------------- painel lateral (direita)
        painel = QFrame()
        painel.setObjectName('painelLateral')
        painel.setFixedWidth(300)
        colunaPainel = QVBoxLayout(painel)
        colunaPainel.setContentsMargins(12, 12, 12, 12)
        colunaPainel.setSpacing(8)

        titulo = QLabel('Tratamento da imagem')
        titulo.setObjectName('titulo')
        colunaPainel.addWidget(titulo)

        self.checkAutoContraste = QCheckBox('Auto-contraste')
        self.checkInverter = QCheckBox('Inverter cores')
        colunaPainel.addWidget(self.checkAutoContraste)
        colunaPainel.addWidget(self.checkInverter)

        self.sliderBrilho = self._criarSlider(colunaPainel, 'Brilho')
        self.sliderContraste = self._criarSlider(colunaPainel, 'Contraste')

        self.botaoRestaurar = QPushButton('Restaurar original')
        colunaPainel.addWidget(self.botaoRestaurar)

        self.botaoSalvarOriginal = QPushButton('Salvar original (.jpg)')
        self.botaoSalvarTratada = QPushButton('Salvar tratada (.png)')
        self.botaoAbrirPasta = QPushButton('Abrir pasta das imagens')
        colunaPainel.addWidget(self.botaoSalvarOriginal)
        colunaPainel.addWidget(self.botaoSalvarTratada)
        colunaPainel.addWidget(self.botaoAbrirPasta)

        self.labelEstatisticas = QLabel('')
        colunaPainel.addWidget(self.labelEstatisticas)

        colunaPainel.addWidget(QLabel('Histórico da sessão:'))
        self.listaHistorico = QListWidget()
        self.listaHistorico.setIconSize(QSize(TAMANHO_MINIATURA, TAMANHO_MINIATURA))
        colunaPainel.addWidget(self.listaHistorico, stretch=1)
        layout.addWidget(painel)

        # ------------------------- sinais
        self.checkAutoContraste.toggled.connect(self.redesenhar)
        self.checkInverter.toggled.connect(self.redesenhar)
        self.sliderBrilho.valueChanged.connect(self.redesenhar)
        self.sliderContraste.valueChanged.connect(self.redesenhar)
        self.botaoRestaurar.clicked.connect(self.restaurarOriginal)
        self.botaoSalvarOriginal.clicked.connect(self.salvarOriginal)
        self.botaoSalvarTratada.clicked.connect(self.salvarTratada)
        self.botaoAbrirPasta.clicked.connect(self.abrirPasta)
        self.listaHistorico.currentRowChanged.connect(self.selecionarDoHistorico)

        self._atualizarEstatisticas()
        self._atualizarBotoes()

    def _criarSlider(self, layoutPai, nome):
        rotulo = QLabel(f'{nome}: 0')
        slider = QSlider(Qt.Horizontal)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.valueChanged.connect(lambda v: rotulo.setText(f'{nome}: {v}'))
        slider.rotulo = rotulo
        layoutPai.addWidget(rotulo)
        layoutPai.addWidget(slider)
        return slider

    # --------------------------------------------------------- recepcao
    def atualizarProgresso(self, lidos, total):
        self.barraProgresso.setMaximum(total)
        self.barraProgresso.setValue(lidos)
        self.barraProgresso.setFormat(f'Recebendo imagem: {lidos}/{total} bytes')

    def registrarErro(self, mensagem):
        self.totalErros += 1
        self.barraProgresso.setValue(0)
        self.barraProgresso.setFormat(f'Erro: {mensagem}')
        self._atualizarEstatisticas()

    def adicionarImagem(self, imagem: ImagemTelemetria):
        """Mostra uma imagem que acabou de entrar no repositorio."""
        self.barraProgresso.setMaximum(max(1, imagem.tamanho))
        self.barraProgresso.setValue(imagem.tamanho)
        self.barraProgresso.setFormat('Imagem completa')

        self.linhas.append(imagem)
        item = QListWidgetItem(self._textoItem(imagem))
        try:
            miniatura = pilParaPixmap(abrirJpeg(imagem.dadosJpeg)).scaled(
                TAMANHO_MINIATURA, TAMANHO_MINIATURA,
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item.setIcon(QIcon(miniatura))
        except Exception:
            pass
        self.listaHistorico.addItem(item)
        self.listaHistorico.setCurrentRow(len(self.linhas) - 1)
        self._atualizarEstatisticas()

    @staticmethod
    def _textoItem(imagem):
        return f"{imagem.horario.strftime('%H:%M:%S')} - {imagem.tamanho} B"

    # ------------------------------------------------------- exibicao
    def selecionarDoHistorico(self, linha):
        self.atual = self.linhas[linha] if 0 <= linha < len(self.linhas) else None
        self.pilAtual = None
        if self.atual is not None:
            try:
                self.pilAtual = abrirJpeg(self.atual.dadosJpeg)
            except Exception:
                self.pilAtual = None
        self.redesenhar()

    def _tratada(self):
        if self.atual is None or self.pilAtual is None:
            return None
        return aplicarTratamento(
            self.pilAtual,
            autoContraste=self.checkAutoContraste.isChecked(),
            inverter=self.checkInverter.isChecked(),
            brilho=self.sliderBrilho.value(),
            contraste=self.sliderContraste.value(),
        )

    def redesenhar(self, *_):
        self._atualizarBotoes()
        if self.atual is None:
            self.visor.setPixmap(QPixmap())
            self.visor.setText('Nenhuma imagem recebida ainda.')
            self.labelInfo.setText('')
            return
        tratada = self._tratada()
        if tratada is None:
            self.visor.setPixmap(QPixmap())
            self.visor.setText('JPEG corrompido: não foi possível exibir.\n'
                               'O arquivo recebido foi salvo mesmo assim.')
            self.labelInfo.setText(f'{self.atual.tamanho} bytes')
            return
        pixmap = pilParaPixmap(tratada).scaled(
            self.visor.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.visor.setText('')
        self.visor.setPixmap(pixmap)
        largura, altura = self.pilAtual.size
        texto = (f"{largura}x{altura} px  |  {self.atual.tamanho} bytes  |  "
                 f"{self.atual.horario.strftime('%d/%m/%Y %H:%M:%S')}")
        telemetria = telemetriaDaImagem(self.atual, self.repositorio)
        if telemetria:
            texto += (f"\nTelemetria no momento: t={telemetria['tempo']} s  |  "
                      f"alt={telemetria['altitude']} m  |  "
                      f"lat={telemetria['latitude']}  lon={telemetria['longitude']}")
        self.labelInfo.setText(texto)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.redesenhar()

    def _atualizarEstatisticas(self):
        self.labelEstatisticas.setText(
            f'Recebidas: {len(self.repositorio.imagens)}   |   Erros: {self.totalErros}')

    def _atualizarBotoes(self):
        temImagem = self.atual is not None
        self.botaoSalvarOriginal.setEnabled(temImagem)
        self.botaoSalvarTratada.setEnabled(temImagem and self.pilAtual is not None)

    # --------------------------------------------------------- acoes
    def restaurarOriginal(self):
        for controle in (self.checkAutoContraste, self.checkInverter):
            controle.blockSignals(True)
            controle.setChecked(False)
            controle.blockSignals(False)
        for slider in (self.sliderBrilho, self.sliderContraste):
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            slider.rotulo.setText(slider.rotulo.text().split(':')[0] + ': 0')
        self.redesenhar()

    def _nomeSugerido(self, extensao):
        return f"imagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensao}"

    def salvarOriginal(self):
        if self.atual is None:
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, 'Salvar imagem original', self._nomeSugerido('jpg'),
            'JPEG (*.jpg)')
        if caminho:
            with open(caminho, 'wb') as arquivo:
                arquivo.write(self.atual.dadosJpeg)

    def salvarTratada(self):
        tratada = self._tratada()
        if tratada is None:
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, 'Salvar imagem tratada', self._nomeSugerido('png'),
            'PNG (*.png)')
        if caminho:
            tratada.save(caminho)

    def abrirPasta(self):
        os.makedirs(self.pastaImagens, exist_ok=True)
        if sys.platform.startswith('win'):
            os.startfile(self.pastaImagens)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', self.pastaImagens])
        else:
            subprocess.Popen(['xdg-open', self.pastaImagens])
