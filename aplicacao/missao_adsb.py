"""Missao ADS-B no AbaTrack: o que fazer com cada mensagem ORANGE: recebida."""

import math
import time
from collections import deque

from aplicacao.deteccao_aeronave import registrarDeteccao_useCase
from dominio.entidades import (
    TAMANHO_TRILHA,
    PosicaoMissao,
    RegistroAeronave,
    RepositorioTelemetria,
)

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


CABECALHO_CSV_ADSB = (
    "sessao", "seq", "icao24", "hora_orange", "chegada_pc", "latitude", "longitude",
    "altitude_ft", "altitude_m", "velocidade_kt", "velocidade_kmh",
    "rumo_graus", "rumo_origem", "latencia_s",
)


def linhasCsvAdsb(registros):
    """Cabecalho e uma linha por registro AC, na ordem em que chegaram.
    rumo_origem diz se o rumo veio do ADS-B ou foi estimado pelo AbaTrack."""
    from datetime import datetime

    def hora(epoch):
        try:
            return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        except (OverflowError, OSError, ValueError, TypeError):
            return ""

    linhas = [CABECALHO_CSV_ADSB]
    for r in registros:
        if r.rumo is None:
            origem = ""
        else:
            origem = "estimado" if r.rumoEstimado else "adsb"
        latencia = r.latencia
        linhas.append((
            r.sessao, r.seq, r.icao24, hora(r.ts),
            "" if r.chegada is None else hora(r.chegada),
            r.latitude, r.longitude,
            r.altitudeFt, round(r.altitudeFt * 0.3048, 1),
            r.velocidadeKt, round(r.velocidadeKt * 1.852, 1),
            "" if r.rumo is None else round(r.rumo, 1), origem,
            "" if latencia is None else round(latencia, 3),
        ))
    return linhas


def registrarPosicaoMissao_useCase(icao24, latitude, longitude, altitudeFt,
                                   repositorio: RepositorioTelemetria, banco=None, chegada=None,
                                   velocidadeKt=None):
    """Guarda a posicao de uma linha "missão: icao, lat, lon, alt".

    Devolve a PosicaoMissao gravada, ou None se foi ignorada por ja estar salva:
    a mesma posicao que acabou de chegar como ORANGE:AC (a base imprime as duas
    linhas para cada aeronave) ou uma posicao repetida da mesma aeronave."""
    icao24 = str(icao24).strip().upper()
    atual = repositorio.aeronaves.get(icao24)
    if atual is not None and (atual.latitude, atual.longitude) == (latitude, longitude):
        return None
    anterior = repositorio.ultimasPosicoesMissao.get(icao24)
    if anterior is not None and (anterior.latitude, anterior.longitude) == (latitude, longitude):
        return None

    rumo, estimado = None, False
    if anterior is not None and (abs(latitude - anterior.latitude)
                                 + abs(longitude - anterior.longitude)) >= DESLOCAMENTO_MINIMO_GRAUS:
        rumo = rumoEntre(anterior.latitude, anterior.longitude, latitude, longitude)
        estimado = True

    posicao = PosicaoMissao(time.time() if chegada is None else chegada, icao24,
                            latitude, longitude, int(altitudeFt), rumo, estimado, velocidadeKt)
    repositorio.ultimasPosicoesMissao[icao24] = posicao
    repositorio.posicoesMissao.append(posicao)
    if banco is not None:
        banco.registrarPosicaoMissao(posicao)
    return posicao


CABECALHO_CSV_MISSAO = (
    "chegada_pc", "icao24", "latitude", "longitude", "altitude_ft", "altitude_m",
    "velocidade_kt", "velocidade_kmh", "rumo_graus", "rumo_origem",
)


def linhasCsvPosicoesMissao(posicoes):
    """Cabecalho e uma linha por posicao vinda de "missão:"."""
    from datetime import datetime

    linhas = [CABECALHO_CSV_MISSAO]
    for p in posicoes:
        try:
            hora = datetime.fromtimestamp(p.chegada).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        except (OverflowError, OSError, ValueError, TypeError):
            hora = ""
        linhas.append((
            hora, p.icao24, p.latitude, p.longitude, p.altitudeFt, round(p.altitudeFt * 0.3048, 1),
            "" if p.velocidadeKt is None else round(p.velocidadeKt, 1),
            "" if p.velocidadeKt is None else round(p.velocidadeKt * 1.852, 1),
            "" if p.rumo is None else round(p.rumo, 1),
            "" if p.rumo is None else ("estimado" if p.rumoEstimado else "adsb"),
        ))
    return linhas
