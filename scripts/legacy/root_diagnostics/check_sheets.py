import pandas as pd
from pathlib import Path

p = Path('data/model/Modelo_Reporte_Paginas_2026.xlsx')
xls = pd.ExcelFile(p)
print(f'Total hojas: {len(xls.sheet_names)}')
for sheet in xls.sheet_names[:10]:
    print(f'  {sheet}')
