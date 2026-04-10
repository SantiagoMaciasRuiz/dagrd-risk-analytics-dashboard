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

print("=== VISUAL CONTAINERS EN COMUNIDAD ===\n")
visual_containers = comunidad_section.get('visualContainers', [])
print(f"Total de visual containers: {len(visual_containers)}\n")

# Analizar cada visual container
for i, vc in enumerate(visual_containers):
    print(f"Visual Container {i}:")
    print(f"  - name: {vc.get('name')}")
    print(f"  - type: {vc.get('type')}")
    print(f"  - claves: {list(vc.keys())}")
    
    # Buscar config o visualSettings
    if 'config' in vc:
        config = vc['config']
        if isinstance(config, dict):
            print(f"  - config keys: {list(config.keys())}")
    
    if 'visualSettings' in vc:
        print(f"  - tiene visualSettings")
    
    # Inspeccionar un poco el contenido
    if 'objects' in vc and vc['objects']:
        print(f"  - objects: {list(vc['objects'].keys())}")
    
    print()

# Buscar "bookmark" en todo el layout
print("\n=== BÚSQUEDA GLOBAL DE BOOKMARK ===\n")
def find_all_bookmarks(obj, depth=0):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if 'bookmark' in key.lower() or (isinstance(value, str) and 'bookmark' in value.lower()):
                results.append((key, type(value).__name__))
            results.extend(find_all_bookmarks(value, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_all_bookmarks(item, depth + 1))
    return results

bookmarks_found = find_all_bookmarks(layout_data)
if bookmarks_found:
    for key, type_name in set(bookmarks_found):
        print(f"Encontrado: {key} ({type_name})")
else:
    print("No se encontraron referencias a 'bookmark' en el layout")

# Buscar en el nivel principal del layout
print(f"\n\n=== CLAVES PRINCIPALES DEL LAYOUT ===\n")
print(f"Claves: {list(layout_data.keys())}")

if 'pods' in layout_data and layout_data['pods']:
    print(f"\n'pods' contiene {len(layout_data['pods'])} elementos")
    if len(layout_data['pods']) > 0:
        first_pod = layout_data['pods'][0]
        print(f"Claves del primer pod: {list(first_pod.keys())}")
