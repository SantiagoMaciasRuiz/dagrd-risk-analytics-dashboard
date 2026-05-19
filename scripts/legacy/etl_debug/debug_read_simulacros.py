#!/usr/bin/env python3
"""ETL Simplificado: Leer Simulacros con openpyxl"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"
OUTPUT_FILE = BASE / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"

print(f"Archivo input: {REPORT_FILE}")
print(f"Archivo output: {OUTPUT_FILE}")

# Leer archivo actual para no perder datos
try:
    with pd.ExcelFile(REPORT_FILE) as xls:
        sheet_names = xls.sheet_names
        print(f"Hojas disponibles en source: {sheet_names}")
        
        # Intentar leer Simulacros
        for sheet_candidate in ["Simulacros", "Tablas dinámicas"]:
            if sheet_candidate in sheet_names:
                print(f"\nLeyendo hoja '{sheet_candidate}'...")
                df = pd.read_excel(REPORT_FILE, sheet_name=sheet_candidate)
                print(f"  Dimensiones: {df.shape}")
                print(f"  Columnas: {list(df.columns)}")
                print(f"  Primeras filas:\n{df.head()}")
                break
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
