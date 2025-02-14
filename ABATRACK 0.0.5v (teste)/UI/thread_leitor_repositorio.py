from aplicacao.use_cases import *
from dominio.entidades import *
from aplicacao.use_cases import *
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ThreadLeituraRepositorio(QThread):
    dadoLido = pyqtSignal(list)

    def __init__(self, repositorio: RepositorioTelemetria):
        super().__init__()
        self.repositorioDados = repositorio
        self.flagRodando = True

    def run(self):
        while self.flagRodando:
            if self.repositorioDados.pacotesDados:
                dado = self.repositorioDados.pacotesDados[-1]
                if dado:
                    self.dadoLido.emit(dado)
            else:
                print("Repositorio vazio")
            time.sleep(0.5)

    def stop(self):
        self.flagRodando = False