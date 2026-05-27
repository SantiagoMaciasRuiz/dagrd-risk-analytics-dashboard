#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ruta del modelo
BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
MODELO = BASE / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"

# Leer la hoja Hecho_Personas_Atendidas_Ordinario
df = pd.read_excel(MODELO, sheet_name='Hecho_Personas_Atendidas_Ordinario')

# Usar la fecha real de atención para que Año/Mes filtren la visual correctamente
if 'FECHA ATENCIÓN' in df.columns:
    df['fecha_date'] = pd.to_datetime(df['FECHA ATENCIÓN'], errors='coerce').dt.date
    print("✓ fecha_date derivada desde FECHA ATENCIÓN")
else:
    raise KeyError("No se encontró la columna 'FECHA ATENCIÓN' en la hoja Personas Atendidas")

print(f"Shape: {df.shape}")
print(f"Columnas ({len(df.columns)}): {list(df.columns)}")
print(f"Últimas 3 columnas: {list(df.columns[-3:])}")

# Guardar de vuelta a Excel
with pd.ExcelWriter(MODELO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='Hecho_Personas_Atendidas_Ordinario', index=False)
    
print("✓ Guardado en Excel")
