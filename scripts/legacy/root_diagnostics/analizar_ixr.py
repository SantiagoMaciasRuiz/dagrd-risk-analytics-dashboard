import pandas as pd

excel_path = r"data\model\IxR_2024-2026.xlsx"

try:
    xls = pd.ExcelFile(excel_path)
    
    print("📋 ESTRUCTURA DE IxR_2024-2026.xlsx")
    print("="*80)
    print(f"\nHojas disponibles: {xls.sheet_names}")
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        print(f"\n📑 {sheet}:")
        print(f"   Shape: {df.shape[0]} filas × {df.shape[1]} columnas")
        print(f"   Columnas: {df.columns.tolist()}")
        
        # Buscar columnas con "fecha"
        fecha_cols = [col for col in df.columns if 'fecha' in col.lower()]
        if fecha_cols:
            print(f"   📅 Columnas de fecha encontradas: {fecha_cols}")
            for col in fecha_cols:
                print(f"      - {col}: {df[col].dtype}")
                print(f"        Muestra: {df[col].head(3).tolist()}")
        
        # Mostrar primeras filas de la primera hoja
        if sheet == xls.sheet_names[0]:
            print(f"\n   Primeras 3 filas:")
            print(df.head(3).to_string())

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
