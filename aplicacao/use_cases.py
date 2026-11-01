import os
from typing import Callable

from datetime import datetime
from dominio.entidades import RepositorioTelemetria, ConfigsComunicacao, ImagemTelemetria

def alterarPortaArduino(configAtual: ConfigsComunicacao, novaPorta: str):
    portaAntiga = configAtual.portaAntiga
    configAtual.portaArduino = novaPorta
    print(f"Porta alterada: {portaAntiga} -> {configAtual.portaArduino}")

def alterarBaudRate(configAtual: ConfigsComunicacao, novoBaudRate: int):
    baudAntiga = configAtual.baudRate
    configAtual.baudRate = int(novoBaudRate)
    print(f"Baud Rate alterada: {baudAntiga} -> {configAtual.baudRate}")

def processarPacoteDeDados(pacote):
    # Divide o pacote em partes
    partes = pacote.split(":")
    
    # Converte cada parte para float, substituindo valores vazios por 0.0
    partes_completas = [float(parte) if parte.strip() else 0.0 for parte in partes]
    
    # Preenche com 0.0 até o tamanho esperado (14 índices, por exemplo)
    while len(partes_completas) < 19:  # Ajuste o número para o tamanho esperado do pacote
        partes_completas.append(0.0)
    
    return partes_completas

def adicionarPacoteRepositorio(pacote, repositorio: RepositorioTelemetria):
    repositorio.pacotesDados.append(pacote)

def filtraSubdado(listaSubdados, indiceSubdado, repositorio: RepositorioTelemetria):
    if repositorio.pacotesDados:
        conjuntoDados = repositorio.pacotesDados[-1]
        dado = conjuntoDados[indiceSubdado]
        listaSubdados.append(dado)

def salvarDadosTXT(repositorio: RepositorioTelemetria):
    if not repositorio.pacotesDados:
        print("Nenhum dado registrado.")
        return
    dataHoraAtual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nomeArquivo = f"historico_{dataHoraAtual}.txt"

    with open(nomeArquivo, 'w') as file:
        file.write(f"Historico de Telemetria - {dataHoraAtual}\n")
        file.write("-------------------------------\n")

        for pacote in repositorio.pacotesDados:
            file.write(f"tempo:{pacote[0]}s  temperatura satélite:{pacote[1]}°C   umidade:{pacote[2]}%  pressão:{pacote[4]}Pa  altitude:{pacote[3]}m latitude:{pacote[5]} longitude:{pacote[6]}  n° de sats:{pacote[7]}  giro x:{pacote[8]}  giro y:{pacote[9]}  giro z:{pacote[10]} ângulo LDR:{pacote[11]}° temperatura bateria 1:{pacote[12]}°C temperatura bateria 2:{pacote[13]}°C tensão:{pacote[14]}V corrente:{pacote[15]}A n° de pacotes:{pacote[16]}  RSSI:{pacote[17]} dBm  tamanho do pacote:{pacote[18]}\n")
    print("Histórico salvo no TXT")


def registrarImagem_useCase(dadosJpeg: bytes,
                  repositorio: RepositorioTelemetria,
                  pasta: str,
                  funcaoSalvarImagem: Callable[[bytes, str, datetime], str]
    ) -> ImagemTelemetria:
    """Guarda a imagem no repositorio e grava o original em disco."""
    if not dadosJpeg:
        raise ValueError("Imagem vazia.")

    horario = datetime.now()
    try:
        caminho = funcaoSalvarImagem(dadosJpeg, pasta, horario)
    except OSError as e:
        print(f"Erro ao salvar imagem: {e}")
        caminho = None

    indicePacote = len(repositorio.pacotesDados) - 1 if repositorio.pacotesDados else None
    imagem = ImagemTelemetria(dadosJpeg, horario, caminho, indicePacote)
    repositorio.imagens.append(imagem)
    return imagem

def telemetriaDaImagem(imagem: ImagemTelemetria, repositorio: RepositorioTelemetria):
    """Telemetria do momento em que a imagem chegou, ou None se nao havia."""
    indice = imagem.indicePacote
    if indice is None or indice >= len(repositorio.pacotesDados):
        return None
    pacote = repositorio.pacotesDados[indice]
    return {
        "tempo": pacote[0],
        "altitude": pacote[3],
        "latitude": pacote[5],
        "longitude": pacote[6],
    }

def salvarGrafico_useCase(dadosX:list,
                  dadosY:list,
                  tituloX:str,
                  tituloY:str,
                  path:str,
                  funcaoSalvarGrafico:Callable[[list, list, str, str, str], None]
    ):

    if len(dadosX) != len(dadosY):
        raise ValueError("Listas com valores diferentes.")

    funcaoSalvarGrafico(dadosX, dadosY, tituloX, tituloY, path)
