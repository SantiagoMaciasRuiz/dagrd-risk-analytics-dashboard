import json

with open(r'_pbix_extract_temp\DiagramLayout', 'r', encoding='utf-16-le') as f:
    diagram_data = json.load(f)

print("=== DIAGRAM LAYOUT ===\n")
print(f"Keys: {list(diagram_data.keys())}\n")

# Buscar información sobre bookmarks
if 'diagrams' in diagram_data:
    print(f"Diagrams: {len(diagram_data['diagrams'])}")
    for i, diagram in enumerate(diagram_data['diagrams'][:3]):
        print(f"\n  Diagram {i}:")
        print(f"    Keys: {list(diagram.keys())}")

# Búsqueda recursiva de bookmarks
def find_bookmarks(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if 'bookmark' in str(key).lower():
                results.append(f"{path}.{key}")
            results.extend(find_bookmarks(value, path + f".{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(find_bookmarks(item, path + f"[{i}]"))
    return results

bookmark_paths = find_bookmarks(diagram_data)
if bookmark_paths:
    print(f"\n\nEncontrado 'bookmark' en: {bookmark_paths}")
else:
    print("\n\nNo se encontraron referencias a 'bookmark' en DiagramLayout")
