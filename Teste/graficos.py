import streamlit as st
import pandas as pd
import plotly.express as px

class Graficos:
    @staticmethod
    def criar_grafico_linha(titulo, dados, x, y):
        fig = px.line(dados, x=x, y=y, title=titulo)
        st.plotly_chart(fig)



