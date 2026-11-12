"""Missao ADS-B no AbaTrack: o que fazer com cada mensagem ORANGE: recebida."""

import math
from collections import deque

from aplicacao.deteccao_aeronave import registrarDeteccao_useCase
from dominio.entidades import TAMANHO_TRILHA, RegistroAeronave, RepositorioTelemetria

# Deslocamento minimo (graus, ~11 m) para estimar o rumo entre duas posicoes.
DESLOCAMENTO_MINIMO_GRAUS = 1e-4


def rumoEntre(lat1, lon1, lat2, lon2):
    """Rumo inicial, em graus (0 a 360), de (lat1, lon1) para (lat2, lon2)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _guardarAeronave(registro: RegistroAeronave, repositorio: RepositorioTelemetria):
    """Atualiza o estado e o rastro da aeronave. Devolve True se ela e nova."""
    novaAeronave = registro.icao24 not in repositorio.aeronaves
    trilha = repositorio.trilhas.setdefault(registro.icao24, deque(maxlen=TAMANHO_TRILHA))

    if registro.rumo is None and trilha:
        anterior = trilha[-1]
        if (abs(registro.latitude - anterior.latitude)
                + abs(registro.longitude - anterior.longitude)) >= DESLOCAMENTO_MINIMO_GRAUS:
            registro.rumo = rumoEntre(anterior.latitude, anterior.longitude,
                                      registro.latitude, registro.longitude)
            registro.rumoEstimado = True

    trilha.append(registro)
    repositorio.aeronaves[registro.icao24] = registro
    repositorio.registrosAdsb.append(registro)
    return novaAeronave


def registrarMensagemOrange_useCase(msg, repositorio: RepositorioTelemetria, banco=None):
    """Guarda a mensagem no repositorio e, se houver banco, grava-a nele.

    Devolve {"tipo", "novaAeronave", "duplicada", "pares"}: pares sao as
    (deteccao, imagem) formadas por um VEREDITO com fotos que ja tinham chegado.
    """
    resultado = {"tipo": msg.tipo, "novaAeronave": False, "duplicada": False, "pares": []}
    dados = msg.dados

    if msg.tipo == "AC":
        dados.sessao = repositorio.sessaoOrange
        chave = (dados.sessao, dados.seq)
        if chave in repositorio.chavesAdsb:
            resultado["duplicada"] = True       # por exemplo, reenviada pelo DUMP
        else:
            repositorio.chavesAdsb.add(chave)
            resultado["novaAeronave"] = _guardarAeronave(dados, repositorio)
    elif msg.tipo == "STATUS":
        repositorio.statusOrange = dados
    elif msg.tipo == "OPSTATE":
        repositorio.opstateOrange = dados
    elif msg.tipo == "EVT":
        repositorio.eventosOrange.append((msg.chegada, dados["tipo"], dados["args"]))
    elif msg.tipo in ("ACK", "NAK"):
        repositorio.confirmacoesOrange.append(
            (msg.chegada, msg.tipo, dados["comando"], dados["args"]))
        if msg.tipo == "ACK" and dados["comando"] == "START" and "sessao" in dados:
            repositorio.sessaoOrange = dados["sessao"]
    elif msg.tipo == "VEREDITO":
        resultado["pares"] = registrarDeteccao_useCase(dados, repositorio)

    if banco is not None:
        banco.registrar(msg, repositorio.sessaoOrange)
    return resultado
