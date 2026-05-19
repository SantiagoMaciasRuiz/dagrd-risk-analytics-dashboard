import pandas as pd

excel_path = r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx"
xls = pd.ExcelFile(excel_path)

print("📋 HOJAS DISPONIBLES EN EL EXCEL:")
print(f"Total: {len(xls.sheet_names)}")
print("\nNombres de hojas:")
for i, sheet in enumerate(xls.sheet_names, 1):
    print(f"  {i}. {sheet}")

# Analizar la hoja Resumen
print("\n" + "="*80)
print("📊 CONTENIDO DE LA HOJA 'Resumen':")
print("="*80)

resumen_df = pd.read_excel(excel_path, sheet_name="RESUMEN")
print(f"\nDimensiones: {resumen_df.shape[0]} filas × {resumen_df.shape[1]} columnas")
print(f"\nColumnas: {resumen_df.columns.tolist()}")
print(f"\nPrimeras 15 filas:")
print(resumen_df.head(15).to_string())

print(f"\n✓ Valores únicos por columna:")
for col in resumen_df.columns:
    unique_count = resumen_df[col].nunique()
    print(f"  - {col}: {unique_count} únicos")
