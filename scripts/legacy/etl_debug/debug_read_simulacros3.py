#!/usr/bin/env python3
"""ETL: Leer Simulacros con primera fila como encabezado"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

print(f"Leyendo Simulacros sin asignación automática de header...")

# Leer sin header
df = pd.read_excel(REPORT_FILE, sheet_name="Simulacros", header=None)

print(f"Dimensiones: {df.shape}")
print(f"Primera fila (encabezados): {list(df.iloc[0])}")

# Usar primera fila como encabezado
df.columns = df.iloc[0]
df = df.iloc[1:].reset_index(drop=True)

print(f"\nDespués de usar fila 0 como encabezado:")
print(f"Dimensiones: {df.shape}")
print(f"Columnas: {list(df.columns)}")
print(f"\nPrimeras filas:\n{df.head()}")
