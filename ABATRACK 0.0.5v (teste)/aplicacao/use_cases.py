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
    return listaPacotes

def adicionarPacoteRepositorio(pacote, repositorio: RepositorioTelemetria):
    repositorio.pacotesDados.append(pacote)
    repositorio.quantidadedepacotedados += 1

def filtraSubdado(listaSubdados, indiceSubdado, repositorio: RepositorioTelemetria):
    # Limpa a lista para evitar acúmulo de dados anteriores
    listaSubdados.clear()
    for pacote in repositorio.pacotesDados:
        if len(pacote) > indiceSubdado:
            listaSubdados.append(pacote[indiceSubdado])
        else:
            print(f"Pacote sem índice {indiceSubdado}: {pacote}")

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
            file.write(f"{pacote}°C\n")
    print("Histórico salvo no TXT")