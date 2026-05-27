import pandas as pd

excel_path = r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx"

# Verificar qué hay exactamente en la fila 0 de hojas C1 y C2
for sheet_name in ["C1", "C2", "COMUNA 2"]:
    print(f"\n📑 {sheet_name} - Fila 0 (headers):")
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    print(f"   Row 0: {df_raw.iloc[0].tolist()}")
    
    # Buscar "Nombre CCGRD"
    found = False
    for col_idx, val in enumerate(df_raw.iloc[0]):
        val_str = str(val).lower()
        if "nombre" in val_str and "ccgrd" in val_str:
            print(f"   ✓ Encontrado en columna {col_idx}: {val}")
            found = True
    if not found:
        print(f"   ⚠️ NO encontrado 'nombre ccgrd'")
        # Mostrar qué hay en cada columna
        for col_idx, val in enumerate(df_raw.iloc[0]):
            val_str = str(val).strip()
            if val_str:
                print(f"      Columna {col_idx}: '{val_str}'")
