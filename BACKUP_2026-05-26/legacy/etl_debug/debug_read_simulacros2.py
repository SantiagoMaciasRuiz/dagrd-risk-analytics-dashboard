#!/usr/bin/env python3
"""ETL: Leer Simulacros correctamente con encabezado en fila 1"""

import pandas as pd
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

print(f"Leyendo Simulacros con encabezado en fila 0...")

# Leer con header en la primera fila
df = pd.read_excel(REPORT_FILE, sheet_name="Simulacros", header=0)

print(f"Dimensiones: {df.shape}")
print(f"Columnas: {list(df.columns)}")
print(f"Tipos de datos:\n{df.dtypes}")
print(f"\nPrimeras filas:\n{df.head()}")
print(f"\nÚltimas filas:\n{df.tail()}")
