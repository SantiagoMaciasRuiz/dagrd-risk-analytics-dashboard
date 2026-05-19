#!/usr/bin/env python3
"""Helper: Convertir dataframe openpyxl a formato row_map compatible con ETL"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

# Leer Simulacros
df_raw = pd.read_excel(REPORT_FILE, sheet_name="Simulacros", header=None, engine='openpyxl')
df_clean = df_raw.dropna(how='all')

# Usar fila 0 como header
header_row = df_clean.iloc[0]
df_data = df_clean.iloc[1:].reset_index(drop=True)
df_data.columns = header_row

print(f"DataFrame shape: {df_data.shape}")
print(f"Columns: {list(df_data.columns)}")

# Convertir a formato row_map similar al del ETL
sheet3_rows = []
# Primero agregar la fila de encabezados (row_num=1, header_map)
header_map = {i+1: str(col).strip() for i, col in enumerate(header_row)}
sheet3_rows.append((1, header_map))

# Luego agregar filas de data (row_num=2+, row_map)
for idx, row in df_data.iterrows():
    row_num = idx + 2  # +2 porque: 1=header, +1 for 1-based indexing
    row_map = {}
    for col_idx, value in enumerate(row, 1):  # col_idx starts from 1
        if pd.notna(value):
            str_val = str(value).strip()
            if str_val and str_val.lower() != 'nan':
                row_map[col_idx] = str_val
    if row_map:
        sheet3_rows.append((row_num, row_map))

print(f"\nTotal rows (including header): {len(sheet3_rows)}")
print(f"Row 0 (header): {sheet3_rows[0]}")
print(f"Row 1 (first data): {sheet3_rows[1]}")
print(f"Row 2 (second data): {sheet3_rows[2]}")

# Verificar que se puede encontrar columnas
def _normalize_text(value: str) -> str:
    import unicodedata
    import re
    normalized = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    value = value.lower().strip()
    return re.sub(r"\s+", " ", value)

def _find_col(headers, contains_all):
    for idx, name in headers.items():
        normalized = _normalize_text(name)
        if all(term in normalized for term in contains_all):
            return idx
    raise RuntimeError(f"No se encontró columna para criterio: {contains_all}")

# Probar búsqueda
header_num, header_map = sheet3_rows[0]
try:
    idx_fecha = _find_col(header_map, ["marca temporal"])
    idx_nombre = _find_col(header_map, ["nombre completo"])
    idx_comuna = _find_col(header_map, ["comuna", "pertenece"])
    idx_sector = _find_col(header_map, ["sector pertenece"])
    idx_personas = _find_col(header_map, ["personas", "participaron"])
    print(f"\n✓ Índices encontrados:")
    print(f"  fecha: {idx_fecha}")
    print(f"  nombre: {idx_nombre}")
    print(f"  comuna: {idx_comuna}")
    print(f"  sector: {idx_sector}")
    print(f"  personas: {idx_personas}")
except Exception as e:
    print(f"\n✗ Error encontrando columnas: {e}")

# Verificar primeros datos
print(f"\nPrimera fila de datos:")
row_num, row_map = sheet3_rows[1]
print(f"  row_num: {row_num}")
print(f"  fecha: {row_map.get(idx_fecha)}")
print(f"  nombre: {row_map.get(idx_nombre)}")
print(f"  comuna: {row_map.get(idx_comuna)}")
print(f"  sector: {row_map.get(idx_sector)}")
print(f"  personas: {row_map.get(idx_personas)}")
