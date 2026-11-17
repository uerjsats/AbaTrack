import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QCoreApplication

from dominio.entidades import ConfigsComunicacao, RepositorioTelemetria
from integracao.adaptador_arduino import AdaptadorArduino

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


class SerialEmEtapas:
    """Cada read() entrega o proximo bloco; in_waiting diz se ainda ha bloco."""
    is_open = True

    def __init__(self, blocos):
        self.blocos = list(blocos)
        self.leituras = 0

    @property
    def in_waiting(self):
        return len(self.blocos[0]) if self.blocos else 0

    def read(self, n):
        self.leituras += 1
        return self.blocos.pop(0) if self.blocos else b""


class TestLeituraComFila(unittest.TestCase):

    def test_continua_lendo_a_porta_mesmo_com_linhas_na_fila(self):
        """Com linhas esperando para serem entregues, os bytes novos precisam ser
        lidos ja: senao o buffer do driver estoura durante uma rajada."""
        adaptador = AdaptadorArduino(RepositorioTelemetria(), ConfigsComunicacao("X", 115200))
        adaptador.timeout = 0.1
        serial = SerialEmEtapas([b"a\nb\nc\n", b"d\ne\n"])
        adaptador.conexao = serial
        self.assertEqual(adaptador.lePacoteSerial(), "a")
        self.assertEqual(adaptador.lePacoteSerial(), "b")
        self.assertEqual(serial.leituras, 2)          # o 2o bloco ja foi lido
        self.assertEqual([adaptador.lePacoteSerial() for _ in range(3)], ["c", "d", "e"])


if __name__ == "__main__":
    unittest.main()
