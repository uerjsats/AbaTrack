from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt5.QtCore import QThread, pyqtSignal
import time

class ThreadPrincipal(QThread):
    ultimosSubdadosTemperaturaTempo = pyqtSignal(float, float)
    ultimosDadosBrutos = pyqtSignal(list)
    ultimosSubdadosPressTemp = pyqtSignal(float, float)
    ultimosSubdadosAltTemp = pyqtSignal(float, float)
    ultimosSubdadosPressAlt = pyqtSignal(float, float)
    dadosdoRadio = pyqtSignal(int, int, int)
    pacoteDadosGPS = pyqtSignal(float,float,int)
    pacoteGiro = pyqtSignal(float,float,float)
    pacoteUmidade = pyqtSignal(float)   

    def __init__(self, adaptador: AdaptadorArduino):
        super().__init__()
        self.adaptadorArduino = adaptador
        self.repositorio = adaptador.repositorio
        self.flagRodando = True

    def run(self):
        while self.flagRodando:
            try:
                pacote = self.adaptadorArduino.lePacoteSerial()  # pacote = "30.1:20.2", "30.2:20.1"
                
                # Serial -> Repositorio
                if pacote:
                    try:
                        dados_processados = processarPacoteDeDados(pacote)
                        adicionarPacoteRepositorio(dados_processados, self.repositorio)

                        # Filtra subdados com segurança
                        filtraSubdado(self.repositorio.dadosTemperatura, 1, self.repositorio)
                        filtraSubdado(self.repositorio.tempo, 0, self.repositorio)
                        filtraSubdado(self.repositorio.tempo1, 0, self.repositorio)
                        filtraSubdado(self.repositorio.umidade, 2, self.repositorio)
                        filtraSubdado(self.repositorio.pressao, 4, self.repositorio)
                        filtraSubdado(self.repositorio.pressao1, 4, self.repositorio)
                        filtraSubdado(self.repositorio.altitude, 3, self.repositorio)
                        filtraSubdado(self.repositorio.altitude1, 3, self.repositorio)
                        filtraSubdado(self.repositorio.latitude, 5, self.repositorio)
                        filtraSubdado(self.repositorio.longitude, 6, self.repositorio)
                        filtraSubdado(self.repositorio.sats, 7, self.repositorio)
                        filtraSubdado(self.repositorio.roll, 8, self.repositorio)
                        filtraSubdado(self.repositorio.pitch, 9, self.repositorio)
                        filtraSubdado(self.repositorio.yaw, 10, self.repositorio)
                        filtraSubdado(self.repositorio.numerodepacotes, 11, self.repositorio)
                        filtraSubdado(self.repositorio.RSSI, 12, self.repositorio)
                        filtraSubdado(self.repositorio.tamanhopacote, 13, self.repositorio)

                        print(self.repositorio.pacotesDados)
                        print(self.repositorio.dadosTemperatura)
                        print(self.repositorio.tempo)
                        print(self.repositorio.pressao)
                        print(self.repositorio.altitude)

                    except (ValueError, IndexError) as e:
                        print(f"Erro ao processar pacote: {pacote}. Erro: {e}")
                        continue  # Ignora o pacote inválido e continua o loop

                # Repositorio -> UI
                if (self.repositorio.dadosTemperatura and self.repositorio.tempo and self.repositorio.altitude
                and self.repositorio.numerodepacotes and self.repositorio.pressao and self.repositorio.tamanhopacote
                and self.repositorio.RSSI and self.repositorio.latitude and self.repositorio.longitude and self.repositorio.sats
                and self.repositorio.roll and self.repositorio.pitch and self.repositorio.yaw and self.repositorio.umidade):

                    self.ultimosSubdadosTemperaturaTempo.emit(self.repositorio.tempo[-1], self.repositorio.dadosTemperatura[-1])
                    self.ultimosDadosBrutos.emit(self.repositorio.pacotesDados[-1])
                    self.ultimosSubdadosPressTemp.emit(self.repositorio.tempo[-1], self.repositorio.pressao[-1])
                    self.ultimosSubdadosAltTemp.emit(self.repositorio.tempo[-1], self.repositorio.altitude[-1])
                    self.ultimosSubdadosPressAlt.emit(self.repositorio.pressao1[-1], self.repositorio.altitude1[-1])
                    self.dadosdoRadio.emit(
                        int(self.repositorio.numerodepacotes[-1]), 
                        int(self.repositorio.RSSI[-1]), 
                        int(self.repositorio.tamanhopacote[-1])
                    )
                    self.pacoteDadosGPS.emit(self.repositorio.latitude[-1], self.repositorio.longitude[-1], int(self.repositorio.sats[-1]))
                    self.pacoteGiro.emit(self.repositorio.roll[-1], self.repositorio.pitch[-1], self.repositorio.yaw[-1])
                    self.pacoteUmidade.emit(self.repositorio.umidade[-1])
        
                else:
                    print("Repositorio vazio")
                
                self.msleep(1000)

            except Exception as e:
                print(f"Erro inesperado: {e}")
                self.msleep(1000)  # Evita travar o loop
    
    def stop(self):
        self.flagRodando = False