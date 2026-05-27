import pandas as pd
from pathlib import Path
import unicodedata
import re

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")

def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

def _normalize_comite_name(value: object) -> str:
    text = str(value or "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text or text.lower() in {"nan", "none"}:
        return ""
    text = _strip_accents(text).upper()
    text = re.sub(r"[;|,]+$", "", text).strip()
    return text

# Auditor (registros tal como están)
p = Path(r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\model\CONSOLIDADO COMITES COMISIONES 03-2026.xlsx")

xls = pd.ExcelFile(p)
valid_sheets = [s for s in xls.sheet_names if s not in {"RESUMEN", "Coordinadores"}]

auditor_rows = []
for sheet_name in valid_sheets:
    df = pd.read_excel(p, sheet_name=sheet_name, header=None)
    
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
    work = work[work["tipo_raw"].isin(["S", "T"])].copy()
    work["tipo"] = work["tipo_raw"]
    work["comuna2"] = pd.to_numeric(work["comuna2"], errors="coerce")
    work["nombre_ccgrd"] = work["nombre_ccgrd"].astype(str).str.strip()
    
    work = work[(work["nombre_ccgrd"] != "") & (~work["nombre_ccgrd"].str.lower().isin(["nan", "none"]))]
    work = work[work["comuna2"].notna()]
    work = work[work["tipo"].isin(["S", "T"])]
    
    for _, row in work.iterrows():
        nombre_norm = _normalize_comite_name(row["nombre_ccgrd"])
        auditor_rows.append({
            "tipo": row["tipo"],
            "comuna2": int(row["comuna2"]),
            "nombre_raw": row["nombre_ccgrd"],
            "nombre_norm": nombre_norm,
            "sheet": sheet_name,
        })

auditor_df = pd.DataFrame(auditor_rows)
auditor_dedup = auditor_df.drop_duplicates(subset=["comuna2", "nombre_norm", "tipo"]).copy()

print(f"Auditor TOTAL (sin dedup): {len(auditor_df)} filas")
print(f"Auditor DEDUP (por comuna2+nombre_norm+tipo): {len(auditor_dedup)} filas")
print()

# CSV actual
csv_df = pd.read_csv(BASE / "data" / "model" / "Dim_Comites_Comisiones_2026.csv")
csv_dedup = csv_df.drop_duplicates(subset=["comuna_cod", "comite_comision_nombre"]).copy()

print(f"CSV TOTAL: {len(csv_df)} filas")
print(f"CSV DEDUP: {len(csv_dedup)} filas")
print()

# Comparar: auditor_dedup vs csv_dedup
auditor_for_compare = auditor_dedup[["comuna2", "nombre_norm", "tipo"]].drop_duplicates()
auditor_for_compare.columns = ["comuna_cod", "comite_comision_nombre", "tipo"]

# Los registros del CSV
csv_set = set(zip(csv_dedup["comuna_cod"], csv_dedup["comite_comision_nombre"]))

# Los registros del auditor
auditor_set = set(zip(auditor_for_compare["comuna_cod"], auditor_for_compare["comite_comision_nombre"]))

print(f"=== REGISTROS QUE FALTAN EN CSV (en auditor pero no en CSV) ===")
missing_in_csv = auditor_set - csv_set
if missing_in_csv:
    for comuna, nombre in sorted(missing_in_csv):
        print(f"  Comuna {int(comuna)}: {nombre}")
else:
    print("  (Ninguno)")
print()

print(f"=== REGISTROS EXTRA EN CSV (en CSV pero no en auditor) ===")
extra_in_csv = csv_set - auditor_set
if extra_in_csv:
    for comuna, nombre in sorted(extra_in_csv):
        print(f"  Comuna {int(comuna)}: {nombre}")
else:
    print("  (Ninguno)")
