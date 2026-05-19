import pandas as pd
from pathlib import Path
import openpyxl

# Paths
csv_path = Path("data/model/Dim_Comites_Comisiones_2026.csv")
excel_path = Path("data/model/Modelo_Reporte_Paginas_2026.xlsx")

print("📋 ACTUALIZAR MODELO CON COMITÉS/COMISIONES")
print("="*80)

# Leer CSV actualizado
print("\n1️⃣ Leyendo CSV actualizado...")
df = pd.read_csv(csv_path)
print(f"   ✓ {len(df)} filas, {df.shape[1]} columnas")

# Cargar el modelo Excel
print("\n2️⃣ Abriendo modelo Excel...")
with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='Dim_Comites_Comisiones_2026', index=False)
    print(f"   ✓ Hoja 'Dim_Comites_Comisiones_2026' actualizada")

# Validar
print("\n3️⃣ Validando modelo actualizado...")
excel_check = pd.ExcelFile(excel_path, engine='openpyxl')
sheets = excel_check.sheet_names
print(f"   ✓ Total de hojas en modelo: {len(sheets)}")
if 'Dim_Comites_Comisiones_2026' in sheets:
    df_check = pd.read_excel(excel_path, sheet_name='Dim_Comites_Comisiones_2026')
    print(f"   ✓ Hoja 'Dim_Comites_Comisiones_2026': {len(df_check)} filas")
    print("\n   Primeras 10 filas:")
    print(df_check.head(10).to_string())
else:
    print("   ⚠️ Hoja no encontrada!")

print("\n✅ ACTUALIZACIÓN COMPLETADA")
