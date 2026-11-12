import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QCoreApplication

from aplicacao.deteccao_aeronave import (
    JANELA_ASSOCIACAO_S,
    ehLinhaDeteccao,
    interpretarLinhaDeteccao,
    registrarDeteccao_useCase,
)
from aplicacao.use_cases import registrarImagem_useCase
from dominio.entidades import RepositorioTelemetria
from UI.thread_main import ThreadPrincipal

app = QCoreApplication.instance() or QCoreApplication(sys.argv)

DET_3 = "DET,3,-22.8800,-43.3000"
DET_4 = "DET,4,-22.9068,-43.1729"
TELEMETRIA = ("12:25.5:40:100.0:101325:-22.9:-43.1:7:1.0:2.0:3.0:45.0:"
              "30:31:7.4:1.2:5:-90:120")


def nada(dados, pasta, horario):
    return None


class TestInterpretarLinha(unittest.TestCase):

    def test_le_foto_e_coordenadas(self):
        d = interpretarLinhaDeteccao(DET_3)
        self.assertEqual(d.indiceFoto, 3)
        self.assertEqual((d.latitude, d.longitude), (-22.88, -43.3))
        self.assertIsNone(d.imagem)

    def test_tolera_espacos_minusculas_e_campos_extras(self):
        d = interpretarLinhaDeteccao("det, 4 , -22.9 , -43.1 , extra, outro \r")
        self.assertEqual((d.indiceFoto, d.latitude, d.longitude), (4, -22.9, -43.1))

    def test_linhas_invalidas(self):
        invalidas = [
            "DET,4,-22.9",             # incompleta
            "DET,x,-22.9,-43.1",       # foto nao numerica
            "DET,-1,-22.9,-43.1",      # foto negativa
            "DET,4,95,-43.1",          # latitude fora do intervalo
            "DET,4,-22.9,200",         # longitude fora do intervalo
            "DET,4,abc,-43.1",         # lat nao numerica
        ]
        for linha in invalidas:
            with self.assertRaises(ValueError, msg=linha):
                interpretarLinhaDeteccao(linha)

    def test_so_reconhece_o_prefixo_det(self):
        self.assertTrue(ehLinhaDeteccao(DET_4))
        self.assertFalse(ehLinhaDeteccao(TELEMETRIA))
        self.assertFalse(ehLinhaDeteccao("DETALHE:1:2"))
        self.assertFalse(ehLinhaDeteccao("2:QRES,NONE"))


class TestAssociacao(unittest.TestCase):

    def novo(self):
        return RepositorioTelemetria()

    def test_deteccao_antes_da_foto(self):
        repo = self.novo()
        det = interpretarLinhaDeteccao(DET_4)
        self.assertEqual(registrarDeteccao_useCase(det, repo), [])
        img = registrarImagem_useCase(b"x", repo, "p", nada)
        self.assertIs(img.deteccao, det)
        self.assertIs(det.imagem, img)

    def test_foto_antes_da_deteccao(self):
        repo = self.novo()
        img = registrarImagem_useCase(b"x", repo, "p", nada)
        self.assertIsNone(img.deteccao)
        det = interpretarLinhaDeteccao(DET_4)
        pares = registrarDeteccao_useCase(det, repo)
        self.assertEqual(pares, [(det, img)])

    def test_cada_foto_casa_com_uma_deteccao_em_ordem(self):
        repo = self.novo()
        d1 = interpretarLinhaDeteccao(DET_4)
        d2 = interpretarLinhaDeteccao(DET_3)
        registrarDeteccao_useCase(d1, repo)
        registrarDeteccao_useCase(d2, repo)
        i1 = registrarImagem_useCase(b"a", repo, "p", nada)
        i2 = registrarImagem_useCase(b"b", repo, "p", nada)
        self.assertIs(i1.deteccao, d1)
        self.assertIs(i2.deteccao, d2)

    def test_fora_da_janela_de_tempo_nao_casa(self):
        repo = self.novo()
        img = registrarImagem_useCase(b"x", repo, "p", nada)
        det = interpretarLinhaDeteccao(
            DET_4,
            horario=img.horario + timedelta(seconds=JANELA_ASSOCIACAO_S + 5))
        self.assertEqual(registrarDeteccao_useCase(det, repo), [])
        self.assertIsNone(img.deteccao)
        self.assertIsNone(det.imagem)


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


class TestThreadRoteiaDeteccao(unittest.TestCase):

    def test_linha_det_vai_para_o_sinal_e_nao_vira_telemetria(self):
        repo = RepositorioTelemetria()
        adaptador = AdaptadorFalso(
            repo, [TELEMETRIA, DET_3, "DET,9,lixo,1", DET_4])
        thread = ThreadPrincipal(adaptador)
        adaptador.thread = thread
        deteccoes, pontos = [], []
        thread.deteccaoRecebida.connect(deteccoes.append)
        thread.ultimosSubdadosTemperaturaTempo.connect(lambda x, y: pontos.append(x))
        thread.run()
        self.assertEqual([d.indiceFoto for d in deteccoes], [3, 4])
        self.assertEqual(len(pontos), 1)
        self.assertEqual(len(repo.pacotesDados), 1)


if __name__ == "__main__":
    unittest.main()
