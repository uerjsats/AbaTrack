# Abatrack — Software de Telemetria da UERJ SATS
O Abatrack é um software de telemetria desenvolvido pela equipe de Computador de Bordo da UERJ SATS para visualização em tempo real dos dados transmitidos por rádio durante missões de nanossatélites.

 🚀 **Funcionalidades — AbaTrack v1.2.2**
 ---

## 📊 Visualização de Dados em Tempo Real

### Tela 1 — Gráficos
- Gráfico **Temperatura × Tempo** (dinâmico)
- Gráfico **Pressão × Tempo** (dinâmico)
- Gráfico **Altitude × Tempo** (dinâmico)
  
<img width="1532" height="812" alt="image" src="https://github.com/user-attachments/assets/ff906760-d379-4182-b0d2-46737f2e5c93" />


### Tela 2 — GPS e Mapa
- Visualização de dados GPS (latitude, longitude, número de satélites)
- Mapa interativo offline com marcador de posição em tempo real
- Múltiplos mapas disponíveis:
  - Teste de Voo  2025
  - IREC  2025
  - CubeDesign (INPE)
 
<img width="1523" height="808" alt="image" src="https://github.com/user-attachments/assets/de9cfa1e-eafc-4ae0-89c9-e69cafac81fd" />


### Tela 3 — Visualização 3D
- Cubo 3D que rotaciona conforme dados do giroscópio:
  - Roll
  - Pitch
  - Yaw
- Ângulo do LDR exibido junto aos dados de giro
- Visualização dos dados de giro em tempo real

<img width="1527" height="811" alt="image" src="https://github.com/user-attachments/assets/dc2a018c-b629-4722-a29a-4435f60220d0" />


### Tela 5: Imagens recebidas
- Recebe as imagens JPEG enviadas pela estação de solo na **mesma porta serial** da telemetria, sem precisar de outro programa
- Barra de progresso durante o recebimento e histórico das imagens da sessão (com miniaturas)
- Tratamento da imagem: um botão de girar 90° a cada clique, como numa galeria (clique duas vezes para corrigir foto de cabeça para baixo), auto-contraste, negativo, brilho e contraste. A rotação vale para todas as imagens até clicar em Restaurar, e o arquivo original salvo não muda
- Salvar a imagem original (.jpg, exatamente como chegou) ou a tratada (.png)
- Cada imagem recebida também é gravada automaticamente em `dados_salvos/imagens/` (ao lado do executável)
- As imagens ficam no repositório de telemetria junto com o índice do último pacote recebido, então a aba mostra tempo, altitude e posição do momento em que a imagem chegou
- Missão secundária: a aeronave clandestina aparece na linha de informações da imagem, com a latitude e a longitude do ADS-B

Protocolo esperado na serial (o JPEG é lido por contagem de bytes, então qualquer byte dentro dele é aceito):
```
IMAGE_BEGIN
SIZE:<n>
<n bytes crus do JPEG>
IMAGE_END
```

A telemetria em texto (19 campos) pode vir intercalada com as imagens. O AbaTrack separa os dois sozinho, então basta conectar na COM da Heltec, sem programas extras nem portas virtuais.

### Missão ADS-B: dados do Orange Pi

O Orange Pi decodifica o ADS-B a bordo e manda as mensagens ao OBC. O OBC as repassa pelo LoRa e a base imprime cada uma na serial com o prefixo `ORANGE:`. O AbaTrack separa essas linhas da telemetria de sensor, guarda o estado e o rastro de cada aeronave e grava tudo num banco SQLite.

| Linha | Formato | O que o AbaTrack faz |
|-------|---------|----------------------|
| Aeronave | `ORANGE:AC,<seq>,<ts>,<icao24>,<lat>,<lon>,<alt_ft>,<gs_kt>[,<rumo>]` | guarda a posição, o rastro (últimas 120 posições) e o rumo; sem rumo, calcula entre duas posições |
| Estado do Orange | `ORANGE:STATUS,<estado>,<modo>,<uptime_s>,<temp_cpu_C>,<msgs_rx>,<msgs_validas>,<aeronaves>,<ac_enviados>,<lat_media_ms>,<lat_max_ms>[,<descartados_fila>,<descartados_tx>,<msgs_ident>,<msgs_pos>,<msgs_vel>,<relogio_ok>]` | guarda o último e todos no banco |
| Estado do OBC | `ORANGE:OPSTATE,<estado>,<auto>,<concluida>,<ac_rx>,<ac_perdidos>,<linhas_ok>,<linhas_invalidas>` | idem |
| Eventos e confirmações | `ORANGE:EVT,<tipo>[,...]`, `ORANGE:ACK,<comando>[,...]`, `ORANGE:NAK,<comando>[,<motivo>]` | guarda; o `ACK,START,<n>` define a sessão |
| Aeronave clandestina | `ORANGE:VEREDITO,CLANDESTINA,<lat>,<lon>` | grava no banco e mostra latitude e longitude na linha de informações da foto |

Qualquer outra linha `ORANGE:` é guardada no banco sem tratamento, e linhas malformadas são guardadas como inválidas, sem travar o programa. O formato antigo `DET,<foto>,<lat>,<lon>` (só clandestinas) continua aceito.

Como o AbaTrack liga o veredito à foto:
- O OBC só envia aeronaves clandestinas (e a foto delas) no CubeDesign 2026, então `CLANDESTINA` é o único veredito aceito. Qualquer outro fica no banco como linha inválida.
- O veredito e a foto podem chegar em qualquer ordem. Cada veredito é ligado à foto sem veredito mais antiga que tenha chegado em até 180 segundos de diferença.
- A associação é por ordem e tempo, porque nem o quadro de imagem nem o veredito trazem o número da foto. Se uma foto se perder no rádio, o veredito dela fica na contagem "sem foto" até a janela de tempo passar.

#### Banco de dados do ADS-B

- **Onde:** `dados_salvos/adsb/adsb_AAAA-MM-DD_HH-MM-SS.db`, ao lado do executável. O arquivo é criado quando chega a primeira linha do Orange, então outras missões não geram arquivo vazio.
- **Tabelas:** `aeronaves`, `status_orange`, `opstate`, `eventos`, `confirmacoes`, `vereditos`, `log_cru` e `meta`. O dicionário de dados completo fica em `ESQUEMA_adsb.md`, gravado na mesma pasta.
- **Reprodutível:** a tabela `log_cru` guarda todas as linhas `ORANGE:` exatamente como chegaram, com a hora de chegada no PC, inclusive as malformadas. Dá para refazer qualquer análise a partir dela.
- **Sem duplicados:** a tabela `aeronaves` ignora registros repetidos da mesma sessão e do mesmo `seq`, como os reenviados pelo `DUMP`.
- **Sem travar a leitura:** a gravação roda numa thread própria, em lotes, e o arquivo `.db` já contém os dados durante a missão, então pode ser copiado sem fechar o AbaTrack.
- **Duas horas por registro:** `ts` é a hora do Orange e `chegada` é a hora do PC. A latência de solo é a diferença, e só vale se o relógio do Orange foi acertado com `OP,TIME,<epoch>`.

Exemplo de consulta, o trajeto de uma aeronave:
```
SELECT ts, lat, lon, alt_ft, rumo_graus FROM aeronaves WHERE icao24 = '40621D' ORDER BY ts;
```

As métricas do edital (perda pelas lacunas do `seq` e latência de solo) são calculadas por `aplicacao/metricas_adsb.py`. Se o OBC enviar só um registro por aeronave por janela, o `seq` tem saltos esperados e a perda deve ser medida por um contador de transmissão do OBC.

<img width="1280" height="720" alt="Tela de imagens recebidas" src="https://github.com/user-attachments/assets/ebd6c9be-00a8-4f8c-b22b-b6d6a4ba2069" />


## 📡 Comunicação Serial

- Conexão e desconexão com Arduino via porta serial
- Seleção de porta COM com atualização automática
- Configuração de Baud Rate:
  - 9600  
  - 115200  
- Monitor Serial dedicado para visualização de dados brutos
- Envio de comandos customizados via serial
- Detecção automática de erros de comunicação


## 💾 Salvamento de Dados

### Formatos de Exportação
- **TXT** — Histórico completo de telemetria formatado
- **CSV** — Dados tabulados:
  - Tempo  
  - Temperatura  
  - Pressão  
  - Altitude  
- **PNG** — Salvamento individual dos gráficos:
  - Temperatura  
  - Pressão  
  - Altitude
<img width="529" height="273" alt="Salvamento de dados" src="https://github.com/user-attachments/assets/64bcdc18-82c5-437c-98a3-0e9227c4a19e" />

### Mapas
- Salvar imagem (screenshot) do mapa atual
- Salvar arquivo HTML do mapa atualizado
  
<img width="264" height="190" alt="Sistema de mapa personalizado" src="https://github.com/user-attachments/assets/d38a9d27-c687-452b-9fc6-781ba90e56fa" />


## 📈 Monitoramento

### Painel de Telemetria do Rádio
- Número de pacotes recebidos
- RSSI (intensidade do sinal em dBm)
- Tamanho dos pacotes

### Dados Brutos
- Visualização dos 19 campos de dados recebidos em tempo real

---

## ⚙️ Recursos Adicionais

- Interface com 5 telas navegáveis por botões
- Salvamento automático ao fechar (se houver dados)
- Sistema de notificações toast para feedback ao usuário
- Avisos configuráveis (opção “não mostrar novamente”)
- Design moderno com tema escuro
- Ícones e logo da AbaTrack / AbaSat
- Barra de menu completa com atalhos organizados

## 📡 Dados Recebidos

| Posição | Dado                    | Unidade / Descrição       |
|---------|-------------------------|---------------------------|
| 0       | Tempo                   | s (segundos)              |
| 1       | Temperatura             | °C                        |
| 2       | Umidade                 | %                         |
| 3       | Altitude                | m (metros)                |
| 4       | Pressão                 | Pa (Pascal)               |
| 5       | Latitude                | graus decimais            |
| 6       | Longitude               | graus decimais            |
| 7       | Número de Satélites     | quantidade                |
| 8       | Roll (Giro X)           | graus                     |
| 9       | Pitch (Giro Y)          | graus                     |
| 10      | Yaw (Giro Z)            | graus                     |
| 11      | Ângulo LDR              | graus                     |
| 12      | Temperatura Bateria 1   | °C                        |
| 13      | Temperatura Bateria 2   | °C                        |
| 14      | Tensão                  | V                         |
| 15      | Corrente                | A                         |
| 16      | Número de Pacotes       | quantidade                |
| 17      | RSSI                    | dBm (sinal do rádio)      |
| 18      | Tamanho do Pacote       | bytes                     |

OBS: o pacote de dados tem **19 campos separados por `:`** e tem que estar com as informações nessa ordem (posição 0 a 18).

## ⚙️ Como Usar

1. Conecte o rádio ao computador  
2. Abra o AbaTrack  
3. Selecione a porta COM e a baud rate correspondente  
4. Clique em **Conectar**  
5. Acompanhe os dados em tempo real  
6. Salve os dados (TXT ou CSV)  
7. Salve as imagens dos gráficos ou do mapa
8. Veja e trate as imagens enviadas pelo satélite na Tela 5 (botão com ícone de foto)

## 🛰️ Aplicação

O AbaTrack é utilizado como software de apoio às missões da **UERJ SATS**, incluindo:

- Ensaios de bancada  
- Testes de integração  
- Campanhas de lançamento  
- Operações em campo  

## 👩‍💻 Desenvolvedores

Projeto desenvolvido em **2025** por:

- **Kataryne Cunha**  
- **Thiago Martins**

Tela de Recepção de imagens via LoRa (2026):
- **Caio Fitipaldi**
- **Asaf Teixeira**
- **Vitor Wilson**

Equipe de Computador de Bordo — **UERJ SATS**


