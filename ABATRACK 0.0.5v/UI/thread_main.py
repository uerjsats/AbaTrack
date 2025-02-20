from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ThreadPrincipal(QThread):
    ultimosSubdados = pyqtSignal(float, float)
    ultimosDadosBrutos = pyqtSignal(list)
    ultimosSubdadosAltitude = pyqtSignal(float, float)
    ultimosSubdadosAltTemp = pyqtSignal(float, float)
    dadosdoRadio = pyqtSignal(float,float,float)

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
                filtraSubdado(self.repositorio.pressao, 2, self.repositorio)
                filtraSubdado(self.repositorio.altitude, 3, self.repositorio)
                filtraSubdado(self.repositorio.numerodepacotes, 4, self.repositorio)
                filtraSubdado(self.repositorio.RSSI, 5, self.repositorio)
                filtraSubdado(self.repositorio.tamanhopacote, 6, self.repositorio)

            # Repositorio -> UI
            if self.repositorio.dadosTemperatura and self.repositorio.tempo:

                self.ultimosSubdados.emit(self.repositorio.dadosTemperatura[-1], self.repositorio.tempo[-1])
                self.ultimosDadosBrutos.emit(self.repositorio.pacotesDados[-1])
                self.ultimosSubdadosAltitude.emit(self.repositorio.altitude[-1],self.repositorio.pressao[-1])
                self.ultimosSubdadosAltTemp.emit(self.repositorio.altitude[-1],self.repositorio.dadosTemperatura[-1])
                self.dadosdoRadio.emit(self.repositorio.numerodepacotes[-1], self.repositorio.RSSI[-1], self.repositorio.tamanhopacote[-1])
    
            else:
                print("Repositorio vazio")
            
            time.sleep(1)
    
    def stop(self):
        self.flagRodando = False