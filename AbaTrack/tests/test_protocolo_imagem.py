import io
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integracao.protocolo_imagem import ProtocoloImagem


def quadro(jpeg: bytes) -> bytes:
    return b"IMAGE_BEGIN\n" + b"SIZE:%d\n" % len(jpeg) + jpeg + b"IMAGE_END\n"


def jpegDificil() -> bytes:
    """Bytes com '\n', '\r', nao-UTF-8 e ate "IMAGE_END" no meio, como num JPEG."""
    rng = random.Random(1)
    corpo = bytes(rng.randrange(256) for _ in range(5000))
    return b"\xff\xd8" + corpo + b"\nIMAGE_END\n\r\n" + corpo + b"\xff\xd9"


class Coletor:
    def __init__(self):
        self.eventos = []
        self.parser = ProtocoloImagem(lambda t, d: self.eventos.append((t, d)))

    def tipo(self, nome):
        return [d for t, d in self.eventos if t == nome]


class TestProtocoloImagem(unittest.TestCase):

    def test_imagem_com_bytes_perigosos(self):
        c = Coletor()
        jpeg = jpegDificil()
        c.parser.alimentar(quadro(jpeg))
        self.assertEqual(c.tipo("completa"), [jpeg])
        self.assertEqual(c.tipo("erro"), [])
        self.assertEqual(c.tipo("linha_invalida"), [])

    def test_pedacos_arbitrarios(self):
        jpeg = jpegDificil()
        fluxo = b"1:2:3\n" + quadro(jpeg) + b"4:5:6\n"
        for tamanho in (1, 2, 7, 64, 1000):
            c = Coletor()
            for i in range(0, len(fluxo), tamanho):
                c.parser.alimentar(fluxo[i:i + tamanho])
            self.assertEqual(c.tipo("completa"), [jpeg], tamanho)
            self.assertEqual(c.tipo("linha"), ["1:2:3", "4:5:6"], tamanho)

    def test_telemetria_e_imagens_intercaladas(self):
        c = Coletor()
        a, b = jpegDificil(), b"\xff\xd8abc\n\xff\xd9"
        c.parser.alimentar(b"t1\n" + quadro(a) + b"t2\n" + quadro(b) + b"t3\n")
        self.assertEqual(c.tipo("completa"), [a, b])
        self.assertEqual(c.tipo("linha"), ["t1", "t2", "t3"])

    def test_tamanho_invalido(self):
        c = Coletor()
        c.parser.alimentar(b"IMAGE_BEGIN\nSIZE:999999999\n")
        self.assertEqual(len(c.tipo("erro")), 1)
        self.assertFalse(c.parser.recebendoImagem)

    def test_sem_size(self):
        c = Coletor()
        c.parser.alimentar(b"IMAGE_BEGIN\n10:20:30\n")
        self.assertEqual(len(c.tipo("erro")), 1)
        self.assertEqual(c.tipo("linha"), ["10:20:30"])

    def test_sem_image_end(self):
        c = Coletor()
        c.parser.alimentar(b"IMAGE_BEGIN\nSIZE:3\nabcXXX\n")
        self.assertEqual(c.tipo("completa"), [])
        self.assertEqual(len(c.tipo("erro")), 1)

    def test_entrar_no_meio_da_imagem_nao_gera_imagem(self):
        c = Coletor()
        jpeg = jpegDificil()
        c.parser.alimentar(jpeg[2000:] + b"IMAGE_END\n" + b"1:2:3\n")
        self.assertEqual(c.tipo("completa"), [])
        self.assertEqual(c.tipo("linha")[-1], "1:2:3")

    def test_abortar_imagem_parada(self):
        c = Coletor()
        c.parser.alimentar(b"IMAGE_BEGIN\nSIZE:100\nabc")
        self.assertTrue(c.parser.recebendoImagem)
        c.parser.abortar("timeout")
        self.assertFalse(c.parser.recebendoImagem)
        self.assertEqual(c.tipo("erro"), ["timeout"])
        c.parser.alimentar(b"7:8:9\n")
        self.assertEqual(c.tipo("linha"), ["7:8:9"])

    def test_lixo_sem_quebra_de_linha_nao_cresce_sem_limite(self):
        c = Coletor()
        c.parser.alimentar(b"\xff" * 10000)
        self.assertEqual(len(c.tipo("linha_invalida")), 1)
        self.assertLess(len(c.parser._buffer), 4097)


if __name__ == "__main__":
    unittest.main()
