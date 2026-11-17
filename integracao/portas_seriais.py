"""Lista das portas COM do computador, sem travar a interface.

No Windows, enumerar as portas pode demorar varios segundos quando um
dispositivo USB novo esta sendo reconhecido. Por isso a lista e consultada
numa thread propria e a interface so recebe um aviso quando ela muda.
"""

import threading
import time

import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal


def listarPortasSerial():
    """Todas as portas COM, inclusive as virtuais do com0com."""
    portas = [porta.device for porta in serial.tools.list_ports.comports()]
    # O com0com 2.x registra as portas virtuais na classe de dispositivo
    # "CNCPorts", que o comports() do pyserial NAO enumera. O registro
    # HKLM\HARDWARE\DEVICEMAP\SERIALCOMM lista TODAS as portas COM (inclusive
    # as virtuais), entao mesclamos as duas fontes.
    try:
        import winreg
        chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"HARDWARE\DEVICEMAP\SERIALCOMM")
        try:
            i = 0
            while True:
                _, valor, _ = winreg.EnumValue(chave, i)
                if valor not in portas:
                    portas.append(valor)
                i += 1
        except OSError:
            pass  # fim da enumeracao
        finally:
            winreg.CloseKey(chave)
    except (OSError, ImportError):
        pass  # sem a chave (ex.: nenhuma porta, ou fora do Windows)
    return portas


class MonitorPortas(QObject):
    """Consulta as portas a cada `intervalo` segundos fora da thread da
    interface e emite `portasMudaram` so quando a lista muda."""

    portasMudaram = pyqtSignal(list)

    def __init__(self, listar=listarPortasSerial, intervalo=1.0, parent=None):
        super().__init__(parent)
        self._listar = listar
        self._intervalo = intervalo
        self._parar = threading.Event()
        self._thread = None
        self._ultima = None

    def iniciar(self):
        if self._thread is None:
            # daemon: se a consulta travar no driver, nao impede o programa de fechar
            self._thread = threading.Thread(target=self._rodar, name="MonitorPortas", daemon=True)
            self._thread.start()

    def parar(self):
        self._parar.set()

    def _rodar(self):
        while not self._parar.is_set():
            try:
                portas = list(self._listar())
            except Exception:
                portas = self._ultima if self._ultima is not None else []
            if portas != self._ultima:
                self._ultima = portas
                self.portasMudaram.emit(portas)
            self._parar.wait(self._intervalo)
