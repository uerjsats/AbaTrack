import os
from datetime import datetime
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QComboBox, QTextEdit, QFileDialog, QLabel, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal

class SerialReaderThread(QThread):
    linhaRecebida = pyqtSignal(str)
    erro = pyqtSignal(str)

    def __init__(self, porta, baud):
        super().__init__()
        self.porta = porta
        self.baud = int(baud)
        self._rodando = True
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.porta, self.baud, timeout=1)
        except Exception as e:
            self.erro.emit(str(e))
            return
        while self._rodando:
            try:
                linha = self.ser.readline()
                if linha:
                    try:
                        texto = linha.decode('utf-8', errors='ignore').rstrip('\r\n')
                    except Exception:
                        texto = str(linha)
                    self.linhaRecebida.emit(texto)
            except Exception as e:
                self.erro.emit(str(e))
                break
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except: pass

    def stop(self):
        self._rodando = False
        self.wait(500)

class TelaSerial(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor Serial (simples)")
        self.resize(700, 400)
        self.thread = None
        self.log_path = None
        self.log_file = None
        self.autosave = True
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Top controls: portas e baud
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Porta:"))
        self.combo_portas = QComboBox()
        self.atualizar_portas()
        controls.addWidget(self.combo_portas)

        controls.addWidget(QLabel("Baud:"))
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "115200", "57600", "38400"])
        self.combo_baud.setCurrentText("9600")
        controls.addWidget(self.combo_baud)

        self.btn_atualizar = QPushButton("Atualizar portas")
        self.btn_atualizar.clicked.connect(self.atualizar_portas)
        controls.addWidget(self.btn_atualizar)

        self.btn_conectar = QPushButton("Conectar")
        self.btn_conectar.clicked.connect(self.conectar)
        controls.addWidget(self.btn_conectar)

        self.btn_desconectar = QPushButton("Desconectar")
        self.btn_desconectar.clicked.connect(self.desconectar)
        self.btn_desconectar.setEnabled(False)
        controls.addWidget(self.btn_desconectar)

        # Escolher arquivo e checkbox autosave
        self.chk_autosave = QCheckBox("Salvar automaticamente")
        self.chk_autosave.setChecked(True)
        self.chk_autosave.stateChanged.connect(lambda s: setattr(self, "autosave", bool(s)))
        controls.addWidget(self.chk_autosave)

        self.btn_escolher_arquivo = QPushButton("Escolher arquivo")
        self.btn_escolher_arquivo.clicked.connect(self.escolher_arquivo)
        controls.addWidget(self.btn_escolher_arquivo)

        layout.addLayout(controls)

        # Texto com dados recebidos
        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        layout.addWidget(self.texto)

        # Rodapé: limpar e salvar manual
        rodape = QHBoxLayout()
        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(lambda: self.texto.clear())
        rodape.addWidget(self.btn_limpar)

        self.btn_salvar = QPushButton("Salvar (Salvar como...)")
        self.btn_salvar.clicked.connect(self.salvar_arquivo)
        rodape.addWidget(self.btn_salvar)

        layout.addLayout(rodape)

    def atualizar_portas(self):
        portas = serial.tools.list_ports.comports()
        lista = [p.device for p in portas]
        self.combo_portas.clear()
        self.combo_portas.addItems(lista)

    def conectar(self):
        porta = self.combo_portas.currentText()
        baud = self.combo_baud.currentText()
        if not porta:
            self.texto.append("Nenhuma porta selecionada.")
            return

        # cria arquivo de log padrão se não escolhido
        if not self.log_path:
            nome = f"serial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            self.log_path = os.path.join(os.getcwd(), nome)

        # abre arquivo em append
        try:
            self.log_file = open(self.log_path, 'a', encoding='utf-8', errors='ignore')
            self.texto.append(f"Log: {self.log_path}")
        except Exception as e:
            self.texto.append(f"Erro abrindo arquivo de log: {e}")
            self.log_file = None

        self.thread = SerialReaderThread(porta, baud)
        self.thread.linhaRecebida.connect(self._append_text)
        self.thread.erro.connect(self._mostrar_erro)
        self.thread.start()
        self.btn_conectar.setEnabled(False)
        self.btn_desconectar.setEnabled(True)
        self.texto.append(f"Conectado em {porta} @ {baud}")

    def desconectar(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        # fecha arquivo de log
        try:
            if self.log_file:
                self.log_file.flush()
                self.log_file.close()
                self.log_file = None
                self.texto.append(f"Log salvo em: {self.log_path}")
        except Exception as e:
            self.texto.append(f"Erro fechando log: {e}")

        self.btn_conectar.setEnabled(True)
        self.btn_desconectar.setEnabled(False)
        self.texto.append("Desconectado.")

    def _append_text(self, linha):
        ts = datetime.now().strftime("%H:%M:%S")
        linha_formatada = f"[{ts}] {linha}"
        self.texto.append(linha_formatada)

        # salva automaticamente se habilitado
        if self.autosave and self.log_file:
            try:
                self.log_file.write(linha_formatada + "\n")
            except Exception as e:
                self.texto.append(f"Erro salvando log: {e}")

    def _mostrar_erro(self, msg):
        self.texto.append(f"Erro: {msg}")

    def salvar_arquivo(self):
        conteudo = self.texto.toPlainText()
        if not conteudo:
            self.texto.append("Nada para salvar.")
            return
        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(self, "Salvar dados seriais", f"serial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "Text Files (*.txt);;All Files (*)", options=options)
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                self.texto.append(f"Salvo em: {path}")
            except Exception as e:
                self.texto.append(f"Erro ao salvar: {e}")

    def escolher_arquivo(self):
        options = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(self, "Escolher arquivo de log", f"serial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "Text Files (*.txt);;All Files (*)", options=options)
        if path:
            self.log_path = path
            self.texto.append(f"Arquivo de log definido: {self.log_path}")