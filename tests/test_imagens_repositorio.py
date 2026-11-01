import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.use_cases import (
    adicionarPacoteRepositorio,
    processarPacoteDeDados,
    registrarImagem_useCase,
    telemetriaDaImagem,
)
from dominio.entidades import RepositorioTelemetria
from integracao.armazenamento_imagens import salvarImagemOriginal

PACOTE = "12:25.5:40:100.0:101325:-22.9:-43.1:7:1.0:2.0:3.0:45.0:30:31:7.4:1.2:5:-90:120"


class TestRegistrarImagem(unittest.TestCase):

    def test_guarda_no_repositorio_e_grava_o_original(self):
        repo = RepositorioTelemetria()
        with tempfile.TemporaryDirectory() as pasta:
            dados = b"\xff\xd8\n\r\n\xff\xd9"
            imagem = registrarImagem_useCase(dados, repo, pasta, salvarImagemOriginal)
            self.assertEqual(repo.imagens, [imagem])
            self.assertEqual(open(imagem.caminho, "rb").read(), dados)

    def test_guarda_o_indice_da_telemetria_do_momento(self):
        repo = RepositorioTelemetria()
        sem = registrarImagem_useCase(b"x", repo, tempfile.gettempdir(),
                                      lambda d, p, h: None)
        self.assertIsNone(sem.indicePacote)
        self.assertIsNone(telemetriaDaImagem(sem, repo))

        adicionarPacoteRepositorio(processarPacoteDeDados(PACOTE), repo)
        com = registrarImagem_useCase(b"x", repo, tempfile.gettempdir(),
                                      lambda d, p, h: None)
        self.assertEqual(com.indicePacote, 0)
        t = telemetriaDaImagem(com, repo)
        self.assertEqual((t["tempo"], t["altitude"]), (12.0, 100.0))

    def test_falha_de_disco_nao_perde_a_imagem(self):
        repo = RepositorioTelemetria()

        def falha(dados, pasta, horario):
            raise OSError("disco cheio")

        imagem = registrarImagem_useCase(b"x", repo, "p", falha)
        self.assertIsNone(imagem.caminho)
        self.assertEqual(len(repo.imagens), 1)

    def test_imagem_vazia_e_rejeitada(self):
        with self.assertRaises(ValueError):
            registrarImagem_useCase(b"", RepositorioTelemetria(), "p", lambda *a: None)


if __name__ == "__main__":
    unittest.main()
