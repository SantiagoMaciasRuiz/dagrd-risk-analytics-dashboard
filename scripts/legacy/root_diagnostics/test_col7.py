import pandas as pd

excel_path = r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx"

# Verificar qué hay en la columna 7 de hojas C1, C2, C3
for sheet_name in ["C1", "C2", "C3", "C8"]:
    print(f"\n📑 {sheet_name} - Columna índice 7:")
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    
    print(f"   Shape: {df.shape}")
    print(f"   Primeras 15 filas de columna índice 7:")
    
    col_values = df[7].dropna().unique()
    for val in col_values[:15]:
        print(f"      - {val}")
