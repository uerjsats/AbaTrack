import time
import random
import streamlit as st
from mapa import Mapa  # Supondo que você tenha uma classe Mapa para gerar o mapa

class Coordenadas:
    def get_fixed_coordinates(self):
        # Retorna coordenadas fixas, por exemplo, de um ponto específico
        return {"latitude": -23.5505, "longitude": -46.6333}  # Coordenadas de São Paulo (exemplo)
    
    def gerar_novas_coordenadas(self):
        # Simula o movimento do satélite, alterando aleatoriamente a latitude e longitude
        nova_latitude = -23.5505 + random.uniform(-0.01, 0.01)  # Simula movimentação na latitude
        nova_longitude = -46.6333 + random.uniform(-0.01, 0.01)  # Simula movimentação na longitude
        return {"latitude": nova_latitude, "longitude": nova_longitude}



