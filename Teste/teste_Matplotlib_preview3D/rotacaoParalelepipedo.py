import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation

def criar_paralelepipedo(centro, dimensoes):
    x, y, z = centro
    base, altura = dimensoes
    vertices = np.array([
        [x-base/2, y-base/2, z-altura/2],
        [x+base/2, y-base/2, z-altura/2],
        [x+base/2, y+base/2, z-altura/2],
        [x-base/2, y+base/2, z-altura/2],
        [x-base/2, y-base/2, z+altura/2],
        [x+base/2, y-base/2, z+altura/2],
        [x+base/2, y+base/2, z+altura/2],
        [x-base/2, y+base/2, z+altura/2],
    ])
    return vertices

def rotacionar(vertices, angulo, eixo):
    if eixo == "x":
        matriz_rotacao = np.array([
            [1, 0, 0],
            [0, np.cos(angulo), -np.sin(angulo)],
            [0, np.sin(angulo), np.cos(angulo)],
        ])
    elif eixo == "y":
        matriz_rotacao = np.array([
            [np.cos(angulo), 0, np.sin(angulo)],
            [0, 1, 0],
            [-np.sin(angulo), 0, np.cos(angulo)],
        ])
    elif eixo == "z":
        matriz_rotacao = np.array([
            [np.cos(angulo), -np.sin(angulo), 0],
            [np.sin(angulo), np.cos(angulo), 0],
            [0, 0, 1],
        ])
    vertices_rotacionados = vertices @ matriz_rotacao.T
    return vertices_rotacionados

def desenhar_paralelepipedo(ax, vertices):
    ax.clear()
    ax.set_xlim([-2, 2])
    ax.set_ylim([-2, 2])
    ax.set_zlim([-2, 2])
    ax.set_box_aspect([1, 1, 1])
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[1], vertices[2], vertices[6], vertices[5]],
        [vertices[4], vertices[7], vertices[3], vertices[0]],
    ]
    for face in faces:
        face_3d = Poly3DCollection([face], alpha=0.5, edgecolor="k")
        ax.add_collection3d(face_3d)

figura = plt.figure()
grafico = figura.add_subplot(111, projection="3d")

centro = [0, 0, 0]
dimensoes = [1, 2]
vertices = criar_paralelepipedo(centro, dimensoes)
angulo = 0

def atualizar_quadro(frame):
    global vertices, angulo
    angulo += 0.1
    vertices_rotacionados = rotacionar(vertices - centro, angulo, eixo="y") + centro
    desenhar_paralelepipedo(grafico, vertices_rotacionados)

animacao = FuncAnimation(figura, atualizar_quadro, frames=100, interval=50)

plt.show()
