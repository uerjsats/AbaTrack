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
        self.repositorio = self.adaptadorArduino.repositorio
        self.flagRodando = True

    def run(self):
        while self.flagRodando:
            pacote = self.adaptadorArduino.lePacoteSerial() # pacote = "30.1:20.2", "30.2:20.1"
            if pacote:
                # Adiciona pacote de dados processado -> repositorio.pacoteDados = [[30.1, 20.2], [30.2, 20.1]]
                adicionarPacoteRepositorio(processarPacoteDeDados(pacote), self.repositorio)

                # filtra subdado Temperatura -> repositorio.dadosTemperatura = [30.1, 30.2]
                filtraSubdado(self.repositorio.dadosTemperatura, 0, self.repositorio)

                # filtra subdado Tempo -> repositorio.tempo = [20.2, 20.1]
                filtraSubdado(self.repositorio.tempo, 1, self.repositorio)

                print(self.repositorio.pacotesDados)
                print(self.repositorio.dadosTemperatura)
                print(self.repositorio.tempo)

            time.sleep(0.5)

    def stop(self):
        self.flagRodando = False