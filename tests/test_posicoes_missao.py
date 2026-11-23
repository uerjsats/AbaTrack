import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.mensagens_orange import interpretarMensagemOrange
from aplicacao.missao_adsb import (
    CABECALHO_CSV_MISSAO,
    linhasCsvPosicoesMissao,
    registrarMensagemOrange_useCase,
    registrarPosicaoMissao_useCase,
)
from dominio.entidades import RepositorioTelemetria
from integracao.banco_adsb import BancoAdsb


class TestPosicoesMissao(unittest.TestCase):

    def test_guarda_icao_lat_lon_alt_e_estima_o_rumo(self):
        repo = RepositorioTelemetria()
        a = registrarPosicaoMissao_useCase("40621d", -22.9, -43.2, 30000, repo, chegada=100.0)
        b = registrarPosicaoMissao_useCase("40621D", -22.8, -43.2, 30000, repo, chegada=101.0)
        self.assertEqual((a.icao24, a.latitude, a.longitude, a.altitudeFt), ("40621D", -22.9, -43.2, 30000))
        self.assertIsNone(a.rumo)                       # primeira posicao: sem rumo
        self.assertAlmostEqual(b.rumo, 0.0, delta=0.5)  # foi para o norte
        self.assertTrue(b.rumoEstimado)
        self.assertEqual(len(repo.posicoesMissao), 2)

    def test_ignora_posicao_repetida(self):
        repo = RepositorioTelemetria()
        registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 30000, repo)
        self.assertIsNone(registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 30000, repo))
        self.assertEqual(len(repo.posicoesMissao), 1)

    def test_nao_duplica_o_que_ja_chegou_como_orange_ac(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(interpretarMensagemOrange(
            "ORANGE:AC,1,1000.0,40621D,-22.9,-43.2,30000,450,90", chegada=1000.5), repo)
        self.assertIsNone(registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 30000, repo))
        self.assertEqual(repo.posicoesMissao, [])
        # outra posicao da mesma aeronave, que nao veio pelo ORANGE:AC, e guardada
        self.assertIsNotNone(registrarPosicaoMissao_useCase("40621D", -22.8, -43.2, 30000, repo))

    def test_grava_na_tabela_do_banco(self):
        with tempfile.TemporaryDirectory() as pasta:
            repo, banco = RepositorioTelemetria(), BancoAdsb(pasta)
            try:
                registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 30000, repo, banco, chegada=100.0)
                registrarPosicaoMissao_useCase("40621D", -22.8, -43.2, 30100, repo, banco, chegada=101.0)
                banco.descarregar()
                con = sqlite3.connect(banco.caminho)
                linhas = con.execute("SELECT icao24, lat, lon, alt_ft, rumo_graus IS NULL, rumo_estimado "
                                     "FROM posicoes_missao ORDER BY id").fetchall()
                con.close()
                self.assertEqual(linhas, [("40621D", -22.9, -43.2, 30000, 1, 0),
                                          ("40621D", -22.8, -43.2, 30100, 0, 1)])
            finally:
                banco.fechar()

    def test_guarda_a_velocidade_enviada_na_linha(self):
        repo = RepositorioTelemetria()
        p = registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 10000, repo, velocidadeKt=450.0)
        self.assertEqual(p.velocidadeKt, 450.0)
        col = {nome: i for i, nome in enumerate(CABECALHO_CSV_MISSAO)}
        linha = linhasCsvPosicoesMissao(repo.posicoesMissao)[1]
        self.assertEqual((linha[col["velocidade_kt"]], linha[col["velocidade_kmh"]]), (450.0, 833.4))

    def test_sem_velocidade_a_coluna_fica_vazia(self):
        repo = RepositorioTelemetria()
        registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 10000, repo)
        col = {nome: i for i, nome in enumerate(CABECALHO_CSV_MISSAO)}
        self.assertEqual(linhasCsvPosicoesMissao(repo.posicoesMissao)[1][col["velocidade_kt"]], "")

    def test_csv_tem_uma_linha_por_posicao(self):
        repo = RepositorioTelemetria()
        registrarPosicaoMissao_useCase("40621D", -22.9, -43.2, 10000, repo, chegada=100.0)
        linhas = linhasCsvPosicoesMissao(repo.posicoesMissao)
        self.assertEqual(linhas[0], CABECALHO_CSV_MISSAO)
        self.assertEqual(len(linhas), 2)
        self.assertEqual(linhas[1][1:6], ("40621D", -22.9, -43.2, 10000, 3048.0))


if __name__ == "__main__":
    unittest.main()
