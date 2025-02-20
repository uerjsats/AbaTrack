from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ThreadPrincipal(QThread):
    ultimosSubdadosTemperaturaTempo = pyqtSignal(float, float)
    ultimosDadosBrutos = pyqtSignal(list)
    ultimosSubdadosPressTemp = pyqtSignal(float, float)
    ultimosSubdadosAltTemp = pyqtSignal(float, float)
    dadosdoRadio = pyqtSignal(float, float, float)
    pacoteDadosGPS = pyqtSignal(float,float,float)
    pacoteGiro = pyqtSignal(float,float,float)

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
                filtraSubdado(self.repositorio.tempo1, 1, self.repositorio)
                filtraSubdado(self.repositorio.pressao, 2, self.repositorio)
                filtraSubdado(self.repositorio.altitude, 3, self.repositorio)
                filtraSubdado(self.repositorio.numerodepacotes, 4, self.repositorio)
                filtraSubdado(self.repositorio.RSSI, 5, self.repositorio)
                filtraSubdado(self.repositorio.tamanhopacote, 6, self.repositorio)
                filtraSubdado(self.repositorio.latitude, 7, self.repositorio)
                filtraSubdado(self.repositorio.longitude, 8, self.repositorio)
                filtraSubdado(self.repositorio.sats, 9, self.repositorio)
                filtraSubdado(self.repositorio.gyrox, 10, self.repositorio)
                filtraSubdado(self.repositorio.gyroy, 11, self.repositorio)
                filtraSubdado(self.repositorio.gyroz, 12, self.repositorio)        

                print(self.repositorio.pacotesDados)
                print(self.repositorio.dadosTemperatura)
                print(self.repositorio.tempo)
                print(self.repositorio.pressao)
                print(self.repositorio.altitude)


            # Repositorio -> UI
            if (self.repositorio.dadosTemperatura and self.repositorio.tempo and self.repositorio.altitude
            and self.repositorio.numerodepacotes and self.repositorio.pressao and self.repositorio.tamanhopacote
            and self.repositorio.RSSI and self.repositorio.latitude and self.repositorio.longitude and self.repositorio.sats
            and self.repositorio.gyrox and self.repositorio.gyroy and self.repositorio.gyroz):

                self.ultimosSubdadosTemperaturaTempo.emit(self.repositorio.tempo[-1], self.repositorio.dadosTemperatura[-1])
                self.ultimosDadosBrutos.emit(self.repositorio.pacotesDados[-1])
                self.ultimosSubdadosPressTemp.emit(self.repositorio.tempo[-1], self.repositorio.pressao[-1])
                self.ultimosSubdadosAltTemp.emit(self.repositorio.tempo[-1], self.repositorio.altitude[-1])
                self.dadosdoRadio.emit(self.repositorio.numerodepacotes[-1], self.repositorio.RSSI[-1], self.repositorio.tamanhopacote[-1])
                self.pacoteDadosGPS.emit(self.repositorio.latitude[-1], self.repositorio.longitude[-1], self.repositorio.sats[-1])
                self.pacoteGiro.emit(self.repositorio.gyrox[-1], self.repositorio.gyroy[-1], self.repositorio.gyroz[-1])
    
            else:
                print("Repositorio vazio")
            
            self.msleep(1000)
    
    def stop(self):
        self.flagRodando = False