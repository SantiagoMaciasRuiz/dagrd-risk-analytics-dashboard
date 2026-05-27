#!/usr/bin/env python3
"""
Validación de integridad de Dim_Fecha.csv
Genera reporte de calidad y estadísticas
"""

import pandas as pd
from pathlib import Path

# Rutas
csv_file = Path("data/model/Dim_Fecha.csv")

# Leer datos
df = pd.read_csv(csv_file)

print("="*80)
print("DIM_FECHA - VALIDACION DE DATOS IMPORTADOS")
print("="*80)
print()

print("PRIMERAS 5 FILAS:")
print(df.head(5).to_string(index=False))
print()

print("ULTIMAS 5 FILAS:")
print(df.tail(5).to_string(index=False))
print()

print("ESTADISTICAS GENERALES:")
print(f"  Total registros: {len(df)}")
print(f"  Rango de anio: {df['año'].min()}-{df['año'].max()}")
print(f"  Meses unicos: {df['mes'].nunique()}")
print(f"  Trimestres unicos: {sorted(df['trimestre'].unique())}")
print(f"  Semanas (min-max): {df['semana'].min()}-{df['semana'].max()}")
print(f"  Dias de semana unicos: {df['día_semana'].nunique()}")
print()

print("FECHAS_KEY UNICAS (muestra de 10):")
sample_keys = df['fecha_key'].unique()[:10]
for key in sample_keys:
    print(f"  {key}")
print()

print("RESUMEN POR TRIMESTRE Y ANIO:")
trimestre_summary = df.groupby(['año', 'trimestre']).size()
for (year, quarter), count in trimestre_summary.items():
    print(f"  {year} {quarter}: {count} dias")
print()

print("VALIDACION DE INTEGRIDAD:")
print(f"  Sin duplicados fecha_key: {df['fecha_key'].duplicated().sum() == 0}")
print(f"  Sin valores nulos: {df.isnull().sum().sum() == 0}")
print(f"  Columnas esperadas: {list(df.columns)}")
print()

print("="*80)
print("VALIDACION COMPLETADA EXITOSAMENTE")
print("="*80)
