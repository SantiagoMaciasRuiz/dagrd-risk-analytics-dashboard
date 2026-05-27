#!/usr/bin/env python3
import sys
sys.path.insert(0, '.venv/Lib/site-packages')

import pandas as pd
from pathlib import Path
import os

os.chdir(r'C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard')

p = Path('data/model/Modelo_Reporte_Paginas_2026.xlsx')

try:
    xls = pd.ExcelFile(p, engine='openpyxl')
    sheets = xls.sheet_names
    
    print(f'✅ Total hojas: {len(sheets)}')
    print('\nHojas presentes:')
    for sheet in sorted(sheets):
        df = pd.read_excel(p, sheet_name=sheet, engine='openpyxl')
        print(f'  ✓ {sheet}: {len(df)} rows × {len(df.columns)} cols')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
