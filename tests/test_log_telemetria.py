import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dominio.entidades import CAMPOS_PACOTE
from integracao.log_telemetria import CABECALHO, LogTelemetria, esquemaMarkdown


def pacote(tempo, bat1=30.0, bat2=31.0):
    return [tempo, 25.5, 40.0, 100.0, 101325.0, -22.9, -43.1, 7.0, 1.0, 2.0, 3.0,
            45.0, bat1, bat2, 7.4, 1.2, tempo, -30.0, 41.0]


def ler(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


class TestLogTelemetria(unittest.TestCase):

    def test_cabecalho_tem_hora_os_19_campos_e_a_media(self):
        self.assertEqual(len(CABECALHO), 1 + len(CAMPOS_PACOTE) + 1)
        self.assertEqual(CABECALHO[0], "chegada_pc")
        self.assertEqual(CABECALHO[-1], "temp_bateria_media")

    def test_grava_cada_pacote_antes_de_fechar(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = LogTelemetria(pasta)
            try:
                for t in (1.0, 2.0, 3.0):
                    log.registrar(pacote(t), chegada=1000.0 + t)
                log.descarregar()
                linhas = ler(log.caminho)          # lido com o log ainda aberto
                self.assertEqual(len(linhas), 4)   # cabecalho + 3 pacotes
                col = {nome: i for i, nome in enumerate(linhas[0])}
                self.assertEqual([l[col["tempo"]] for l in linhas[1:]], ["1.0", "2.0", "3.0"])
                self.assertEqual(linhas[1][col["tensao"]], "7.4")
                self.assertEqual(linhas[1][col["temp_bateria_media"]], "30.5")
            finally:
                log.fechar()

    def test_media_da_bateria_descarta_o_sensor_com_menos_127(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = LogTelemetria(pasta)
            try:
                log.registrar(pacote(1.0, bat1=-127.0, bat2=18.5))
                log.registrar(pacote(2.0, bat1=-127.0, bat2=-127.0))
                log.descarregar()
                linhas = ler(log.caminho)
                col = {nome: i for i, nome in enumerate(linhas[0])}
                self.assertEqual(linhas[1][col["temp_bateria_media"]], "18.5")
                self.assertEqual(linhas[2][col["temp_bateria_media"]], "")     # os dois falharam
                self.assertEqual(linhas[2][col["temp_bateria1"]], "-127.0")    # o dado cru fica
            finally:
                log.fechar()

    def test_pacote_curto_e_completado_e_um_pacote_ruim_nao_derruba_o_log(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = LogTelemetria(pasta)
            try:
                log.registrar([1.0, 2.0])                      # curto
                log.registrar(pacote(3.0))
                log.descarregar()
                linhas = ler(log.caminho)
                self.assertEqual(len(linhas), 3)
                self.assertEqual(len(linhas[1]), len(CABECALHO))
                self.assertEqual(log.erros, 0)
            finally:
                log.fechar()

    def test_escreve_o_esquema_ao_lado(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = LogTelemetria(pasta)
            log.fechar()
            texto = open(os.path.join(pasta, "ESQUEMA_telemetria.md"), encoding="utf-8").read()
            self.assertEqual(texto, esquemaMarkdown())
            for c in CAMPOS_PACOTE:
                self.assertIn(c.chave, texto)


if __name__ == "__main__":
    unittest.main()
