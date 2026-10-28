# Abatrack — Software de Telemetria da UERJ SATS
O Abatrack é um software de telemetria desenvolvido pela equipe de Computador de Bordo da UERJ SATS para visualização em tempo real dos dados transmitidos por rádio durante missões de nanossatélites.

 🚀 **Funcionalidades — AbaTrack v1.0.11**
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

- Interface com 3 telas navegáveis por botões
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

Equipe de Computador de Bordo — **UERJ SATS**


