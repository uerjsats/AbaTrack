"""Metricas da missao ADS-B calculadas no solo (HLR-ADS-08 do edital)."""

import math
from collections import defaultdict

# Latencias fora desta faixa indicam relogio do Orange nao acertado (sem TIME) ou
# adiantado em relacao ao PC: ficam fora da conta.
LATENCIA_MINIMA_VALIDA_S = -1.0
LATENCIA_MAXIMA_VALIDA_S = 86400


def _percentil(valores, p):
    if not valores:
        return None
    ordenados = sorted(valores)
    indice = max(0, math.ceil(p * len(ordenados)) - 1)
    return ordenados[indice]


def metricasAdsb(registros):
    """registros: lista de RegistroAeronave (sem duplicados).

    perdidos: lacunas no seq de cada sessao. Vale como perda de radio quando o
    OBC envia todas as linhas; se o OBC enviar so um registro por aeronave por
    janela, o seq tem saltos esperados e a perda deve ser medida por um contador
    de transmissao do OBC.
    """
    esperados = recebidos = 0
    seqPorSessao = defaultdict(set)
    for r in registros:
        seqPorSessao[r.sessao].add(r.seq)
    for seqs in seqPorSessao.values():
        esperados += max(seqs) - min(seqs) + 1
        recebidos += len(seqs)

    latencias, descartadas = [], 0
    for r in registros:
        if r.latencia is None:
            continue
        if not (LATENCIA_MINIMA_VALIDA_S <= r.latencia <= LATENCIA_MAXIMA_VALIDA_S):
            descartadas += 1
        else:
            latencias.append(r.latencia)

    perdidos = esperados - recebidos
    return {
        "registros": len(registros),
        "aeronaves": len({r.icao24 for r in registros}),
        "sessoes": len(seqPorSessao),
        "esperados": esperados,
        "perdidos": perdidos,
        "taxaPerda": (perdidos / esperados) if esperados else None,
        "latenciaMediaS": (sum(latencias) / len(latencias)) if latencias else None,
        "latenciaMaxS": max(latencias) if latencias else None,
        "latenciaP95S": _percentil(latencias, 0.95),
        "latenciasDescartadas": descartadas,
    }
