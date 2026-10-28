import os
import shutil
import subprocess
import sys

# Defina a versão desejada para a build aqui:
VERSION = "1.2.1"  
APP_NAME = f"AbaTrack_v{VERSION}"
MAIN_SCRIPT = "abatrack.py"
ICON_PATH = os.path.join("imgs", "AbaTrack.ico")

# Pastas extras a serem incluídas: (origem, destino)
DATA_FOLDERS = [
    ("imgs", "imgs"),
    ("UI", "UI"),
    ("Leaflet", "Leaflet"),
]

def build():
    separator = ";" if os.name == "nt" else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",  # Equivalente a console=False
        f"--name={APP_NAME}",
    ]

    if os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])

    for src, dst in DATA_FOLDERS:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{separator}{dst}"])
        else:
            print(f"[AVISO] Pasta não encontrada: {src}")

    cmd.append(MAIN_SCRIPT)

    print(f"[*] Iniciando build para {APP_NAME}...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n[SUCESSO] Executável gerado na pasta dist/{APP_NAME}.exe")
    else:
        print(f"\n[ERRO] Falha no processo de build.")

if __name__ == "__main__":
    build()