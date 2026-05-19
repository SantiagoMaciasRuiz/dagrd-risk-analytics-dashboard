import pandas as pd
from pathlib import Path

print("🔍 VALIDACIÓN DEL MODELO EXCEL ACTUALIZADO")
print("="*80)

excel_path = Path("data/model/Modelo_Reporte_Paginas_2026.xlsx")

# Leer todas las hojas
excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
sheets = excel_file.sheet_names

print(f"\n📋 Total de hojas: {len(sheets)}")

# Hojas críticas que debemos validar
critical_sheets = {
    'Dim_Comites_Comisiones_2026': {'expected_cols': ['comuna_cod', 'comite_comision_nombre', 'comite_comision_etiqueta'], 'min_rows': 160},
    'Dim_SATC': {'expected_cols': ['SATC_ID', 'SATC_Nombre'], 'min_rows': 30},
    'Dim_Semilleros': {'expected_cols': ['Semillero', 'Comuna'], 'min_rows': 18},
    'Hecho_Simulacros': {'expected_cols': ['Simulacro'], 'min_rows': 3000},
}

print("\n✓ Validando hojas críticas:")
all_ok = True
for sheet_name, specs in critical_sheets.items():
    if sheet_name not in sheets:
        print(f"   ❌ {sheet_name}: NO EXISTE")
        all_ok = False
        continue
    
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    # Verificar filas
    row_ok = len(df) >= specs['min_rows']
    row_status = "✓" if row_ok else "❌"
    
    # Verificar columnas clave
    cols_ok = all(col in df.columns for col in specs['expected_cols'])
    cols_status = "✓" if cols_ok else "❌"
    
    print(f"   {row_status}{cols_status} {sheet_name}: {len(df)} filas, columnas: {cols_ok}")
    
    if not (row_ok and cols_ok):
        all_ok = False

if all_ok:
    print("\n✅ MODELO VALIDADO - Todas las hojas críticas están correctas")
else:
    print("\n⚠️ MODELO CON PROBLEMAS - Ver detalles arriba")

# Resumen final
print("\n" + "="*80)
print("📊 RESUMEN DEL MODELO:")
for sheet in sheets:
    df = pd.read_excel(excel_path, sheet_name=sheet)
    cols = df.shape[1]
    rows = df.shape[0]
    # Mostrar primeros X bytes de tipos
    dtypes = ", ".join([f"{col}:{df[col].dtype}" for col in df.columns[:3]])
    print(f"   {sheet[:35]:35} | {rows:5} rows | {cols:2} cols | {dtypes}...")
