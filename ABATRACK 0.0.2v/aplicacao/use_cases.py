from datetime import datetime
from dominio.entidades import RepositorioTelemetria, ConfigsComunicacao

def alterarPortaArduino(configAtual: ConfigsComunicacao, novaPorta: str):
    portaAntiga = configAtual.portaAntiga
    configAtual.portaArduino = novaPorta
    print(f"Porta alterada: {portaAntiga} -> {configAtual.portaArduino}")

def alterarBaudRate(configAtual: ConfigsComunicacao, novoBaudRate: int):
    baudAntiga = configAtual.baudRate
    configAtual.baudRate = int(novoBaudRate)
    print(f"Baud Rate alterada: {baudAntiga} -> {configAtual.baudRate}")

def processarPacoteDeDados(pacote):
    listaPacotes = list(map(float, pacote.split(":")))
    pacoteProcessado = f"Temperatura: {listaPacotes[0]} C Tempo: {listaPacotes[1]}s"

    return pacoteProcessado

def adicionarPacoteRepositorio(pacote, repositorio: RepositorioTelemetria):
    repositorio.pacotesDados.append(pacote)

def printEstadoAtual(repositorio: RepositorioTelemetria, configs: ConfigsComunicacao):
    print(f"\nEstado atual:\nRepositorio: {repositorio}\nConfigs: {configs}")

def salvarDadosTXT(repositorio: RepositorioTelemetria):
    if not repositorio.pacotesDados:
        print("Nenhum dado registrado.")
        return
    dataHoraAtual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nomeArquivo = f"historico_{dataHoraAtual}.txt"

    with open(nomeArquivo, 'w') as file:
        file.write(f"Historico de Telemetria - {dataHoraAtual}\n")
        file.write("-------------------------------\n")

        for pacote in repositorio.pacotesDados:
            pacoteProcessado = processarPacoteDeDados(pacote)
            file.write(f"{pacoteProcessado}\n")
    print("Histórico salvo no TXT")