import subprocess
import sys

# Lista de pacotes que devem ser instalados via pip
PACKAGES = [
    "PyQt5",
    "PyQtWebEngine",
    "folium",
    "numpy",
    "Pillow",
    "pyqtgraph",
    "PyOpenGL",
    "pyserial",
    "matplotlib",
    "mplcursors",
]

def install_packages():
    print("🚀 Verificando e instalando dependências do AbaTrack...\n")
    
    # Atualiza o pip primeiro
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Instala o pacote completo de dependências
    cmd = [sys.executable, "-m", "pip", "install"] + PACKAGES
    try:
        subprocess.check_call(cmd)
        print("\n✅ Todas as dependências foram instaladas com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ocorreu um erro ao instalar as dependências: {e}")

if __name__ == "__main__":
    install_packages()
