import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.mensagens_orange import interpretarMensagemOrange, lerMensagemOrange
from aplicacao.missao_adsb import registrarMensagemOrange_useCase
from dominio.entidades import RepositorioTelemetria
from integracao.banco_adsb import TABELAS, BancoAdsb, esquemaMarkdown

LINHAS = [
    "ORANGE:EVT,BOOT",
    "ORANGE:ACK,START,2",
    "ORANGE:AC,1,1000.100,40621D,-22.9,-43.2,38000,450,90",
    "ORANGE:AC,2,1000.600,40621D,-22.9,-43.19,38000,450",
    "ORANGE:AC,2,1000.600,40621D,-22.9,-43.19,38000,450",        # repetida (DUMP)
    "ORANGE:STATUS,RUNNING,0,3,48.2,180,180,20,60,0.7,1.0,3,1,40,50,60,1",
    "ORANGE:OPSTATE,EXECUTANDO,1,0,120,3,500,2",
    "ORANGE:VEREDITO,CLANDESTINA,-22.9068,-43.1729",
    "ORANGE:NAK,START,JA_EM_EXECUCAO",
    "ORANGE:AC,lixo",
]


class TestBancoAdsb(unittest.TestCase):

    def gravar(self, pasta, linhas=LINHAS):
        repo = RepositorioTelemetria()
        banco = BancoAdsb(pasta)
        for i, linha in enumerate(linhas):
            registrarMensagemOrange_useCase(lerMensagemOrange(linha, chegada=2000.0 + i), repo, banco)
        banco.descarregar()
        return repo, banco

    def consulta(self, banco, sql, *args):
        con = sqlite3.connect(banco.caminho)
        try:
            return con.execute(sql, args).fetchall()
        finally:
            con.close()

    def test_grava_cada_tipo_na_sua_tabela(self):
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta)
            try:
                n = lambda t: self.consulta(banco, f"SELECT COUNT(*) FROM {t}")[0][0]
                self.assertEqual(n("aeronaves"), 2)          # a repetida foi ignorada
                self.assertEqual(n("status_orange"), 1)
                self.assertEqual(n("opstate"), 1)
                self.assertEqual(n("eventos"), 1)
                self.assertEqual(n("confirmacoes"), 2)
                self.assertEqual(n("vereditos"), 1)
                self.assertEqual(n("log_cru"), len(LINHAS))
            finally:
                banco.fechar()

    def test_registro_de_aeronave_completo(self):
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta)
            try:
                l1, l2 = self.consulta(
                    banco, "SELECT sessao, seq, ts, chegada, icao24, lat, lon, alt_ft, gs_kt, "
                           "rumo_graus, rumo_estimado FROM aeronaves ORDER BY seq")
                self.assertEqual(l1[:5], (2, 1, 1000.1, 2002.0, "40621D"))
                self.assertEqual((l1[9], l1[10]), (90.0, 0))            # rumo do ADS-B
                self.assertEqual(l2[10], 1)                              # rumo estimado
                self.assertAlmostEqual(l2[9], 90, delta=0.5)
            finally:
                banco.fechar()

    def test_status_com_campos_opcionais_e_vereditos(self):
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta)
            try:
                st = self.consulta(banco, "SELECT estado, aeronaves, lat_max_ms, descartados_fila, "
                                          "msgs_pos, relogio_ok FROM status_orange")[0]
                self.assertEqual(st, ("RUNNING", 20, 1.0, 3, 50, 1))
                v = self.consulta(banco, "SELECT lat, lon, foto FROM vereditos ORDER BY id")
                self.assertEqual(v, [(-22.9068, -43.1729, None)])
            finally:
                banco.fechar()

    def test_log_cru_guarda_tudo_inclusive_o_que_nao_deu_para_ler(self):
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta)
            try:
                linhas = self.consulta(banco, "SELECT linha, valida FROM log_cru ORDER BY id")
                self.assertEqual([l[0] for l in linhas], LINHAS)
                self.assertEqual([l[1] for l in linhas].count(0), 1)
                self.assertEqual(linhas[-1], ("ORANGE:AC,lixo", 0))
            finally:
                banco.fechar()

    def test_esquema_documentado_e_igual_ao_do_banco(self):
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta, LINHAS[:1])
            try:
                with open(os.path.join(pasta, "ESQUEMA_adsb.md"), encoding="utf-8") as f:
                    doc = f.read()
                self.assertEqual(doc, esquemaMarkdown())
                for tabela, colunas in TABELAS.items():
                    reais = [c[1] for c in self.consulta(banco, f"PRAGMA table_info({tabela})")]
                    self.assertEqual(reais, [c[0] for c in colunas], tabela)
                    self.assertIn(f"## {tabela}", doc)
                meta = dict(self.consulta(banco, "SELECT chave, valor FROM meta"))
                self.assertEqual(meta["software"], "AbaTrack")
            finally:
                banco.fechar()

    def test_arquivo_db_sozinho_ja_tem_os_dados_durante_a_missao(self):
        import shutil
        with tempfile.TemporaryDirectory() as pasta:
            _, banco = self.gravar(pasta)
            try:
                copia = os.path.join(pasta, "copia.db")
                shutil.copyfile(banco.caminho, copia)      # so o .db, sem o -wal
                con = sqlite3.connect(copia)
                try:
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM aeronaves").fetchone()[0], 2)
                    self.assertEqual(con.execute("SELECT COUNT(*) FROM log_cru").fetchone()[0], len(LINHAS))
                finally:
                    con.close()
            finally:
                banco.fechar()

    def test_fechar_grava_o_que_faltava(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = BancoAdsb(pasta)
            for i in range(1, 501):
                banco.registrar(interpretarMensagemOrange(
                    f"ORANGE:AC,{i},1000.0,40621D,-22.9,-43.2,38000,450", 2000.0), 1)
            banco.fechar()
            con = sqlite3.connect(banco.caminho)
            try:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM aeronaves").fetchone()[0], 500)
            finally:
                con.close()

    def test_erro_numa_mensagem_nao_derruba_a_gravacao(self):
        class Quebrada:
            tipo, dados, bruta, chegada = "AC", None, "ORANGE:AC,quebrada", 1.0

        with tempfile.TemporaryDirectory() as pasta:
            banco = BancoAdsb(pasta)
            try:
                banco.registrar(Quebrada(), 0)
                banco.registrar(interpretarMensagemOrange("ORANGE:EVT,BOOT"), 0)
                banco.descarregar()
                self.assertEqual(banco.erros, 1)
                self.assertEqual(self.consulta(banco, "SELECT COUNT(*) FROM eventos")[0][0], 1)
            finally:
                banco.fechar()


if __name__ == "__main__":
    unittest.main()
