import pandas as pd

excel_path = r"data\model\CONSOLIDADO COMITES COMISIONES 03-2026_Construcciom.xlsx"
xls = pd.ExcelFile(excel_path)

print("📊 ANÁLISIS: COMITÉS/COMISIONES ÚNICOS POR HOJA")
print("="*80)

# Leer todas las hojas excepto RESUMEN
rows = []
for sheet_name in xls.sheet_names:
    if "resumen" in sheet_name.lower() or sheet_name == "consolidado":
        print(f"\n⏭️  Saltando: {sheet_name}")
        continue
    
    print(f"\n📑 {sheet_name}:")
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Buscar columnas relevantes
        print(f"   Columnas: {df.columns.tolist()}")
        
        # Buscar "Nombre CCGRD" o similar
        relevant_cols = [col for col in df.columns if 'nombre' in col.lower() and ('ccgrd' in col.lower() or 'comite' in col.lower() or 'comision' in col.lower())]
        print(f"   Columnas relevantes: {relevant_cols}")
        
        if relevant_cols:
            col = relevant_cols[0]
            print(f"   Usando columna: {col}")
            
            # Valores únicos
            unique_names = df[col].dropna().unique()
            unique_names = [str(x).strip() for x in unique_names if x and str(x).strip()]
            print(f"   ✓ Valores únicos: {len(unique_names)}")
            for name in unique_names[:5]:
                print(f"      - {name}")
            if len(unique_names) > 5:
                print(f"      ... y {len(unique_names) - 5} más")
            
            # Agregar a filas
            for name in unique_names:
                rows.append({
                    'sheet': sheet_name,
                    'nombre': name
                })
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

print("\n" + "="*80)
print(f"\n📈 TOTAL ACUMULADO:")
print(f"   Total de registros sin deduplicar: {len(rows)}")

# Deduplicar por nombre
unique_nombres = set(r['nombre'] for r in rows)
print(f"   Total de nombres únicos: {len(unique_nombres)}")

print("\nNombres únicos encontrados:")
for nombre in sorted(unique_nombres):
    print(f"   - {nombre}")
