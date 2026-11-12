import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QCoreApplication

from dominio.entidades import RepositorioTelemetria
from UI.thread_main import ThreadPrincipal

app = QCoreApplication.instance() or QCoreApplication(sys.argv)

TELEMETRIA = ("12:25.5:40:100.0:101325:-22.9:-43.1:7:1.0:2.0:3.0:45.0:"
              "30:31:7.4:1.2:5:-90:120")


class AdaptadorFalso:
    def __init__(self, repositorio, linhas):
        self.repositorio = repositorio
        self.linhas = list(linhas)
        self.thread = None

    def lePacoteSerial(self):
        if not self.linhas:
            self.thread.flagRodando = False
            return None
        return self.linhas.pop(0)


class TestThreadRoteiaOrange(unittest.TestCase):

    def rodar(self, linhas):
        repo = RepositorioTelemetria()
        adaptador = AdaptadorFalso(repo, linhas)
        thread = ThreadPrincipal(adaptador)
        adaptador.thread = thread
        mensagens, deteccoes, pontos = [], [], []
        thread.mensagemOrange.connect(mensagens.append)
        thread.deteccaoRecebida.connect(deteccoes.append)
        thread.ultimosSubdadosTemperaturaTempo.connect(lambda x, y: pontos.append(x))
        thread.run()
        return repo, mensagens, deteccoes, pontos

    def test_linhas_orange_vao_para_o_sinal_e_nao_viram_telemetria(self):
        repo, mensagens, _, pontos = self.rodar([
            "ORANGE:AC,17,1790950771.056,40621D,52.26578,3.93891,38000,450,254",
            TELEMETRIA,
            "ORANGE:VEREDITO,CLANDESTINA,-22.9068,-43.1729",
            "ORANGE:STATUS,RUNNING,0,3,48.2,180,180,20,60,0.7,1.0",
            "ORANGE:AC,lixo",
        ])
        self.assertEqual([m.tipo for m in mensagens], ["AC", "VEREDITO", "STATUS", "INVALIDA"])
        self.assertEqual(mensagens[0].dados.rumo, 254.0)
        self.assertEqual(len(pontos), 1)
        self.assertEqual(len(repo.pacotesDados), 1)

    def test_mensagem_orange_nao_emite_para_os_graficos(self):
        _, mensagens, _, pontos = self.rodar(["ORANGE:EVT,BOOT"])
        self.assertEqual(len(mensagens), 1)
        self.assertEqual(pontos, [])

    def test_det_antigo_continua_funcionando(self):
        _, mensagens, deteccoes, _ = self.rodar(["DET,4,-22.9068,-43.1729"])
        self.assertEqual(mensagens, [])
        self.assertEqual(len(deteccoes), 1)

    def test_chegam_todas_mesmo_com_rajada(self):
        linhas = [f"ORANGE:AC,{i},1000.0,40621D,-22.9,-43.2,38000,450" for i in range(1, 201)]
        _, mensagens, _, _ = self.rodar(linhas)
        self.assertEqual(len(mensagens), 200)


if __name__ == "__main__":
    unittest.main()
