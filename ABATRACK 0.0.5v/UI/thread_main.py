from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ThreadPrincipal(QThread):
    ultimosSubdados = pyqtSignal(float, float)
    ultimosDadosBrutos = pyqtSignal(list)

    def __init__(self, adaptador: AdaptadorArduino):
        super().__init__()
        self.adaptadorArduino = adaptador
        self.repositorio = adaptador.repositorio
        self.flagRodando = True

    def run(self):
        while self.flagRodando:
            pacote = self.adaptadorArduino.lePacoteSerial() # pacote = "30.1:20.2", "30.2:20.1" 
            
            # Serial -> Repositorio
            if pacote:
                adicionarPacoteRepositorio(processarPacoteDeDados(pacote), self.repositorio)
                filtraSubdado(self.repositorio.dadosTemperatura, 0, self.repositorio)
                filtraSubdado(self.repositorio.tempo, 1, self.repositorio)

            # Repositorio -> Grafico
            if self.repositorio.dadosTemperatura and self.repositorio.tempo:
                self.ultimosSubdados.emit(self.repositorio.dadosTemperatura[-1], self.repositorio.tempo[-1])
                self.ultimosDadosBrutos.emit(self.repositorio.pacotesDados[-1])
            else:
                print("Repositorio vazio")
            
            time.sleep(1)
    
    def stop(self):
        self.flagRodando = False