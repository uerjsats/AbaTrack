import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.mensagens_orange import interpretarMensagemOrange
from aplicacao.missao_adsb import CABECALHO_CSV_ADSB, linhasCsvAdsb, registrarMensagemOrange_useCase
from dominio.entidades import RepositorioTelemetria


def enviar(repo, linha, chegada):
    registrarMensagemOrange_useCase(interpretarMensagemOrange(linha, chegada=chegada), repo)


class TestCsvAdsb(unittest.TestCase):

    def test_sem_dados_so_tem_cabecalho(self):
        self.assertEqual(linhasCsvAdsb([]), [CABECALHO_CSV_ADSB])

    def test_uma_linha_por_registro_com_unidades_e_origem_do_rumo(self):
        repo = RepositorioTelemetria()
        enviar(repo, "ORANGE:AC,1,1000.0,40621D,-22.9,-43.2,10000,100,90", 1000.5)
        enviar(repo, "ORANGE:AC,2,1001.0,40621D,-22.9,-43.19,10000,100", 1001.5)
        enviar(repo, "ORANGE:AC,3,1002.0,7788FF,-22.8,-43.1,5000,200", 1002.5)
        linhas = linhasCsvAdsb(repo.registrosAdsb)
        self.assertEqual(len(linhas), 4)
        self.assertTrue(all(len(l) == len(CABECALHO_CSV_ADSB) for l in linhas))
        col = {nome: i for i, nome in enumerate(CABECALHO_CSV_ADSB)}
        a, b, c = linhas[1:]
        self.assertEqual((a[col["altitude_m"]], a[col["velocidade_kmh"]]), (3048.0, 185.2))
        self.assertEqual((a[col["rumo_graus"]], a[col["rumo_origem"]]), (90.0, "adsb"))
        self.assertEqual(b[col["rumo_origem"]], "estimado")
        self.assertEqual((c[col["rumo_graus"]], c[col["rumo_origem"]]), ("", ""))   # 1o ponto, sem rumo
        self.assertEqual(a[col["latencia_s"]], 0.5)


if __name__ == "__main__":
    unittest.main()
