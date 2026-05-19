import pandas as pd
from pathlib import Path

p = Path(r"data/model/CONSOLIDADO COMITES COMISIONES 03-2026.xlsx")
xls = pd.ExcelFile(p)

valid_sheets = [s for s in xls.sheet_names if s not in {"RESUMEN", "Coordinadores"}]

rows = []
per_sheet = []

for s in valid_sheets:
    df = pd.read_excel(p, sheet_name=s, header=None)

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
        per_sheet.append((s, 0, 0, 0, "NO_HEADER"))
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
        per_sheet.append((s, 0, 0, 0, "MISSING_COLS"))
        continue

    work = data[[col_tipo, col_comuna2, col_nombre]].copy()
    work.columns = ["tipo_raw", "comuna2", "nombre_ccgrd"]

    work["tipo_raw"] = work["tipo_raw"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    work["tipo"] = work["tipo_raw"].where(work["tipo_raw"].isin(["S", "T"]))
    work["tipo"] = work["tipo"].ffill()

    work["comuna2"] = pd.to_numeric(work["comuna2"], errors="coerce")
    work["nombre_ccgrd"] = work["nombre_ccgrd"].astype(str).str.strip()
    work = work[(work["nombre_ccgrd"] != "") & (~work["nombre_ccgrd"].str.lower().isin(["nan", "none"]))]
    work = work[work["comuna2"].notna()]
    work = work[work["tipo"].isin(["S", "T"])]

    dedup = work.drop_duplicates(subset=["comuna2", "nombre_ccgrd", "tipo"]).copy()
    n_s = int((dedup["tipo"] == "S").sum())
    n_t = int((dedup["tipo"] == "T").sum())
    n_tot = int(len(dedup))

    per_sheet.append((s, n_s, n_t, n_tot, "OK"))
    dedup["sheet"] = s
    rows.append(dedup)

all_df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["tipo","comuna2","nombre_ccgrd","sheet"])

# Consolidado global deduplicado (por si una entidad aparece en varias hojas)
global_dedup = all_df.drop_duplicates(subset=["comuna2", "nombre_ccgrd", "tipo"]).copy()

print("=== CONTEO POR HOJA (S=Comision, T=Comite) ===")
for s, ns, nt, ntot, st in per_sheet:
    print(f"{s:12} S={ns:3d} T={nt:3d} TOTAL={ntot:3d} [{st}]")

print("\n=== TOTALES DEDUP GLOBALES ===")
print("S (comisiones):", int((global_dedup["tipo"] == "S").sum()))
print("T (comites):", int((global_dedup["tipo"] == "T").sum()))
print("TOTAL:", int(len(global_dedup)))

# RESUMEN
res = pd.read_excel(p, sheet_name="RESUMEN")
res_cols = {str(c).strip().lower(): c for c in res.columns}
col_c = next((res_cols[k] for k in res_cols if "# comit" in k and "total" not in k), None)
col_s = next((res_cols[k] for k in res_cols if "# comision" in k), None)
col_tot = next((res_cols[k] for k in res_cols if "total de comit" in k), None)

if col_c and col_s and col_tot:
    rr = res.copy()
    rr[col_c] = pd.to_numeric(rr[col_c], errors="coerce").fillna(0)
    rr[col_s] = pd.to_numeric(rr[col_s], errors="coerce").fillna(0)
    rr[col_tot] = pd.to_numeric(rr[col_tot], errors="coerce").fillna(0)
    # excluye fila total si existe
    if "nombre de la comuna" in [str(c).strip().lower() for c in rr.columns]:
        nc = [c for c in rr.columns if str(c).strip().lower() == "nombre de la comuna"][0]
        rr = rr[~rr[nc].astype(str).str.upper().str.contains("TOTAL", na=False)]

    print("\n=== RESUMEN (suma filas comunas) ===")
    print("Comites (#):", int(rr[col_c].sum()))
    print("Comisiones (#):", int(rr[col_s].sum()))
    print("Total:", int(rr[col_tot].sum()))

    print("\n=== DIFERENCIA VS RESUMEN ===")
    print("Delta Comites (T - resumen):", int((global_dedup["tipo"] == "T").sum() - rr[col_c].sum()))
    print("Delta Comisiones (S - resumen):", int((global_dedup["tipo"] == "S").sum() - rr[col_s].sum()))
    print("Delta Total:", int(len(global_dedup) - rr[col_tot].sum()))
else:
    print("No se pudieron detectar columnas de RESUMEN")
