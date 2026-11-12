
from integracao.adaptador_arduino import AdaptadorArduino
from aplicacao.use_cases import *
from dominio.entidades import *
from PyQt5.QtCore import QThread, pyqtSignal
import time
import math


class ThreadPrincipal(QThread):
    ultimosSubdadosTemperaturaTempo = pyqtSignal(float, float)
    ultimosDadosBrutos = pyqtSignal(list)
    ultimosSubdadosPressTemp = pyqtSignal(float, float)
    ultimosSubdadosAltTemp = pyqtSignal(float, float)
    ultimosSubdadosPressAlt = pyqtSignal(float, float)
    dadosdoRadio = pyqtSignal(int, int, int)
    pacoteDadosGPS = pyqtSignal(float, float, int)
    pacoteGiro = pyqtSignal(float, float, float, float)
    pacoteUmidade = pyqtSignal(float)
    pacoteAviao = pyqtSignal(str, float, float, int, float)
    # icao, lat, lon, alt, velocidade_kmh

    def __init__(self, adaptador: AdaptadorArduino):
        super().__init__()
        self.adaptadorArduino = adaptador
        self.repositorio = adaptador.repositorio
        self.flagRodando = True
        # Guarda a última posição de cada avião.
        self._ultima_posicao_aviao = {}

    def calcularDistanciaGPS(self, lat1, lon1, lat2, lon2):
        """Calcula a distância entre duas coordenadas GPS em metros."""
        raioTerra = 6371000.0
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat, dlon = lat2 - lat1, lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return raioTerra * c

    def calcularVelocidadeAviao(self, icao, lat, lon):
        """Calcula a velocidade do avião em km/h usando posições sucessivas."""
        agora = time.monotonic()
        ultima = self._ultima_posicao_aviao.get(icao)

        # Primeira posição recebida: ainda não existe distância para calcular.
        self._ultima_posicao_aviao[icao] = (lat, lon, agora)
        if ultima is None:
            return 0.0

        latAnterior, lonAnterior, tempoAnterior = ultima
        intervalo = agora - tempoAnterior
        if intervalo <= 0:
            return 0.0

        distancia = self.calcularDistanciaGPS(
            latAnterior, lonAnterior, lat, lon
        )
        return (distancia / intervalo) * 3.6

    def _tentaProcessarAviao(self, pacote) -> bool:
        """Retorna True se o pacote era uma linha 'missão:' (válida ou não)."""
        if isinstance(pacote, bytes):
            pacote = pacote.decode('utf-8', errors='ignore')
        if not isinstance(pacote, str):
            return False

        texto = pacote.strip()
        if not texto.lower().startswith(('missão:', 'missao:')):
            return False

        try:
            d = [x.strip() for x in texto.split(':', 1)[1].split(',')]
            icao = d[0].upper()
            lat, lon = float(d[1]), float(d[2])
            alt = int(float(d[3]))

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Coordenadas GPS inválidas")

            velocidade = self.calcularVelocidadeAviao(icao, lat, lon)
            self.pacoteAviao.emit(icao, lat, lon, alt, velocidade)

        except (IndexError, ValueError) as e:
            print(f"Linha missão inválida: {texto}. Erro: {e}")
        return True

    def run(self):
        while self.flagRodando:
            try:
                pacote = self.adaptadorArduino.lePacoteSerial()
                novoPacote = False

                # Linha de missão (ADS-B): não passa pelo fluxo normal de telemetria
                if pacote and self._tentaProcessarAviao(pacote):
                    self.msleep(10)
                    continue

                # Serial -> Repositorio
                if pacote:
                    try:
                        dados_processados = processarPacoteDeDados(pacote)
                        adicionarPacoteRepositorio(dados_processados, self.repositorio)
                        distribuirPacoteNosSubdados(self.repositorio)
                        novoPacote = True
                        print(dados_processados)

                    except (ValueError, IndexError) as e:
                        print(f"Erro ao processar pacote: {pacote}. Erro: {e}")
                        continue  # Ignora o pacote inválido e continua o loop

                # Repositorio -> UI (so quando chegou pacote novo, para nao repetir pontos nos graficos)
                if novoPacote:
                    self.ultimosSubdadosTemperaturaTempo.emit(
                        self.repositorio.tempo[-1],
                        self.repositorio.dadosTemperatura[-1]
                    )
                    self.ultimosDadosBrutos.emit(self.repositorio.pacotesDados[-1])
                    self.ultimosSubdadosPressTemp.emit(
                        self.repositorio.tempo[-1],
                        self.repositorio.pressao[-1]
                    )
                    self.ultimosSubdadosAltTemp.emit(
                        self.repositorio.tempo[-1],
                        self.repositorio.altitude[-1]
                    )
                    self.ultimosSubdadosPressAlt.emit(
                        self.repositorio.pressao1[-1],
                        self.repositorio.altitude1[-1]
                    )
                    self.dadosdoRadio.emit(
                        int(self.repositorio.numerodepacotes[-1]),
                        int(self.repositorio.RSSI[-1]),
                        int(self.repositorio.tamanhopacote[-1])
                    )
                    self.pacoteDadosGPS.emit(
                        self.repositorio.latitude[-1],
                        self.repositorio.longitude[-1],
                        int(self.repositorio.sats[-1])
                    )
                    self.pacoteGiro.emit(
                        self.repositorio.roll[-1],
                        self.repositorio.pitch[-1],
                        self.repositorio.yaw[-1],
                        self.repositorio.anguloldr[-1]
                    )
                    self.pacoteUmidade.emit(self.repositorio.umidade[-1])

                self.msleep(10)

            except Exception as e:
                print(f"Erro inesperado: {e}")
                self.msleep(10)  # Evita travar o loop

    def stop(self):
        self.flagRodando = False
