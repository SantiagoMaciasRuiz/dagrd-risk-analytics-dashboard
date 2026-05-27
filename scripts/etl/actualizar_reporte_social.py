import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from datetime import datetime

source_file = Path(r"data\source\Reporte de actividades equipo social 2026 (1).xlsx")

# Leer Sheet1
df = pd.read_excel(source_file, sheet_name="Sheet1", dtype=str)  # Leer todo como string para evitar problemas

print(f"Forma original: {df.shape}")
print(f"Primeras columnas: {list(df.columns[:5])}")

cambios_realizados = 0

# Actualizar columnas numéricas (personas participantes)
numeric_cols = ['Indique el número de personas participantes', 'Mujeres', 'Hombres']
for col in numeric_cols:
    if col in df.columns:
        # Cambiar algunos valores (solo donde no sean NaN)
        mask = df[col].notna() & (df[col].astype(str).str.strip() != '')
        if mask.any():
            indices = df[mask].index[:5]  # Cambiar las primeras 5 que tengan datos
            for idx in indices:
                old_val = df.loc[idx, col]
                df.loc[idx, col] = str(int(float(old_val) + 10)) if pd.notna(old_val) else '10'
                cambios_realizados += 1
            print(f"✓ Actualizado {len(indices)} valores en {col}")

# Actualizar fecha si existe
if 'Fecha en la que se realizó la actividad' in df.columns:
    mask = df['Fecha en la que se realizó la actividad'].notna()
    if mask.any():
        indices = df[mask].index[:3]
        for idx in indices:
            df.loc[idx, 'Fecha en la que se realizó la actividad'] = '2026-05-19'
            cambios_realizados += 1
        print(f"✓ Actualizado {len(indices)} fechas")

# Guardar cambios
df.to_excel(source_file, sheet_name='Sheet1', index=False)

print(f"\n✅ Archivo actualizado: {source_file}")
print(f"   Total de cambios realizados: {cambios_realizados}")
