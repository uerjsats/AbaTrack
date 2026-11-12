"""Mensagens do Orange Pi (missao ADS-B) que a base imprime na serial.

O Orange manda ao OBC linhas "2:TIPO,campos"; o OBC tira o "2:" e repassa pelo
LoRa, e a base imprime cada mensagem com o prefixo "ORANGE:":

    ORANGE:AC,<seq>,<ts>,<icao24>,<lat>,<lon>,<alt_ft>,<gs_kt>[,<rumo_graus>]
    ORANGE:STATUS,<estado>,<modo>,<uptime_s>,<temp_cpu_C>,<msgs_rx>,...
    ORANGE:OPSTATE,<estado>,<auto>,<concluida>,<ac_rx>,<ac_perdidos>,...
    ORANGE:EVT,<tipo>[,<campos>]
    ORANGE:ACK,<comando>[,<campos>]   ORANGE:NAK,<comando>[,<motivo>]
    ORANGE:VEREDITO,CLANDESTINA,<lat>,<lon>  (ver aplicacao.deteccao_aeronave)

Este modulo so interpreta texto (sem Qt, sem disco).
"""

import math
import re
import time
from datetime import datetime

from aplicacao.deteccao_aeronave import interpretarVeredito
from dominio.entidades import RegistroAeronave

PREFIXO_ORANGE = "ORANGE:"

# Tipos reconhecidos. Qualquer outro vira "OUTRO" (guardado, mas sem tratamento).
TIPOS_ORANGE = ("AC", "STATUS", "OPSTATE", "EVT", "ACK", "NAK", "VEREDITO")

_ICAO = re.compile(r"^[0-9A-Fa-f]{6}$")

CAMPOS_STATUS = ("estado", "modo", "uptime_s", "temp_cpu_c", "msgs_rx",
                 "msgs_validas", "aeronaves", "ac_enviados", "lat_media_ms",
                 "lat_max_ms")
# Campos que o Orange pode acrescentar no FIM do STATUS (opcionais).
CAMPOS_STATUS_EXTRAS = ("descartados_fila", "descartados_tx", "msgs_ident",
                        "msgs_pos", "msgs_vel", "relogio_ok")
CAMPOS_OPSTATE = ("estado", "auto", "concluida", "ac_rx", "ac_perdidos",
                  "linhas_ok", "linhas_invalidas")


class MensagemOrange:
    """tipo: AC, STATUS, OPSTATE, EVT, ACK, NAK, VEREDITO, OUTRO ou INVALIDA.
    dados: RegistroAeronave (AC), DeteccaoAeronave (VEREDITO) ou dict.
    bruta: a linha como chegou. chegada: epoch do PC quando a linha chegou."""

    def __init__(self, tipo, dados, bruta, chegada):
        self.tipo = tipo
        self.dados = dados
        self.bruta = bruta
        self.chegada = chegada


def ehMensagemOrange(linha: str) -> bool:
    return linha.lstrip().upper().startswith(PREFIXO_ORANGE)


def _inteiro(texto):
    valor = float(texto)
    if not math.isfinite(valor):
        raise ValueError("numero nao finito")
    return int(valor)


def _opcional(conversor, texto):
    return None if texto == "" else conversor(texto)


def _finito(*valores):
    return all(math.isfinite(v) for v in valores)


def _interpretarAC(partes, chegada):
    if len(partes) < 8:
        raise ValueError("AC incompleta")
    seq = int(partes[1])
    ts = float(partes[2])
    icao24 = partes[3].upper()
    if not _ICAO.match(icao24):
        raise ValueError(f"ICAO invalido: {ascii(partes[3][:12])}")
    latitude, longitude = float(partes[4]), float(partes[5])
    if not (_finito(ts, latitude, longitude)
            and -90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("coordenadas ou tempo invalidos")
    altitudeFt, velocidadeKt = _inteiro(partes[6]), _inteiro(partes[7])
    rumo = None
    if len(partes) > 8 and partes[8] != "":
        rumo = float(partes[8])
        if not (math.isfinite(rumo) and 0 <= rumo <= 360):
            raise ValueError("rumo fora do intervalo")
    return RegistroAeronave(seq, ts, icao24, latitude, longitude, altitudeFt,
                            velocidadeKt, rumo, chegada)


def _interpretarStatus(partes):
    dados = {"estado": partes[1].upper() if len(partes) > 1 else ""}
    tipos = (str, int, int, float, int, int, int, int, float, float)
    for nome, conversor, texto in zip(CAMPOS_STATUS[1:], tipos[1:], partes[2:]):
        try:
            dados[nome] = _opcional(conversor, texto)
        except ValueError:
            dados[nome] = None
    for nome, texto in zip(CAMPOS_STATUS_EXTRAS, partes[1 + len(CAMPOS_STATUS):]):
        try:
            dados[nome] = _opcional(_inteiro, texto)
        except ValueError:
            dados[nome] = None
    return dados


def _interpretarOpstate(partes):
    dados = {"estado": partes[1].upper() if len(partes) > 1 else ""}
    for nome, texto in zip(CAMPOS_OPSTATE[1:], partes[2:]):
        try:
            dados[nome] = _opcional(_inteiro, texto)
        except ValueError:
            dados[nome] = None
    return dados


def _interpretarConfirmacao(partes):
    comando = partes[1].upper() if len(partes) > 1 else ""
    dados = {"comando": comando, "args": partes[2:]}
    if comando == "START" and len(partes) > 2:
        try:
            dados["sessao"] = int(partes[2])
        except ValueError:
            pass
    return dados


def interpretarMensagemOrange(linha: str, chegada=None) -> MensagemOrange:
    """Levanta ValueError se a linha for do tipo conhecido mas estiver malformada."""
    chegada = time.time() if chegada is None else chegada
    bruta = linha.strip()
    if not ehMensagemOrange(bruta):
        raise ValueError("a linha nao e do Orange")
    partes = [p.strip() for p in bruta[len(PREFIXO_ORANGE):].split(",")]
    tipo = partes[0].upper()

    if tipo == "AC":
        dados = _interpretarAC(partes, chegada)
    elif tipo == "STATUS":
        dados = _interpretarStatus(partes)
    elif tipo == "OPSTATE":
        dados = _interpretarOpstate(partes)
    elif tipo == "EVT":
        dados = {"tipo": partes[1].upper() if len(partes) > 1 else "",
                 "args": partes[2:]}
    elif tipo in ("ACK", "NAK"):
        dados = _interpretarConfirmacao(partes)
    elif tipo == "VEREDITO":
        dados = interpretarVeredito(partes[1:], datetime.fromtimestamp(chegada))
    else:
        tipo, dados = "OUTRO", {"campos": partes}
    return MensagemOrange(tipo, dados, bruta, chegada)


def lerMensagemOrange(linha: str, chegada=None) -> MensagemOrange:
    """Como interpretarMensagemOrange, mas nunca levanta: linha malformada vira
    tipo INVALIDA (a linha crua continua sendo guardada no banco)."""
    chegada = time.time() if chegada is None else chegada
    try:
        return interpretarMensagemOrange(linha, chegada)
    except ValueError as e:
        return MensagemOrange("INVALIDA", {"erro": str(e)}, linha.strip(), chegada)
