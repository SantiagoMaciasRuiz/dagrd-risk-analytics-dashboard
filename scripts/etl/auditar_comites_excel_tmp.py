import pandas as pd
from pathlib import Path

p = Path(r"data/model/CONSOLIDADO COMITES COMISIONES 03-2026.xlsx")
xls = pd.ExcelFile(p)

print("sheets", len(xls.sheet_names))
print(xls.sheet_names)

for s in xls.sheet_names[:10]:
    df = pd.read_excel(p, sheet_name=s, header=None)
    print("---", s, "shape", df.shape)
    print(df.head(5).fillna("").to_string(index=False, header=False))
