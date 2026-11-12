import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao.mensagens_orange import (
    ehMensagemOrange,
    interpretarMensagemOrange,
    lerMensagemOrange,
)

AC = "ORANGE:AC,17,1790950771.056,40621D,52.26578,3.93891,38000,450"
AC_RUMO = AC + ",254"


class TestAC(unittest.TestCase):

    def test_ac_sem_rumo(self):
        m = interpretarMensagemOrange(AC, chegada=1790950772.0)
        r = m.dados
        self.assertEqual(m.tipo, "AC")
        self.assertEqual((r.seq, r.ts, r.icao24), (17, 1790950771.056, "40621D"))
        self.assertEqual((r.latitude, r.longitude), (52.26578, 3.93891))
        self.assertEqual((r.altitudeFt, r.velocidadeKt), (38000, 450))
        self.assertIsNone(r.rumo)
        self.assertAlmostEqual(r.latencia, 0.944, places=3)

    def test_ac_com_rumo_e_icao_em_minuscula(self):
        r = interpretarMensagemOrange(AC_RUMO.replace("40621D", "40621d")).dados
        self.assertEqual((r.icao24, r.rumo), ("40621D", 254.0))

    def test_rumo_vazio_vale_como_ausente(self):
        self.assertIsNone(interpretarMensagemOrange(AC + ",").dados.rumo)

    def test_campos_extras_no_fim_sao_ignorados(self):
        r = interpretarMensagemOrange(AC_RUMO + ",-64,SIM0001").dados
        self.assertEqual(r.rumo, 254.0)

    def test_acs_invalidas(self):
        invalidas = [
            "ORANGE:AC,17,1790950771.056,40621D,52.2,3.9,38000",        # incompleta
            "ORANGE:AC,x,1790950771.056,40621D,52.2,3.9,38000,450",     # seq
            "ORANGE:AC,17,1790950771.056,ZZZZZZ,52.2,3.9,38000,450",    # ICAO
            "ORANGE:AC,17,1790950771.056,4062,52.2,3.9,38000,450",      # ICAO curto
            "ORANGE:AC,17,1790950771.056,40621D,95,3.9,38000,450",      # latitude
            "ORANGE:AC,17,1790950771.056,40621D,52.2,200,38000,450",    # longitude
            "ORANGE:AC,17,1790950771.056,40621D,52.2,3.9,inf,450",      # altitude
            "ORANGE:AC,17,nan,40621D,52.2,3.9,38000,450",               # tempo
            "ORANGE:AC,17,1790950771.056,40621D,52.2,3.9,38000,450,400",  # rumo
        ]
        for linha in invalidas:
            with self.assertRaises(ValueError, msg=linha):
                interpretarMensagemOrange(linha)


class TestOutrosTipos(unittest.TestCase):

    def test_status(self):
        m = interpretarMensagemOrange("ORANGE:STATUS,RUNNING,0,3,48.2,180,180,20,60,0.7,1.0")
        d = m.dados
        self.assertEqual(m.tipo, "STATUS")
        self.assertEqual((d["estado"], d["modo"], d["uptime_s"]), ("RUNNING", 0, 3))
        self.assertEqual((d["temp_cpu_c"], d["msgs_rx"], d["aeronaves"]), (48.2, 180, 20))
        self.assertEqual((d["lat_media_ms"], d["lat_max_ms"]), (0.7, 1.0))
        self.assertNotIn("descartados_fila", d)

    def test_status_com_campos_opcionais_no_fim_e_temperatura_vazia(self):
        d = interpretarMensagemOrange(
            "ORANGE:STATUS,IDLE,0,5,,10,10,2,8,0.5,0.9,3,1,40,50,60,1").dados
        self.assertIsNone(d["temp_cpu_c"])
        self.assertEqual((d["descartados_fila"], d["descartados_tx"]), (3, 1))
        self.assertEqual((d["msgs_ident"], d["msgs_pos"], d["msgs_vel"]), (40, 50, 60))
        self.assertEqual(d["relogio_ok"], 1)

    def test_opstate(self):
        d = interpretarMensagemOrange("ORANGE:OPSTATE,EXECUTANDO,1,0,120,3,500,2").dados
        self.assertEqual((d["estado"], d["auto"], d["ac_rx"], d["ac_perdidos"]), ("EXECUTANDO", 1, 120, 3))

    def test_evento(self):
        d = interpretarMensagemOrange("ORANGE:EVT,SDR_ERR,dongle solto").dados
        self.assertEqual((d["tipo"], d["args"]), ("SDR_ERR", ["dongle solto"]))

    def test_ack_start_traz_a_sessao(self):
        m = interpretarMensagemOrange("ORANGE:ACK,START,3")
        self.assertEqual((m.tipo, m.dados["comando"], m.dados["sessao"]), ("ACK", "START", 3))

    def test_ack_do_obc_e_nak(self):
        self.assertEqual(interpretarMensagemOrange("ORANGE:ACK,OP,AUTO,1").dados["args"], ["AUTO", "1"])
        d = interpretarMensagemOrange("ORANGE:NAK,START,JA_EM_EXECUCAO").dados
        self.assertEqual((d["comando"], d["args"]), ("START", ["JA_EM_EXECUCAO"]))

    def test_tipo_desconhecido_vira_outro(self):
        m = interpretarMensagemOrange("ORANGE:QRES,FOUND,7788FF")
        self.assertEqual(m.tipo, "OUTRO")


class TestVeredito(unittest.TestCase):

    def test_clandestina(self):
        d = interpretarMensagemOrange("ORANGE:VEREDITO,CLANDESTINA,-22.90680,-43.17290").dados
        self.assertEqual((d.latitude, d.longitude), (-22.9068, -43.1729))
        self.assertIsNone(d.indiceFoto)

    def test_so_a_clandestina_e_aceita(self):
        for linha in ("ORANGE:VEREDITO,NAO_CLANDESTINA,7788ff,TAP0803,-22.88,-43.3",
                      "ORANGE:VEREDITO,INDETERMINADO,-22.95,-43.18"):
            with self.assertRaises(ValueError, msg=linha):
                interpretarMensagemOrange(linha)

    def test_vereditos_invalidos(self):
        for linha in ("ORANGE:VEREDITO", "ORANGE:VEREDITO,CLANDESTINA,-22.9",
                      "ORANGE:VEREDITO,TALVEZ,-22.9,-43.1",
                      "ORANGE:VEREDITO,CLANDESTINA,95,-43.1"):
            with self.assertRaises(ValueError, msg=linha):
                interpretarMensagemOrange(linha)


class TestLeitura(unittest.TestCase):

    def test_reconhece_o_prefixo(self):
        self.assertTrue(ehMensagemOrange(AC))
        self.assertTrue(ehMensagemOrange("  orange:evt,boot"))
        self.assertFalse(ehMensagemOrange("12:25.5:40"))
        self.assertFalse(ehMensagemOrange("Controle de Atitude: OK"))
        self.assertFalse(ehMensagemOrange("2:AC,17,1.0,40621D,1,1,1,1"))

    def test_lerMensagemOrange_nunca_levanta(self):
        lixos = ["ORANGE:AC,x", "ORANGE:", "ORANGE:AC,17,nan,40621D,1,1,inf,1",
                 "ORANGE:VEREDITO,\xff\xfe", "ORANGE:STATUS", "ORANGE:AC," + "9" * 400]
        for linha in lixos:
            m = lerMensagemOrange(linha)
            self.assertIn(m.tipo, ("INVALIDA", "STATUS", "OUTRO"))
            self.assertEqual(m.bruta, linha.strip())

    def test_linha_invalida_guarda_o_motivo(self):
        m = lerMensagemOrange("ORANGE:AC,x,1,40621D,1,1,1,1")
        self.assertEqual(m.tipo, "INVALIDA")
        self.assertIn("erro", m.dados)


if __name__ == "__main__":
    unittest.main()
