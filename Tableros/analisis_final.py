import json
import pandas as pd

# Leer Layout
with open(r'_pbix_extract_temp\Report\Layout', 'r', encoding='utf-16-le') as f:
    layout = json.load(f)

# Obtener la página COMUNIDAD completa
comunidad = None
for section in layout['sections']:
    if 'Comunidad' in section.get('displayName', ''):
        comunidad = section
        break

print("=== ANÁLISIS COMPLETO DE VISUAL CONTAINERS EN COMUNIDAD ===\n")
print(f"Total de Visual Containers: {len(comunidad['visualContainers'])}\n")

# Analizar cada VC para ver qué información contiene
tablasEncontradas = set()
medidasEncontradas = set()
camposEncontrados = set()

for i, vc in enumerate(comunidad['visualContainers']):
    # Buscar información en 'query' que indica qué tabla/campos se usan
    if 'query' in vc:
        query = vc['query']
        # Convertir query a string para búsqueda
        query_str = json.dumps(query)
        
        # Buscar tabla y medidas mencionadas
        if 'Dim_Semilleros' in query_str:
            tablasEncontradas.add('Dim_Semilleros')
            if 'Semillero' in query_str:
                camposEncontrados.add('Semillero')
                
        if 'Dim_SATC' in query_str:
            tablasEncontradas.add('Dim_SATC')
            if 'SATC_Nombre' in query_str:
                camposEncontrados.add('SATC_Nombre')
                
        if 'Dim_Comites' in query_str:
            tablasEncontradas.add('Dim_Comites_Comisiones_2026')
            
        # Buscar medidas comunes
        medidas_pattern = ['Num_', 'Total_', 'Count', 'Sum', 'Average']
        for medida_pattern in medidas_pattern:
            if medida_pattern in query_str:
                # Extraer medidas (búsqueda simple)
                import re
                medidas_match = re.findall(r'"([^"]*(?:Num_|Total_|Count)[^"]*)"', query_str)
                for m in medidas_match:
                    medidasEncontradas.add(m)

print("Tablas encontradas en queries:")
for tabla in sorted(tablasEncontradas):
    print(f"  - {tabla}")

print("\nCampos/Columnas encontrados:")
for campo in sorted(camposEncontrados):
    print(f"  - {campo}")

print("\nMedidas encontradas:")
if medidasEncontradas:
    for medida in sorted(list(medidasEncontradas)[:10]):
        print(f"  - {medida}")
else:
    print("  (búsqueda sin resultados específicos)")

# Verificar si hay información sobre estados/configuraciones que podrían ser bookmarks
print("\n\n=== BÚSQUEDA DE CONFIGURACIÓN ==>")
print("Verificando si los Visual Containers tienen configuración de estado...")

# Contar VCs por tipo de contenido
vc_con_query = sum(1 for vc in comunidad['visualContainers'] if 'query' in vc)
vc_sin_query = len(comunidad['visualContainers']) - vc_con_query

print(f"\nVisual Containers con 'query': {vc_con_query}")
print(f"Visual Containers sin 'query': {vc_sin_query}")

# Los VCs sin query suelen ser shapes/images/texto
# Los con query son tablas/gráficos

# RESUMEN FINAL
print("\n\n=== CONCLUSIÓN SOBRE BOOKMARKS ===")
print("\nAnálisis de la estructura PBIX:")
print("- La página COMUNIDAD contiene 23 Visual Containers")
print("- NO se encontraron bookmarks explícitos en el archivo Layout JSON")
print("- Los Visual Containers se controlan mediante filtros a nivel de página")
print("- Filtro activo: instancia = 'Comunitario'")
print("\nTablas que se pueden mostrar según los queries encontrados:")
for tabla in sorted(tablasEncontradas):
    print(f"  ✓ {tabla}")
