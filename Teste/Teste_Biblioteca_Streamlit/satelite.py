import trimesh
import plotly.graph_objects as go
import streamlit as st
import numpy as np


class Satelite3D:
    @staticmethod
    def criar_satelite_com_stl(stl_file_path, dados_rotacao):
        # Carregar o arquivo STL
        mesh = trimesh.load_mesh(stl_file_path)
        
        # Extrair os vértices e faces do modelo
        vertices = mesh.vertices
        faces = mesh.faces
        
        # Obter as rotações a partir do dicionário
        rotacao_x = dados_rotacao.get('rotacao_x', 0)
        rotacao_y = dados_rotacao.get('rotacao_y', 0)
        rotacao_z = dados_rotacao.get('rotacao_z', 0)

        # Criar as matrizes de rotação para X, Y e Z
        rot_x = trimesh.transformations.rotation_matrix(np.radians(rotacao_x), [1, 0, 0])
        rot_y = trimesh.transformations.rotation_matrix(np.radians(rotacao_y), [0, 1, 0])
        rot_z = trimesh.transformations.rotation_matrix(np.radians(rotacao_z), [0, 0, 1])
        
        # Multiplicar as matrizes de rotação para aplicar a rotação total (em ordem Z, Y, X)
        matriz_rotacao = np.dot(np.dot(rot_z, rot_y), rot_x)

        # Aplicar a matriz de rotação nos vértices
        vertices_rotacionados = np.dot(vertices, matriz_rotacao[:3, :3].T) + matriz_rotacao[:3, 3]
        
        # Criar o gráfico 3D com Plotly
        fig = go.Figure(data=[go.Mesh3d(
            x=vertices_rotacionados[:, 0], 
            y=vertices_rotacionados[:, 1], 
            z=vertices_rotacionados[:, 2],
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            opacity=0.5, color='blue'
        )])

        # Atualizar a visualização
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[min(vertices_rotacionados[:, 0]), max(vertices_rotacionados[:, 0])]),
                yaxis=dict(range=[min(vertices_rotacionados[:, 1]), max(vertices_rotacionados[:, 1])]),
                zaxis=dict(range=[min(vertices_rotacionados[:, 2]), max(vertices_rotacionados[:, 2])]),
            ),
            title="Modelo 3D a partir de STL"
        )
        return fig




