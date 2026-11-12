import glob
import os
import re
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from PyQt5.QtCore import QCoreApplication

from aplicacao.use_cases import (
    adicionarPacoteRepositorio,
    distribuirPacoteNosSubdados,
    processarPacoteDeDados,
    salvarDadosTXT,
)
from dominio.entidades import CAMPOS_PACOTE, INDICE_CAMPO, RepositorioTelemetria
from UI.thread_main import ThreadPrincipal

app = QCoreApplication.instance() or QCoreApplication(sys.argv)

PACOTE = ("12:25.5:40:100.0:101325:-22.9:-43.1:7:1.0:2.0:3.0:45.0:"
          "30:31:7.4:1.2:5:-90:120")


class TestEsquema(unittest.TestCase):

    def test_readme_segue_a_ordem_do_esquema(self):
        """A tabela 'Dados Recebidos' do README tem que bater com CAMPOS_PACOTE."""
        with open(os.path.join(RAIZ, "README.md"), encoding="utf-8") as f:
            texto = f.read()
        linhas = re.findall(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|", texto, re.MULTILINE)
        self.assertEqual(
            [(int(i), nome) for i, nome in linhas],
            [(i, campo.nome) for i, campo in enumerate(CAMPOS_PACOTE)],
        )

    def test_toda_lista_do_esquema_existe_no_repositorio(self):
        repo = RepositorioTelemetria()
        for campo in CAMPOS_PACOTE:
            for lista in campo.listas:
                self.assertIsInstance(getattr(repo, lista), list, lista)

    def test_chaves_unicas_e_indices_coerentes(self):
        self.assertEqual(len(INDICE_CAMPO), len(CAMPOS_PACOTE))
        self.assertEqual(INDICE_CAMPO["angulo_ldr"], 11)
        self.assertEqual(INDICE_CAMPO["tamanho_pacote"], len(CAMPOS_PACOTE) - 1)

    def test_distribui_cada_campo_na_lista_certa(self):
        repo = RepositorioTelemetria()
        adicionarPacoteRepositorio(processarPacoteDeDados(PACOTE), repo)
        distribuirPacoteNosSubdados(repo)
        self.assertEqual(repo.tempo, [12.0])
        self.assertEqual(repo.tempo1, [12.0])
        self.assertEqual(repo.altitude, [100.0])
        self.assertEqual(repo.pressao1, [101325.0])
        self.assertEqual(repo.anguloldr, [45.0])
        self.assertEqual(repo.tempbateria1, [30.0])
        self.assertEqual(repo.RSSI, [-90.0])
        self.assertEqual(repo.tamanhopacote, [120.0])

    def test_pacote_curto_e_completado_sem_desalinhar_listas(self):
        repo = RepositorioTelemetria()
        adicionarPacoteRepositorio(processarPacoteDeDados("1:2:3"), repo)
        distribuirPacoteNosSubdados(repo)
        comprimentos = {len(getattr(repo, l)) for c in CAMPOS_PACOTE for l in c.listas}
        self.assertEqual(comprimentos, {1})

    def test_txt_mantem_o_formato(self):
        repo = RepositorioTelemetria()
        adicionarPacoteRepositorio(processarPacoteDeDados(PACOTE), repo)
        antigo = os.getcwd()
        with tempfile.TemporaryDirectory() as pasta:
            os.chdir(pasta)
            try:
                salvarDadosTXT(repo)
                arquivo = glob.glob("historico_*.txt")[0]
                # mesma codificacao padrao com que salvarDadosTXT grava o arquivo
                with open(arquivo) as f:
                    linha = f.read().splitlines()[2]
            finally:
                os.chdir(antigo)
        self.assertEqual(
            linha,
            "tempo:12.0s  temperatura satélite:25.5°C   umidade:40.0%  "
            "pressão:101325.0Pa  altitude:100.0m latitude:-22.9 longitude:-43.1  "
            "n° de sats:7.0  giro x:1.0  giro y:2.0  giro z:3.0 ângulo LDR:45.0° "
            "temperatura bateria 1:30.0°C temperatura bateria 2:31.0°C tensão:7.4V "
            "corrente:1.2A n° de pacotes:5.0  RSSI:-90.0 dBm  tamanho do pacote:120.0",
        )


class AdaptadorFalso:
    """Devolve as linhas da lista e depois None; para a thread ao acabar."""

    def __init__(self, repositorio, linhas):
        self.repositorio = repositorio
        self.linhas = list(linhas)
        self.thread = None

    def lePacoteSerial(self):
        if not self.linhas:
            self.thread.flagRodando = False
            return None
        return self.linhas.pop(0)


class TestThreadSoEmiteComPacoteNovo(unittest.TestCase):

    def rodar(self, linhas):
        repo = RepositorioTelemetria()
        adaptador = AdaptadorFalso(repo, linhas)
        thread = ThreadPrincipal(adaptador)
        adaptador.thread = thread
        pontos, giros = [], []
        thread.ultimosSubdadosTemperaturaTempo.connect(lambda x, y: pontos.append((x, y)))
        thread.pacoteGiro.connect(lambda *a: giros.append(a))
        thread.run()
        return repo, pontos, giros

    def test_timeout_nao_repete_ponto(self):
        outro = PACOTE.replace("12:", "13:", 1)
        repo, pontos, giros = self.rodar([PACOTE, None, None, outro, None])
        self.assertEqual(pontos, [(12.0, 25.5), (13.0, 25.5)])
        self.assertEqual(len(repo.pacotesDados), 2)
        self.assertEqual(giros[0], (1.0, 2.0, 3.0, 45.0))

    def test_linha_que_nao_e_telemetria_nao_emite(self):
        repo, pontos, _ = self.rodar(["COMANDO_RX:AA BB", PACOTE])
        self.assertEqual(len(pontos), 1)
        self.assertEqual(len(repo.pacotesDados), 1)


if __name__ == "__main__":
    unittest.main()
