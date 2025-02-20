from pykml import parser

# Caminho para o arquivo KML na pasta 'dados'
input_kml = "../dados/exemplo.kml"

# Verificar se o arquivo existe
if os.path.exists(input_kml):
    with open(input_kml, "r") as f:
        root = parser.parse(f).getroot()

    # Iterar pelos elementos do KML
    for place in root.Document.Placemark:
        name = place.name.text
        coords = place.Point.coordinates.text.split(',')
        lat, lon = float(coords[1]), float(coords[0])
        print(f"{name}: Latitude={lat}, Longitude={lon}")
else:
    print(f"Arquivo KML não encontrado: {input_kml}")