import pandas as pd
from pathlib import Path

try:
    p = Path('data/model/Modelo_Reporte_Paginas_2026.xlsx')
    print(f'✅ Archivo existe: {p.exists()}')
    
    xls = pd.ExcelFile(p)
    print(f'📋 Hojas: {len(xls.sheet_names)}')
    print(f'   Hojas: {xls.sheet_names[:5]}...')
    
    df = pd.read_excel(p, sheet_name='Hecho_Participacion_General')
    print(f'✓ Hecho_Participacion_General: {len(df)} filas')
    
    df2 = pd.read_excel(p, sheet_name='Hecho_Simulacros')
    print(f'✓ Hecho_Simulacros: {len(df2)} filas')
    
    df3 = pd.read_excel(p, sheet_name='Dim_Comites_Comisiones_2026')
    print(f'✓ Dim_Comites_Comisiones_2026: {len(df3)} filas')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
