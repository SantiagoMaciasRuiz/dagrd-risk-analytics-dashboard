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

# Inspeccionar el config de la página misma
print("=== CONFIG DE LA PÁGINA COMUNIDAD ===\n")
page_config = comunidad_section.get('config')
if page_config:
    print(f"Type: {type(page_config)}")
    print(f"Content (primeros 1000 chars): {str(page_config)[:1000]}")
    
    # Intentar parsear si es JSON
    try:
        if isinstance(page_config, str):
            config_obj = json.loads(page_config)
            print(f"\n\nKeys en config: {list(config_obj.keys())}")
            
            # Buscar bookmarks
            if 'bookmarks' in config_obj:
                print(f"\nBookmarks encontrados: {config_obj['bookmarks']}")
    except:
        pass

# Inspeccionar vc[0] en detalle
print("\n\n=== VISUAL CONTAINER 0 - DETALLE ===\n")
vc0 = comunidad_section['visualContainers'][0]
for key, value in vc0.items():
    if isinstance(value, str):
        print(f"{key}: {value[:100] if len(str(value)) > 100 else value}")
    elif isinstance(value, dict):
        print(f"{key}: {{...{len(value)} keys...}}")
    elif isinstance(value, list):
        print(f"{key}: [...{len(value)} items...]")
    else:
        print(f"{key}: {value}")
