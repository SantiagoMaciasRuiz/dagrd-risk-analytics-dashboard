#!/usr/bin/env python3
"""ETL: Leer Simulacros - fila de encabezado está en segunda fila"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

print(f"Leyendo Simulacros...")

# Leer sin header
df = pd.read_excel(REPORT_FILE, sheet_name="Simulacros", header=None)

print(f"Dimensiones originales: {df.shape}")
print(f"Primeras 3 filas (índices 0,1,2):\n{df.head(3)}")

# El encabezado está en la fila con índice 0 (primera data row)
# Primero eliminar filas vacías al inicio
df = df.dropna(how='all')
df = df.reset_index(drop=True)

print(f"\nDespués de eliminar filas vacías:")
print(f"Dimensiones: {df.shape}")
print(f"Primeras 3 filas:\n{df.head(3)}")

# Usar primera fila como encabezado
df.columns = df.iloc[0]
df = df.iloc[1:].reset_index(drop=True)

print(f"\nDespués de asignar encabezado:")
print(f"Dimensiones: {df.shape}")
print(f"Columnas: {list(df.columns)}")
print(f"Primeras filas:\n{df.head()}")
