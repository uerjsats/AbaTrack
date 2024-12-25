import streamlit as st
import pydeck as pdk

class Mapa:
    def __init__(self):
        self.deck = None

    def criar_mapa(self, coordenadas):
        # Criar a camada do Pydeck
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=[coordenadas],
            get_position="[longitude, latitude]",
            get_color="[200, 30, 0, 160]",
            get_radius=50000,
        )

        # Configurar a visão inicial
        view_state = pdk.ViewState(
            latitude=coordenadas["latitude"],
            longitude=coordenadas["longitude"],
            zoom=2,
            pitch=0,
        )

        # Criar o objeto Deck
        self.deck = pdk.Deck(layers=[layer], initial_view_state=view_state)

        # Retornar o mapa para o Streamlit
        return st.pydeck_chart(self.deck)

    def atualizar_mapa(self, coordenadas, mapa):
        # Atualizar a camada com novos dados
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=[coordenadas],
            get_position="[longitude, latitude]",
            get_color="[200, 30, 0, 160]",
            get_radius=50000,
        )

        # Atualizar a visão
        self.deck.layers = [layer]
        self.deck.initial_view_state.latitude = coordenadas["latitude"]
        self.deck.initial_view_state.longitude = coordenadas["longitude"]

        # Atualizar o mapa no Streamlit
        mapa.pydeck_chart(self.deck)
