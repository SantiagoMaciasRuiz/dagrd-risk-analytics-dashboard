import json

# Leer el Layout con todas las páginas
with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-16-le') as f:
    layout = json.load(f)

# Buscar en toda la estructura referencias a "Navigation" que podrían ser bookmarks
def search_deep(obj, keyword="", max_depth=3, current_depth=0):
    """Búsqueda recursiva por palabra clave"""
    results = []
    
    if current_depth > max_depth:
        return results
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if keyword.lower() in key.lower():
                results.append({
                    'key': key,
                    'depth': current_depth,
                    'type': type(value).__name__
                })
            if isinstance(value, (dict, list)):
                results.extend(search_deep(value, keyword, max_depth, current_depth + 1))
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                results.extend(search_deep(item, keyword, max_depth, current_depth + 1))
    
    return results

# Buscar "navigation", "bookmark", "action", "drill"
keywords = ['navigation', 'bookmark', 'action', 'drill',  'page', 'tabular', 'semillero']

print("=== BÚSQUEDA DE PALABRAS CLAVE EN LAYOUT ===\n")
for kw in keywords:
    results = search_deep(layout, kw, max_depth=2)
    if results:
        print(f"Palabra '{kw}': {len(results)} encontrados")
        for r in results[:3]:
            print(f"  - {r}")

# Revisar la página COMUNIDAD en detalle
print("\n\n=== ANÁLISIS DETALLADO DE COMUNIDAD ===\n")
comunidad_section = None
for section in layout['sections']:
    if 'Comunidad' in section.get('displayName', ''):
        comunidad_section = section
        break

if comunidad_section:
    # Contar visualElements
    vc_count = len(comunidad_section.get('visualContainers', []))
    print(f"Visual Containers: {vc_count}")
    
    # Ver si algún VC tiene nombre o información sobre qué mostra
    print("\nPrimeros 5 visual containers:")
    for i, vc in enumerate(comunidad_section.get('visualContainers', [])[:5]):
        config_str = vc.get('config', '')
        if isinstance(config_str, str) and len(config_str) > 50:
            # Intentar extraer información del config
            try:
                config_obj = json.loads(config_str)
                if 'objects' in config_obj:
                    obj_keys = list(config_obj['objects'].keys())
                    print(f"  VC{i}: objects={obj_keys[:3]}")
            except:
                pass
        
        # Ver si tiene query (indica tabla/visual)
        if 'query' in vc:
            query_str = str(vc['query'])[:100]
            print(f"  VC{i}: tiene query")

print("\n\n=== ANÁLISIS DE FILTROS (PUEDEN SER BOOKMARKS) ===\n")

# Ver si hay elementos que podrían modelar bookmarks en los filtros
if 'filters' in comunidad_section:
    print(f"Filtros en la página: {len(comunidad_section['filters'])}")
    for f_idx, f in enumerate(comunidad_section['filters'][:3]):
        print(f"\n  Filtro {f_idx}:")
        print(f"    Nombre: {f.get('name')}")
        print(f"    Type: {f.get('type')}")
