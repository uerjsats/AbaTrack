import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QCoreApplication

from integracao.portas_seriais import MonitorPortas

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


def esperar(condicao, limite=3.0):
    fim = time.monotonic() + limite
    while time.monotonic() < fim and not condicao():
        app.processEvents()
        time.sleep(0.01)
    return condicao()


class TestMonitorPortas(unittest.TestCase):

    def monitor(self, listar, intervalo=0.02):
        m = MonitorPortas(listar=listar, intervalo=intervalo)
        self.recebidas = []
        m.portasMudaram.connect(self.recebidas.append)
        self.addCleanup(m.parar)
        m.iniciar()
        return m

    def test_so_avisa_quando_a_lista_muda(self):
        estados = [["COM3"], ["COM3"], ["COM3", "COM7"], ["COM3", "COM7"]]
        def listar():
            return estados.pop(0) if len(estados) > 1 else estados[0]
        self.monitor(listar)
        self.assertTrue(esperar(lambda: len(self.recebidas) >= 2))
        time.sleep(0.15)
        app.processEvents()
        self.assertEqual(self.recebidas, [["COM3"], ["COM3", "COM7"]])

    def test_erro_na_consulta_nao_derruba_o_monitor(self):
        chamadas = []
        def listar():
            chamadas.append(1)
            if len(chamadas) == 1:
                raise OSError("driver ocupado")
            return ["COM5"]
        self.monitor(listar)
        self.assertTrue(esperar(lambda: ["COM5"] in self.recebidas))

    def test_consulta_lenta_nao_trava_quem_chamou(self):
        liberar = threading.Event()
        def listar():
            liberar.wait(5)            # simula o Windows reconhecendo um USB novo
            return ["COM9"]
        self.addCleanup(liberar.set)
        inicio = time.monotonic()
        self.monitor(listar, intervalo=0.01)
        self.assertLess(time.monotonic() - inicio, 0.2)   # iniciar() volta na hora
        liberar.set()
        self.assertTrue(esperar(lambda: self.recebidas == [["COM9"]]))


if __name__ == "__main__":
    unittest.main()
