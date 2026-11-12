import os
import sys
from datetime import datetime


def diretorioImagens():
    """Pasta onde as imagens originais sao gravadas assim que chegam. No .exe
    fica ao lado do executavel (a pasta temporaria do PyInstaller some ao fechar)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'dados_salvos', 'imagens')


def salvarImagemOriginal(dadosJpeg: bytes, pasta: str, horario: datetime) -> str:
    """Grava o JPEG exatamente como chegou, sem recompressao. Devolve o caminho."""
    os.makedirs(pasta, exist_ok=True)  # Garante que o path existe/existirá
    nome = f"img_{horario.strftime('%Y-%m-%d_%H-%M-%S-%f')}.jpg"
    caminho = os.path.join(pasta, nome)
    with open(caminho, 'wb') as arquivo:
        arquivo.write(dadosJpeg)
    return caminho
