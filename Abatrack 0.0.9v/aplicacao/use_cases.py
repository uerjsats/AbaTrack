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
    # Divide o pacote em partes
    partes = pacote.split(":")
    
    # Converte cada parte para float, substituindo valores vazios por 0.0
    partes_completas = [float(parte) if parte.strip() else 0.0 for parte in partes]
    
    # Preenche com 0.0 até o tamanho esperado (14 índices, por exemplo)
    while len(partes_completas) < 14:  # Ajuste o número 14 para o tamanho esperado do pacote
        partes_completas.append(0.0)
    
    return partes_completas

def adicionarPacoteRepositorio(pacote, repositorio: RepositorioTelemetria):
    repositorio.pacotesDados.append(pacote)

def filtraSubdado(listaSubdados, indiceSubdado, repositorio: RepositorioTelemetria):
    if repositorio.pacotesDados:
        conjuntoDados = repositorio.pacotesDados[-1]
        dado = conjuntoDados[indiceSubdado]
        listaSubdados.append(dado)

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
            file.write(f"{pacote[0]}°C  {pacote[1]}s  {pacote[2]}Pa  {pacote[3]}m  latitude:{pacote[4]}  longitude:{pacote[5]}  n° de sats:{pacote[6]}  giro x:{pacote[7]}  giro y:{pacote[8]}  giro z:{pacote[9]}  n° de pacotes:{pacote[10]}  RSSI:{pacote[11]} dBm  tamanho do pacote:{pacote[12]}\n")
    print("Histórico salvo no TXT")