#!/usr/bin/env python3
"""ETL Simplificado: Usar openpyxl para todos los sheets, especialmente Simulacros"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

print(f"Probando lectura de Simulacros con openpyxl...")

# Leer todas las hojas para verificar
excel_file = pd.ExcelFile(REPORT_FILE, engine='openpyxl')
print(f"\nHojas disponibles: {excel_file.sheet_names}")

# Leer Simulacros sin header automatizado
df_raw = pd.read_excel(REPORT_FILE, sheet_name="Simulacros", header=None, engine='openpyxl')
print(f"\nDimensiones raw: {df_raw.shape}")

# Eliminar filas completamente vacías
df_clean = df_raw.dropna(how='all')
print(f"Dimensiones después de eliminar vacías: {df_clean.shape}")

# Usar fila 0 como header
df_clean.columns = df_clean.iloc[0]
df_clean = df_clean.iloc[1:].reset_index(drop=True)

print(f"\nDimensiones finales: {df_clean.shape}")
print(f"Columnas: {list(df_clean.columns)}")
print(f"\nPrimeras 2 filas:")
print(df_clean.head(2))
print(f"\nÚltimas 2 filas:")
print(df_clean.tail(2))

# Contar valores válidos por columna
print(f"\nValores por columna:")
for col in df_clean.columns:
    non_null = df_clean[col].notna().sum()
    print(f"  {col}: {non_null} valores")
