import pandas as pd
from pathlib import Path

excel_path = Path(r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx")
xls = pd.ExcelFile(excel_path)

print("📊 PRUEBA DE EXTRACCIÓN DE COMITÉS MEJORADA")
print("="*80)

rows = []
for sheet_name in xls.sheet_names:
    sh = sheet_name.strip().lower().replace(" ", "")
    
    if "resumen" in sh or sh == "consolidado":
        print(f"⏭️  {sheet_name}: SALTADO (resumen/consolidado)")
        continue
    
    print(f"\n📑 {sheet_name}:")
    
    try:
        # Intenta primero con headers estándar
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"   ✓ Leído con headers estándar: {df.shape}")
        
        name_col = None
        for c in df.columns:
            hc = c.strip().lower().replace(" ", "")
            if "nombre" in hc and ("comision" in hc or "ccgrd" in hc):
                name_col = c
                print(f"   ✓ Encontrada columna por nombre: {c}")
                break
        
        if name_col is None:
            print(f"   ⚠️ No encontrada columna por nombre, intentando header=None...")
            df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
            print(f"   ✓ Leído raw: {df_raw.shape}")
            
            if len(df_raw) > 0 and len(df_raw.columns) >= 8:
                # Buscar "Nombre CCGRD" en la fila 0
                for col_idx, val in enumerate(df_raw.iloc[0]):
                    if "nombre" in str(val).lower() and "ccgrd" in str(val).lower():
                        name_col = col_idx
                        print(f"   ✓ Encontrada columna en índice {col_idx}: {val}")
                        
                        # Usar los valores de esa columna desde fila 1
                        unique_vals = df_raw.iloc[1:, col_idx].dropna().unique()
                        print(f"   ✓ Valores únicos en columna {col_idx}: {len(unique_vals)}")
                        for val in list(unique_vals)[:5]:
                            print(f"      - {val}")
                        if len(unique_vals) > 5:
                            print(f"      ... y {len(unique_vals) - 5} más")
                        
                        # Agregar a rows para conteo
                        for val in unique_vals:
                            if val and str(val).strip():
                                rows.append({
                                    'sheet': sheet_name,
                                    'nombre': str(val).strip()
                                })
                        break
        else:
            # Si encontró por nombre, agregar los valores únicos
            unique_vals = df[name_col].dropna().unique()
            print(f"   ✓ Valores únicos: {len(unique_vals)}")
            for val in list(unique_vals)[:5]:
                print(f"      - {val}")
            if len(unique_vals) > 5:
                print(f"      ... y {len(unique_vals) - 5} más")
                
            for val in unique_vals:
                if val and str(val).strip():
                    rows.append({
                        'sheet': sheet_name,
                        'nombre': str(val).strip()
                    })
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print(f"📈 TOTAL SIN DEDUPLICAR: {len(rows)} registros")

unique_nombres = {}
for r in rows:
    key = r['nombre']
    if key not in unique_nombres:
        unique_nombres[key] = []
    unique_nombres[key].append(r['sheet'])

print(f"📊 TOTAL DE NOMBRES ÚNICOS: {len(unique_nombres)}")
print("\nNombres únicos encontrados:")
for nombre in sorted(unique_nombres.keys()):
    sheets = unique_nombres[nombre]
    print(f"   - {nombre} (en hojas: {', '.join(sheets)})")
