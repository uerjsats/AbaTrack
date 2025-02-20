import os
import simplekml

# Caminho para a pasta de saída
output_dir = "../saida"
os.makedirs(output_dir, exist_ok=True)  # Cria a pasta se ela não existir

# Criar um objeto KML
kml = simplekml.Kml()

# Adicionar pontos ao KML
kml.newpoint(name="São Paulo", coords=[(-46.6333, -23.5500)])
kml.newpoint(name="Rio de Janeiro", coords=[(-43.1729, -22.9068)])

# Salvar o arquivo KML na pasta 'saida'
output_path = os.path.join(output_dir, "pontos.kml")
kml.save(output_path)
print(f"Arquivo KML salvo em: {output_path}")