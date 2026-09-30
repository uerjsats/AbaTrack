import subprocess
import sys

# Lista de pacotes que devem ser instalados via pip
PACKAGES = [
    "PyQt5==5.15.11",
    "PyQtWebEngine==5.15.7",
    "folium==0.19.5",
    "numpy==2.5.3",
    "Pillow==11.1.0",
    "pyqtgraph==0.13.7",
    "PyOpenGL==3.1.9",
    "pyserial==3.5",
    "matplotlib==3.10.0",
    "mplcursors==0.6",
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
