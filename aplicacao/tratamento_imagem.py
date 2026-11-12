"""Tratamento das imagens recebidas do satelite (sem dependencia de Qt)."""

import io

from PIL import Image, ImageEnhance, ImageFile, ImageOps

# Mostra o que deu para decodificar mesmo se o JPEG vier cortado.
ImageFile.LOAD_TRUNCATED_IMAGES = True


def abrirJpeg(dadosJpeg: bytes) -> Image.Image:
    """Decodifica o JPEG recebido. Levanta OSError se estiver corrompido."""
    imagem = Image.open(io.BytesIO(dadosJpeg))
    imagem.load()
    return imagem


def aplicarTratamento(imagem: Image.Image,
                      autoContraste: bool = False,
                      inverter: bool = False,
                      brilho: int = 0,
                      contraste: int = 0) -> Image.Image:
    """Devolve uma copia tratada. brilho e contraste vao de -100 a 100 (0 = original)."""
    resultado = imagem.convert("L") if imagem.mode in ("1", "P") else imagem.copy()

    if autoContraste:
        resultado = ImageOps.autocontrast(resultado, cutoff=1)
    if brilho:
        resultado = ImageEnhance.Brightness(resultado).enhance(1 + brilho / 100)
    if contraste:
        resultado = ImageEnhance.Contrast(resultado).enhance(1 + contraste / 100)
    if inverter:
        resultado = ImageOps.invert(resultado.convert("RGB") if resultado.mode == "RGBA" else resultado)
    return resultado
