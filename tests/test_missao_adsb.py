import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.mensagens_orange import interpretarMensagemOrange, lerMensagemOrange
from aplicacao.metricas_adsb import metricasAdsb
from aplicacao.missao_adsb import registrarMensagemOrange_useCase, rumoEntre
from aplicacao.use_cases import registrarImagem_useCase
from dominio.entidades import TAMANHO_TRILHA, RepositorioTelemetria


def ac(seq, icao="40621D", lat=-22.9, lon=-43.2, ts=1000.0, rumo=None, chegada=1000.5):
    linha = f"ORANGE:AC,{seq},{ts},{icao},{lat},{lon},38000,450"
    if rumo is not None:
        linha += f",{rumo}"
    return interpretarMensagemOrange(linha, chegada)


def nada(dados, pasta, horario):
    return None


class BancoFalso:
    def __init__(self):
        self.recebidas = []

    def registrar(self, msg, sessao=0):
        self.recebidas.append((msg.tipo, sessao))


class TestRegistroAC(unittest.TestCase):

    def test_guarda_estado_trilha_e_lista(self):
        repo = RepositorioTelemetria()
        r1 = registrarMensagemOrange_useCase(ac(1), repo)
        r2 = registrarMensagemOrange_useCase(ac(2, lat=-22.8), repo)
        self.assertTrue(r1["novaAeronave"])
        self.assertFalse(r2["novaAeronave"])
        self.assertEqual(len(repo.registrosAdsb), 2)
        self.assertEqual(repo.aeronaves["40621D"].seq, 2)
        self.assertEqual([r.seq for r in repo.trilhas["40621D"]], [1, 2])

    def test_aeronaves_diferentes_tem_trilhas_separadas(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(ac(1, icao="AAAAAA"), repo)
        registrarMensagemOrange_useCase(ac(2, icao="BBBBBB"), repo)
        self.assertEqual(set(repo.aeronaves), {"AAAAAA", "BBBBBB"})
        self.assertEqual(len(repo.trilhas["AAAAAA"]), 1)

    def test_repeticao_do_dump_e_ignorada_na_memoria_mas_vai_ao_banco(self):
        repo, banco = RepositorioTelemetria(), BancoFalso()
        registrarMensagemOrange_useCase(ac(5), repo, banco)
        r = registrarMensagemOrange_useCase(ac(5), repo, banco)
        self.assertTrue(r["duplicada"])
        self.assertEqual(len(repo.registrosAdsb), 1)
        self.assertEqual(len(banco.recebidas), 2)

    def test_trilha_tem_tamanho_maximo(self):
        repo = RepositorioTelemetria()
        for i in range(1, TAMANHO_TRILHA + 30):
            registrarMensagemOrange_useCase(ac(i, lat=-22.9 + i * 0.001), repo)
        trilha = repo.trilhas["40621D"]
        self.assertEqual(len(trilha), TAMANHO_TRILHA)
        self.assertEqual(trilha[-1].seq, TAMANHO_TRILHA + 29)
        self.assertEqual(len(repo.registrosAdsb), TAMANHO_TRILHA + 29)

    def test_sessao_vem_do_ack_start(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(ac(1), repo)
        registrarMensagemOrange_useCase(interpretarMensagemOrange("ORANGE:ACK,START,2"), repo)
        registrarMensagemOrange_useCase(ac(1), repo)   # mesmo seq, outra sessao: nao e repeticao
        self.assertEqual([r.sessao for r in repo.registrosAdsb], [0, 2])


class TestRumo(unittest.TestCase):

    def test_rumo_entre_pontos_cardeais(self):
        self.assertAlmostEqual(rumoEntre(0, 0, 1, 0), 0, places=3)
        self.assertAlmostEqual(rumoEntre(0, 0, 0, 1), 90, places=3)
        self.assertAlmostEqual(rumoEntre(0, 0, -1, 0), 180, places=3)
        self.assertAlmostEqual(rumoEntre(0, 0, 0, -1), 270, places=3)

    def test_rumo_estimado_quando_falta(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(ac(1, lat=-22.9, lon=-43.2), repo)
        registrarMensagemOrange_useCase(ac(2, lat=-22.9, lon=-43.1), repo)   # para leste
        r1, r2 = repo.registrosAdsb
        self.assertIsNone(r1.rumo)
        self.assertAlmostEqual(r2.rumo, 90, delta=0.5)
        self.assertTrue(r2.rumoEstimado)

    def test_rumo_do_adsb_nao_e_sobrescrito(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(ac(1, lat=-22.9, lon=-43.2), repo)
        registrarMensagemOrange_useCase(ac(2, lat=-22.9, lon=-43.1, rumo=33), repo)
        self.assertEqual(repo.registrosAdsb[1].rumo, 33.0)
        self.assertFalse(repo.registrosAdsb[1].rumoEstimado)

    def test_sem_deslocamento_nao_estima_rumo(self):
        repo = RepositorioTelemetria()
        registrarMensagemOrange_useCase(ac(1), repo)
        registrarMensagemOrange_useCase(ac(2), repo)
        self.assertIsNone(repo.registrosAdsb[1].rumo)


class TestOutrasMensagens(unittest.TestCase):

    def test_status_opstate_eventos_e_confirmacoes(self):
        repo = RepositorioTelemetria()
        for linha in ("ORANGE:STATUS,RUNNING,0,3,48.2,180,180,20,60,0.7,1.0",
                      "ORANGE:OPSTATE,EXECUTANDO,1,0,120,0,500,0",
                      "ORANGE:EVT,SDR_OK", "ORANGE:ACK,PING", "ORANGE:NAK,START,JA_EM_EXECUCAO"):
            registrarMensagemOrange_useCase(interpretarMensagemOrange(linha), repo)
        self.assertEqual(repo.statusOrange["aeronaves"], 20)
        self.assertEqual(repo.opstateOrange["ac_rx"], 120)
        self.assertEqual([e[1] for e in repo.eventosOrange], ["SDR_OK"])
        self.assertEqual([(c[1], c[2]) for c in repo.confirmacoesOrange],
                         [("ACK", "PING"), ("NAK", "START")])

    def test_mensagem_invalida_so_vai_ao_banco(self):
        from aplicacao.mensagens_orange import lerMensagemOrange
        repo, banco = RepositorioTelemetria(), BancoFalso()
        registrarMensagemOrange_useCase(lerMensagemOrange("ORANGE:AC,x"), repo, banco)
        self.assertEqual(len(repo.registrosAdsb), 0)
        self.assertEqual(banco.recebidas[0][0], "INVALIDA")

    def test_veredito_associa_a_foto_nas_duas_ordens(self):
        repo = RepositorioTelemetria()
        img = registrarImagem_useCase(b"x", repo, "p", nada)
        v = interpretarMensagemOrange("ORANGE:VEREDITO,CLANDESTINA,-22.9068,-43.1729",
                                      chegada=img.horario.timestamp() + 5)
        resultado = registrarMensagemOrange_useCase(v, repo)
        self.assertEqual(len(resultado["pares"]), 1)
        self.assertIs(img.deteccao, repo.deteccoes[0])

        v2 = interpretarMensagemOrange("ORANGE:VEREDITO,CLANDESTINA,-22.9,-43.1",
                                       chegada=img.horario.timestamp() + 5)
        registrarMensagemOrange_useCase(v2, repo)
        img2 = registrarImagem_useCase(b"y", repo, "p", nada)
        self.assertIs(img2.deteccao, repo.deteccoes[1])

    def test_outros_vereditos_sao_invalidos_e_nao_roubam_foto(self):
        repo = RepositorioTelemetria()
        agora = datetime.now().timestamp()
        for linha in ("ORANGE:VEREDITO,NAO_CLANDESTINA,7788FF,TAP0803,-22.88,-43.3",
                      "ORANGE:VEREDITO,INDETERMINADO,-22.95,-43.18"):
            registrarMensagemOrange_useCase(lerMensagemOrange(linha, chegada=agora), repo)
        self.assertEqual(repo.deteccoes, [])
        img = registrarImagem_useCase(b"x", repo, "p", nada)
        self.assertIsNone(img.deteccao)


class TestMetricas(unittest.TestCase):

    def registros(self, seqs, ts=1000.0, atraso=0.5):
        repo = RepositorioTelemetria()
        for s in seqs:
            registrarMensagemOrange_useCase(ac(s, ts=ts + s, chegada=ts + s + atraso), repo)
        return repo.registrosAdsb

    def test_perda_pelas_lacunas_do_seq(self):
        m = metricasAdsb(self.registros([1, 2, 3, 6, 7, 10]))
        self.assertEqual((m["esperados"], m["perdidos"]), (10, 4))
        self.assertAlmostEqual(m["taxaPerda"], 0.4)

    def test_sem_perda(self):
        m = metricasAdsb(self.registros(range(1, 11)))
        self.assertEqual(m["perdidos"], 0)
        self.assertEqual(m["aeronaves"], 1)

    def test_latencia(self):
        m = metricasAdsb(self.registros(range(1, 21), atraso=2.0))
        self.assertAlmostEqual(m["latenciaMediaS"], 2.0)
        self.assertAlmostEqual(m["latenciaMaxS"], 2.0)
        self.assertAlmostEqual(m["latenciaP95S"], 2.0)

    def test_relogio_do_orange_nao_acertado_fica_fora_da_latencia(self):
        m = metricasAdsb(self.registros([1, 2], ts=50.0, atraso=1.7e9))
        self.assertIsNone(m["latenciaMediaS"])
        self.assertEqual(m["latenciasDescartadas"], 2)

    def test_relogio_do_orange_adiantado_fica_fora_da_latencia(self):
        m = metricasAdsb(self.registros([1, 2, 3], atraso=-30.0))
        self.assertIsNone(m["latenciaMediaS"])
        self.assertEqual(m["latenciasDescartadas"], 3)

    def test_sem_registros(self):
        m = metricasAdsb([])
        self.assertEqual((m["registros"], m["perdidos"]), (0, 0))
        self.assertIsNone(m["taxaPerda"])


if __name__ == "__main__":
    unittest.main()
