from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt6.QtCore import QThread, pyqtSignal
import time

# Thread para ler a serial e armazenar dados no repositório
class ThreadLeituraSerial(QThread):
    def __init__(self, adaptador: AdaptadorArduino):
        super().__init__()
        self.adaptadorArduino = adaptador
        self.flagRodando = True

    def run(self):
        while self.flagRodando:
            pacote = self.adaptadorArduino.lePacoteSerial()
            if pacote:
                adicionarPacoteRepositorio(pacote, self.adaptadorArduino.repositorio)
            time.sleep(0.5)

    def stop(self):
        self.flagRodando = False