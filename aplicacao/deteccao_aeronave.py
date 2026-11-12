"""Deteccao de aeronaves da missao secundaria: leitura da linha enviada pela
base e associacao com a foto correspondente."""

from datetime import datetime

from dominio.entidades import DeteccaoAeronave, RepositorioTelemetria

PREFIXO_DETECCAO = "DET,"

# A foto e a linha DET chegam por caminhos diferentes (a foto leva dezenas de
# segundos pelo LoRa). Elas so sao associadas se chegarem com ate esta
# diferenca de tempo, para uma foto sem deteccao nao casar com a deteccao seguinte.
JANELA_ASSOCIACAO_S = 180


def ehLinhaDeteccao(linha: str) -> bool:
    return linha.lstrip().upper().startswith(PREFIXO_DETECCAO)


def interpretarLinhaDeteccao(linha: str, horario=None) -> DeteccaoAeronave:
    """Formato antigo (so clandestinas), mantido por compatibilidade:

        DET,<foto>,<lat>,<lon>

    O firmware atual manda ORANGE:VEREDITO (ver interpretarVeredito). Campos
    extras depois de <lon> sao ignorados. Levanta ValueError se a linha for
    invalida.
    """
    if not ehLinhaDeteccao(linha):
        raise ValueError("a linha nao e uma deteccao")
    partes = [p.strip() for p in linha.strip().split(",")]
    if len(partes) < 4:
        raise ValueError("deteccao incompleta")

    indiceFoto = int(partes[1])
    if indiceFoto < 0:
        raise ValueError("indice de foto negativo")
    latitude, longitude = float(partes[2]), float(partes[3])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("coordenadas fora do intervalo")

    return DeteccaoAeronave(indiceFoto, latitude, longitude,
                            horario or datetime.now())


def interpretarVeredito(campos, horario=None) -> DeteccaoAeronave:
    """campos = o que vem depois de "VEREDITO,". O OBC so envia clandestinas:

        CLANDESTINA,<lat>,<lon>

    Levanta ValueError se o veredito for invalido ou nao for CLANDESTINA.
    """
    campos = [c.strip() for c in campos]
    if not campos:
        raise ValueError("veredito vazio")
    if campos[0].upper() != "CLANDESTINA":
        raise ValueError(f"veredito desconhecido: {ascii(campos[0][:20])}")
    if len(campos) < 3:
        raise ValueError("veredito incompleto")
    latitude, longitude = float(campos[1]), float(campos[2])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("coordenadas fora do intervalo")
    return DeteccaoAeronave(None, latitude, longitude,
                            horario or datetime.now())


def associarDeteccoesEImagens(repositorio: RepositorioTelemetria):
    """Liga cada deteccao sem foto a imagem sem deteccao mais antiga que tenha
    chegado dentro da janela de tempo. Funciona nas duas ordens de chegada.
    Devolve a lista de pares (deteccao, imagem) criados agora."""
    pares = []
    for deteccao in repositorio.deteccoes:
        if deteccao.imagem is not None:
            continue
        for imagem in repositorio.imagens:
            if imagem.deteccao is not None:
                continue
            diferenca = abs((imagem.horario - deteccao.horario).total_seconds())
            if diferenca <= JANELA_ASSOCIACAO_S:
                deteccao.imagem = imagem
                imagem.deteccao = deteccao
                pares.append((deteccao, imagem))
                break
    return pares


def registrarDeteccao_useCase(deteccao: DeteccaoAeronave,
                              repositorio: RepositorioTelemetria):
    """Guarda a deteccao no repositorio e a associa a foto, se ela ja chegou."""
    repositorio.deteccoes.append(deteccao)
    return associarDeteccoesEImagens(repositorio)
