import json

# Leer el archivo Layout
try:
    with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-8') as f:
        layout_data = json.load(f)
except UnicodeDecodeError:
    with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-16-le') as f:
        layout_data = json.load(f)

# Buscar la página COMUNIDAD
comunidad_section = None
for section in layout_data['sections']:
    if section.get('displayName', '').strip() == 'Comunidad':
        comunidad_section = section
        break

if not comunidad_section:
    print("No se encontró la página COMUNIDAD")
    exit(1)

print("=== ESTRUCTURA DE LA PÁGINA COMUNIDAD ===\n")
print(f"Claves disponibles en la sección: {list(comunidad_section.keys())}\n")

# Mostrar si hay visualElements
if 'visualElements' in comunidad_section:
    print(f"Visual Elements: {len(comunidad_section.get('visualElements', []))}")
    for ve in comunidad_section.get('visualElements', [])[:3]:
        print(f"  - {ve.get('name')}: {ve.get('type')}")

# Mostrar si hay filters o config
if 'filters' in comunidad_section:
    print(f"\nFiltros: {comunidad_section['filters']}")

if 'config' in comunidad_section:
    print(f"\nConfig keys: {list(comunidad_section['config'].keys())}")

# Buscar "bookmark" o similar en toda la estructura
print("\n\n=== BÚSQUEDA DE BOOKMARKS EN LA ESTRUCTURA ===\n")

def search_bookmarks(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if 'bookmark' in key.lower():
                print(f"Encontrado en {path}.{key}: {type(value)}")
            search_bookmarks(value, path + "." + key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            search_bookmarks(item, path + f"[{i}]")

search_bookmarks(comunidad_section)
