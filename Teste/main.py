import time
from mapa import Mapa
from coordenadas import Coordenadas
from graficos import Graficos
from satelite import Satelite3D
import pandas as pd
import streamlit as st

# Instanciar as classes
mapa = Mapa()
coordenadas = Coordenadas()
satelite = Satelite3D()

# Inicializar o Streamlit
st.title("Sistema de Telemetria")

# Coordenadas iniciais (valores fixos para exibição)
current_coords = coordenadas.get_fixed_coordinates()
map_placeholder = mapa.criar_mapa(current_coords)

# Dados fixos para gráficos
data = pd.DataFrame({
    "Tempo": range(10),
    "Temperatura (°C)": [22, 24, 23, 25, 27, 26, 25, 24, 23, 22],
    "Altitude (km)": [500, 505, 510, 515, 520, 525, 530, 535, 540, 545],
    "Pressão (Pa)": [101325, 101300, 101275, 101250, 101225, 101200, 101175, 101150, 101125, 101100],  # Dados de pressão
})

# Mostrar gráficos
st.header("Gráficos de Dados")
Graficos.criar_grafico_linha("Temperatura", data, x="Tempo", y="Temperatura (°C)")
Graficos.criar_grafico_linha("Altitude", data, x="Tempo", y="Altitude (km)")
Graficos.criar_grafico_linha("Pressão", data, x="Tempo", y="Pressão (Pa)")  # Novo gráfico de pressão

# Atualizar o mapa em tempo real
placeholder = st.empty()
while True:
    # Atualiza as coordenadas
    new_coords = coordenadas.get_simulated_coordinates()
    mapa.atualizar_mapa(new_coords, map_placeholder)
    placeholder.write(f"Coordenadas atuais: {new_coords}")
    time.sleep(2)  # Atualiza a cada 2 segundos

# Carregar o arquivo STL (substitua pelo caminho correto)
stl_file_path = "C:/Users/katar/Downloads/educational-cubesat-1u-1.snapshot.5/ToPrint/p5Tapa1st.stl"  # Substitua pelo seu caminho

# Definir os valores iniciais de rotação
rotacao_inicial = {
    'rotacao_x': 45,  # Exemplo de rotação inicial no eixo X
    'rotacao_y': 90,  # Exemplo de rotação inicial no eixo Y
    'rotacao_z': 180  # Exemplo de rotação inicial no eixo Z
}

# Criar uma variável para os dados de rotação que será alterada no loop
dados_rotacao = rotacao_inicial.copy()

# Criar o satélite com o modelo STL e as rotações definidas
figura_satelite = Satelite3D.criar_satelite_com_stl(stl_file_path, dados_rotacao)

# Exibir o gráfico no Streamlit
if figura_satelite:
    st.plotly_chart(figura_satelite, use_container_width=True)

# Criar um contêiner para exibir o gráfico com rolagem
with st.container():
    # Adicionar uma área de rolagem para o gráfico
    st.markdown(
        """
        <style>
            .stPlotlyChart {
                height: 600px;
                overflow-y: auto;
            }
        </style>
        """, unsafe_allow_html=True)

    # Simulação de rotação contínua
    placeholder = st.empty()
    for i in range(100):  # Exemplo de 100 iterações
        # Aumentar os valores de rotação
        dados_rotacao['rotacao_x'] = (dados_rotacao['rotacao_x'] + 1) % 360
        dados_rotacao['rotacao_y'] = (dados_rotacao['rotacao_y'] + 2) % 360
        dados_rotacao['rotacao_z'] = (dados_rotacao['rotacao_z'] + 3) % 360
        
        # Criar a nova figura com a rotação atualizada
        figura_satelite = Satelite3D.criar_satelite_com_stl(stl_file_path, dados_rotacao)
        
        # Exibir o gráfico
        placeholder.plotly_chart(figura_satelite, use_container_width=True)
        
        # Espera um tempo para atualizar a visualização
        time.sleep(0.1)  # Intervalo de 0.1 segundo entre as atualizações