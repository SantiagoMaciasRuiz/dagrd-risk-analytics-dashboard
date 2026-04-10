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

print("=== PÁGINA COMUNIDAD ===\n")
print(f"Nombre: {comunidad_section.get('displayName')}")
print(f"ID: {comunidad_section.get('name')}\n")

bookmarks = comunidad_section.get('bookmarks', [])
print(f"Total de bookmarks: {len(bookmarks)}\n")

if len(bookmarks) > 0:
    for i, bookmark in enumerate(bookmarks):
        print(f"\n{'='*80}")
        print(f"BOOKMARK {i+1}")
        print(f"{'='*80}")
        print(f"Nombre (name): {bookmark.get('name')}")
        print(f"Nombre mostrado (displayName): {bookmark.get('displayName')}")
        print(f"\nContenido del bookmark:")
        
        # Imprimir toda la estructura del bookmark como JSON para inspección
        print(json.dumps(bookmark, indent=2, ensure_ascii=False)[:2000])
        print("\n[... más contenido ...]")
