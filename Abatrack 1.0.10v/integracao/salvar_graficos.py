import os
from datetime import datetime
import matplotlib.pyplot as plt

def salvarGrafico(dadosX: list,
                  dadosY: list,
                  tituloX: str,
                  tituloY: str,
                  path: str
    ):
    """Implementação de salvarGrafico_useCase"""
    os.makedirs(path, exist_ok=True)  # Garante que o path existe/existirá

    hora_atual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"grafico_{tituloX}x{tituloY}_{hora_atual}.png"
    path_completo = os.path.join(path, nome_arquivo)

    # Cria figura e eixos isolados
    fig, ax = plt.subplots()
    ax.plot(dadosX, dadosY, linestyle="-", marker="o")
    ax.set_xlabel(tituloX)
    ax.set_ylabel(tituloY)
    ax.set_title(f"{tituloX} x {tituloY}")
    ax.set_xticks(dadosX)
    ax.grid(True, linestyle="-")

    # Salva e fecha apenas essa figura
    fig.savefig(path_completo)
    plt.close(fig)
