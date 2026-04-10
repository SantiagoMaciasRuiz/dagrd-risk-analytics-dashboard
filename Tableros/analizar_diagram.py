import json

# Leer el archivo DiagramLayout
try:
    with open(r'_pbix_extract_temp\DiagramLayout', 'r', encoding='utf-8') as f:
        diagram_data = json.load(f)
except UnicodeDecodeError:
    try:
        with open(r'_pbix_extract_temp\DiagramLayout', 'r', encoding='utf-16-le') as f:
            diagram_data = json.load(f)
    except:
        print("No se pudo leer DiagramLayout")
        exit(1)

print("=== DIAGRAM LAYOUT ===\n")
print(f"Keys: {list(diagram_data.keys())}")

# Buscar bookmarks en el DiagramLayout
def search_for_key(obj, target_key, path=""):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() == target_key.lower():
                results.append((path + "." + key, value))
            results.extend(search_for_key(value, target_key, path + "." + key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(search_for_key(item, target_key, path + f"[{i}]"))
    return results

bookmark_results = search_for_key(diagram_data, "bookmark")
print(f"\n\nResultados de búsqueda 'bookmark': {len(bookmark_results)}")
for path, value in bookmark_results:
    print(f"\n{path}:")
    print(f"  Type: {type(value)}")
    if isinstance(value, (dict, list)):
        print(f"  Keys/Length: {len(value)}")
    else:
        print(f"  Value: {str(value)[:200]}")

# Listar primeras claves
if diagram_data:
    first_key = list(diagram_data.keys())[0]
    print(f"\n\nPrimer elemento de {first_key}:")
    first_item = diagram_data[first_key]
    if isinstance(first_item, dict):
        print(f"Keys: {list(first_item.keys())}")
    elif isinstance(first_item, list) and len(first_item) > 0:
        print(f"Primer item type: {type(first_item[0])}")
        if isinstance(first_item[0], dict):
            print(f"Primer item keys: {list(first_item[0].keys())}")
