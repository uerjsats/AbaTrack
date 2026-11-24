import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QCoreApplication

from aplicacao.bateria import registrarMediaBateria_useCase, sensorValido, temperaturaBateriaMedia
from dominio.entidades import RepositorioTelemetria
from UI.tela_bateria import potencia
from UI.thread_main import ThreadPrincipal

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


def pacote(bat1, bat2, tensao=7.4, corrente=1.2):
    return (f"12:25.5:40:100.0:101325:-22.9:-43.1:7:1.0:2.0:3.0:45.0:"
            f"{bat1}:{bat2}:{tensao}:{corrente}:5:-90:120")


class TestMedia(unittest.TestCase):

    def test_media_dos_dois_sensores(self):
        self.assertEqual(temperaturaBateriaMedia(20.0, 30.0), 25.0)

    def test_sensor_com_menos_127_e_descartado(self):
        self.assertEqual(temperaturaBateriaMedia(-127.0, 30.0), 30.0)
        self.assertEqual(temperaturaBateriaMedia(18.5, -127.00), 18.5)
        self.assertEqual(temperaturaBateriaMedia("-127", 22.0), 22.0)

    def test_os_dois_invalidos_nao_tem_media(self):
        self.assertIsNone(temperaturaBateriaMedia(-127.0, -127.0))
        self.assertIsNone(temperaturaBateriaMedia(None, float("nan")))

    def test_temperatura_negativa_valida_nao_e_descartada(self):
        self.assertEqual(temperaturaBateriaMedia(-3.0, 1.0), -1.0)
        self.assertTrue(sensorValido(-126.0))     # so o -127 e falha
        self.assertFalse(sensorValido(-127.0))

    def test_use_case_guarda_so_quando_ha_media(self):
        repo = RepositorioTelemetria()
        repo.tempbateria1, repo.tempbateria2 = [-127.0], [-127.0]
        self.assertIsNone(registrarMediaBateria_useCase(repo))
        self.assertEqual(repo.tempbateriaMedia, [])
        repo.tempbateria1.append(10.0)
        repo.tempbateria2.append(-127.0)
        self.assertEqual(registrarMediaBateria_useCase(repo), 10.0)
        self.assertEqual(repo.tempbateriaMedia, [10.0])


class TestPotencia(unittest.TestCase):

    def test_e_tensao_vezes_corrente(self):
        self.assertAlmostEqual(potencia(7.4, 1.2), 8.88)

    def test_sem_numero_valido_nao_tem_potencia(self):
        self.assertIsNone(potencia(None, 1.2))
        self.assertIsNone(potencia(float("nan"), 1.2))
        self.assertIsNone(potencia("x", 1.2))


class AdaptadorFalso:
    def __init__(self, repositorio, linhas):
        self.repositorio, self.linhas, self.thread = repositorio, list(linhas), None

    def lePacoteSerial(self):
        if not self.linhas:
            self.thread.flagRodando = False
            return None
        return self.linhas.pop(0)


class TestSinalDaThread(unittest.TestCase):

    def test_emite_tempo_tensao_corrente_e_media(self):
        repo = RepositorioTelemetria()
        adaptador = AdaptadorFalso(repo, [pacote(30, 31), pacote(-127, 18.5), pacote(-127, -127)])
        thread = ThreadPrincipal(adaptador)
        adaptador.thread = thread
        emitidos = []
        thread.pacoteBateria.connect(lambda *a: emitidos.append(a))
        thread.run()
        self.assertEqual(len(emitidos), 3)
        self.assertEqual(emitidos[0], (12.0, 7.4, 1.2, 30.5))
        self.assertEqual(emitidos[1][3], 18.5)                 # so o sensor 2
        self.assertTrue(math.isnan(emitidos[2][3]))            # os dois falharam
        self.assertEqual(repo.tempbateriaMedia, [30.5, 18.5])


if __name__ == "__main__":
    unittest.main()
