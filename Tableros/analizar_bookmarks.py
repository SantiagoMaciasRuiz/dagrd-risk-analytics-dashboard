import json
import sys

# Leer el archivo Layout
try:
    with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-8') as f:
        layout_data = json.load(f)
except UnicodeDecodeError:
    with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-16-le') as f:
        layout_data = json.load(f)

# Mostrar la estructura básica
print("=== ESTRUCTURA GENERAL ===")
print(f"Claves disponibles: {list(layout_data.keys())}\n")

# Buscar páginas
if 'sections' in layout_data:
    print(f"Total de páginas: {len(layout_data['sections'])}\n")
    for i, section in enumerate(layout_data['sections']):
        print(f"Página {i}: '{section.get('displayName', 'SIN NOMBRE')}'")
        if 'bookmarks' in section:
            bookmarks = section.get('bookmarks', [])
            print(f"  - Cantidad de bookmarks: {len(bookmarks)}")
            if len(bookmarks) > 0:
                for b in bookmarks:
                    print(f"    * {b.get('name', 'SIN NOMBRE')}")
        print()
