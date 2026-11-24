"""Temperatura da bateria a partir dos dois sensores (sem dependencia de Qt)."""

import math

# Valor que o sensor de temperatura manda quando esta desconectado ou falhou.
TEMPERATURA_SENSOR_INVALIDA = -127.0


def sensorValido(temperatura) -> bool:
    """False se o sensor mandou -127 (falha), nao e um numero ou esta ausente."""
    if temperatura is None:
        return False
    try:
        valor = float(temperatura)
    except (TypeError, ValueError):
        return False
    return math.isfinite(valor) and abs(valor - TEMPERATURA_SENSOR_INVALIDA) >= 0.5


def temperaturaBateriaMedia(temperatura1, temperatura2):
    """Media dos dois sensores. Se um deles esta invalido (-127), usa so o outro.
    Devolve None quando os dois estao invalidos."""
    validas = [float(t) for t in (temperatura1, temperatura2) if sensorValido(t)]
    if not validas:
        return None
    return sum(validas) / len(validas)


def registrarMediaBateria_useCase(repositorio):
    """Calcula a media do ultimo pacote e a guarda em repositorio.tempbateriaMedia.
    Devolve a media, ou None se nenhum sensor era valido (nada e guardado)."""
    if not repositorio.tempbateria1 or not repositorio.tempbateria2:
        return None
    media = temperaturaBateriaMedia(repositorio.tempbateria1[-1], repositorio.tempbateria2[-1])
    if media is not None:
        repositorio.tempbateriaMedia.append(media)
    return media
