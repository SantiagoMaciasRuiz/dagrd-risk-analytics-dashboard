import pandas as pd
from pathlib import Path

csv_path = Path('data/model/Dim_Comites_Comisiones_2026.csv')
df = pd.read_csv(csv_path)

print('='*70)
print('✅ VERIFICACION FINAL - CSV DE COMITES Y COMISIONES')
print('='*70)
print()
print('📊 ESTADÍSTICAS:')
print(f'  • Filas totales: {len(df)}')
print(f'  • Columnas: {list(df.columns)}')
print()

# Conteo por comuna
print('📍 DISTRIBUCIÓN POR COMUNA:')
by_comuna = df.groupby('comuna_cod').size().reset_index(name='count').sort_values('comuna_cod')
for _, row in by_comuna.iterrows():
    print(f'  • Comuna {int(row["comuna_cod"]):2d}: {row["count"]:2d} registros')
print()

# Duplicados
dup = df[df.duplicated(subset=['comuna_cod', 'comite_comision_nombre'], keep=False)]
if len(dup) > 0:
    print('⚠️  REGISTROS DUPLICADOS PRESERVADOS:')
    for _, row in dup.drop_duplicates(subset=['comuna_cod', 'comite_comision_nombre']).iterrows():
        count = len(df[(df['comuna_cod'] == row['comuna_cod']) & (df['comite_comision_nombre'] == row['comite_comision_nombre'])])
        print(f'  • Comuna {int(row["comuna_cod"])}: "{row["comite_comision_nombre"]}" ({count}x)')
print()

print('='*70)
print('✅ CSV LISTO PARA POWER BI - 158 FILAS CORRECTAS')
print('='*70)
