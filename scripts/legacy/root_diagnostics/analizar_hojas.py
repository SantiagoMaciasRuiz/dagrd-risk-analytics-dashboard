import pandas as pd

excel_path = r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx"
xls = pd.ExcelFile(excel_path)

print("📋 ESTRUCTURA DE CADA HOJA")
print("="*80)

# Analizar la primera hoja individual
for sheet_name in ["C1", "C2", "RESUMEN"]:
    print(f"\n📑 HOJA: {sheet_name}")
    print("-" * 80)
    
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    print(f"Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
    print(f"Columnas: {df.columns.tolist()}")
    print(f"\nPrimeras 10 filas (raw):")
    print(df.head(10).to_string())
    print("\n")
