#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ruta del modelo
BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
MODELO = BASE / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"

# Leer la hoja Hecho_Personas_Atendidas_Ordinario
df = pd.read_excel(MODELO, sheet_name='Hecho_Personas_Atendidas_Ordinario')

# Verificar si ya tiene fecha_date
if 'fecha_date' in df.columns:
    print("✓ Ya tiene fecha_date")
else:
    # Agregar columna con fecha predeterminada (mitad del período 2025-01-01 a 2026-01-31)
    df['fecha_date'] = pd.to_datetime('2025-07-01')
    print("✓ Agregada columna fecha_date = 2025-07-01 para todos los registros")

print(f"Shape: {df.shape}")
print(f"Columnas ({len(df.columns)}): {list(df.columns)}")
print(f"Últimas 3 columnas: {list(df.columns[-3:])}")

# Guardar de vuelta a Excel
with pd.ExcelWriter(MODELO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='Hecho_Personas_Atendidas_Ordinario', index=False)
    
print("✓ Guardado en Excel")
