import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from aplicacao.tratamento_imagem import abrirJpeg, aplicarTratamento


def imagemAssimetrica():
    """4x3 com um pixel diferente em cada canto, para ver para onde cada um vai."""
    imagem = Image.new("L", (4, 3), 100)
    imagem.putpixel((0, 0), 10)     # canto superior esquerdo
    imagem.putpixel((3, 0), 20)     # canto superior direito
    imagem.putpixel((0, 2), 30)     # canto inferior esquerdo
    imagem.putpixel((3, 2), 40)     # canto inferior direito
    return imagem


class TestRotacao(unittest.TestCase):

    def test_cada_canto_vai_para_o_canto_oposto(self):
        r = aplicarTratamento(imagemAssimetrica(), rotacao=180)
        self.assertEqual(r.size, (4, 3))
        self.assertEqual(r.getpixel((3, 2)), 10)
        self.assertEqual(r.getpixel((0, 2)), 20)
        self.assertEqual(r.getpixel((3, 0)), 30)
        self.assertEqual(r.getpixel((0, 0)), 40)

    def test_90_graus_horario_troca_largura_e_altura(self):
        r = aplicarTratamento(imagemAssimetrica(), rotacao=90)
        self.assertEqual(r.size, (3, 4))
        self.assertEqual(r.getpixel((2, 0)), 10)   # canto sup. esquerdo vai para o sup. direito
        self.assertEqual(r.getpixel((2, 3)), 20)

    def test_270_e_o_inverso_de_90(self):
        o = imagemAssimetrica()
        r = aplicarTratamento(aplicarTratamento(o, rotacao=90), rotacao=270)
        self.assertEqual(list(r.getdata()), list(o.getdata()))

    def test_360_nao_muda(self):
        o = imagemAssimetrica()
        self.assertEqual(list(aplicarTratamento(o, rotacao=360).getdata()), list(o.getdata()))

    def test_sem_a_opcao_a_imagem_nao_muda(self):
        original = imagemAssimetrica()
        r = aplicarTratamento(original)
        self.assertEqual(list(r.getdata()), list(original.getdata()))

    def test_girar_duas_vezes_volta_ao_original(self):
        original = imagemAssimetrica()
        r = aplicarTratamento(aplicarTratamento(original, rotacao=180), rotacao=180)
        self.assertEqual(list(r.getdata()), list(original.getdata()))

    def test_nao_altera_a_imagem_de_entrada(self):
        original = imagemAssimetrica()
        antes = list(original.getdata())
        aplicarTratamento(original, rotacao=180)
        self.assertEqual(list(original.getdata()), antes)

    def test_combina_com_o_negativo(self):
        r = aplicarTratamento(imagemAssimetrica(), rotacao=180, inverter=True)
        self.assertEqual(r.getpixel((3, 2)), 255 - 10)
        self.assertEqual(r.getpixel((0, 0)), 255 - 40)

    def test_vale_para_imagem_colorida(self):
        imagem = Image.new("RGB", (2, 2), (0, 0, 0))
        imagem.putpixel((0, 0), (255, 0, 0))
        r = aplicarTratamento(imagem, rotacao=180)
        self.assertEqual(r.getpixel((1, 1)), (255, 0, 0))

    def test_jpeg_recebido_gira_sem_mudar_o_tamanho(self):
        buf = io.BytesIO()
        Image.new("L", (320, 240), 120).save(buf, "JPEG")
        r = aplicarTratamento(abrirJpeg(buf.getvalue()), rotacao=180)
        self.assertEqual(r.size, (320, 240))


if __name__ == "__main__":
    unittest.main()
