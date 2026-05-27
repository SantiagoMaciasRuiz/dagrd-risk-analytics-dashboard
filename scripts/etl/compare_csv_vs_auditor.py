import pandas as pd
from pathlib import Path

# Auditor sin dedup global (conteo correcto)
p = Path(r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\model\CONSOLIDADO COMITES COMISIONES 03-2026.xlsx")

xls = pd.ExcelFile(p)
valid_sheets = [s for s in xls.sheet_names if s not in {"RESUMEN", "Coordinadores"}]

auditor_rows = []
for sheet_name in valid_sheets:
    df = pd.read_excel(p, sheet_name=sheet_name, header=None)
    
    # Buscar header
    header_idx = None
    header_map = {}
    for i in range(min(8, len(df))):
        vals = [str(v).strip() for v in df.iloc[i].tolist()]
        norm = [v.lower().replace(" ", "") for v in vals]
        if "comuna2" in norm and any("nombreccgrd" in x for x in norm):
            header_idx = i
            header_map = {j: vals[j] for j in range(len(vals))}
            break
    
    if header_idx is None:
        continue
    
    data = df.iloc[header_idx + 1 :].copy()
    data.columns = [header_map.get(j, f"col_{j}") for j in range(data.shape[1])]
    cols_norm = {str(c).strip().lower().replace(" ", ""): c for c in data.columns}
    
    col_tipo = cols_norm.get("comuna")
    col_comuna2 = cols_norm.get("comuna2")
    col_nombre = None
    for k, c in cols_norm.items():
        if "nombreccgrd" in k:
            col_nombre = c
            break
    
    if not (col_tipo and col_comuna2 and col_nombre):
        continue
    
    work = data[[col_tipo, col_comuna2, col_nombre]].copy()
    work.columns = ["tipo_raw", "comuna2", "nombre_ccgrd"]
    work["tipo_raw"] = work["tipo_raw"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    # Sin ffill
    work = work[work["tipo_raw"].isin(["S", "T"])].copy()
    work["tipo"] = work["tipo_raw"]
    work["comuna2"] = pd.to_numeric(work["comuna2"], errors="coerce")
    work["nombre_ccgrd"] = work["nombre_ccgrd"].astype(str).str.strip()
    
    work = work[(work["nombre_ccgrd"] != "") & (~work["nombre_ccgrd"].str.lower().isin(["nan", "none"]))]
    work = work[work["comuna2"].notna()]
    work = work[work["tipo"].isin(["S", "T"])]
    
    # Sin dedup intra-hoja
    for _, row in work.iterrows():
        auditor_rows.append({
            "tipo": row["tipo"],
            "comuna2": int(row["comuna2"]),
            "nombre_ccgrd": row["nombre_ccgrd"],
            "sheet": sheet_name,
        })

auditor_df = pd.DataFrame(auditor_rows)
print(f"Auditor (sin dedup global): {len(auditor_df)} filas")
print()

# CSV actual
csv_df = pd.read_csv(r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\model\Dim_Comites_Comisiones_2026.csv")
print(f"CSV actual: {len(csv_df)} filas")
print()

# Dedup global del auditor
auditor_dedup = auditor_df.drop_duplicates(subset=["comuna2", "nombre_ccgrd", "tipo"]).copy()
print(f"Auditor (con dedup global): {len(auditor_dedup)} filas")
print()

# Comparar con CSV
# El CSV tiene estructura diferente, vamos a ver
print("=== CSV COLUMNS ===")
print(csv_df.columns.tolist())
print()
print(csv_df.head())
