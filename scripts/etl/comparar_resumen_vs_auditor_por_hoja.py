import pandas as pd
from pathlib import Path

p = Path(r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\model\CONSOLIDADO COMITES COMISIONES 03-2026.xlsx")

# ========== REPLICAR CONTEO DEL RESUMEN: Contar T y S POR HOJA (sin dedup global) ==========
xls = pd.ExcelFile(p)
valid_sheets = [s for s in xls.sheet_names if s not in {"RESUMEN", "Coordinadores"}]

# Leer RESUMEN para comparar
resumen = pd.read_excel(p, sheet_name="RESUMEN", header=None)
resumen_data = resumen.iloc[2:24].copy()  # Rows 3-24 (comunas, sin headers ni totales)
resumen_data.columns = resumen.iloc[1].tolist()  # Headers from row 2

print("=== COMPARACIÓN HOJA POR HOJA ===")
print(f"{'Hoja':<12} {'COUNTIF-T':<12} {'COUNTIF-S':<12} {'Auditor-T':<12} {'Auditor-S':<12} {'Delta':<8}")
print("-" * 80)

grand_total_t_resumen = 0
grand_total_s_resumen = 0
grand_total_t_auditor = 0
grand_total_s_auditor = 0

for sheet_idx, sheet_name in enumerate(valid_sheets, 1):
    # ========== LÓGICA DEL AUDITOR (con normalización) ==========
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
        print(f"{sheet_name:<12} {'ERROR':<12} {'NO_HEADER':<12}")
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
        print(f"{sheet_name:<12} {'ERROR':<12} {'MISSING_COLS':<12}")
        continue
    
    work = data[[col_tipo, col_comuna2, col_nombre]].copy()
    work.columns = ["tipo_raw", "comuna2", "nombre_ccgrd"]
    work["tipo_raw"] = work["tipo_raw"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    work["tipo"] = work["tipo_raw"].where(work["tipo_raw"].isin(["S", "T"]))
    work["tipo"] = work["tipo"].ffill()
    work["comuna2"] = pd.to_numeric(work["comuna2"], errors="coerce")
    work["nombre_ccgrd"] = work["nombre_ccgrd"].astype(str).str.strip()
    
    # Filtros del auditor
    work = work[(work["nombre_ccgrd"] != "") & (~work["nombre_ccgrd"].str.lower().isin(["nan", "none"]))]
    work = work[work["comuna2"].notna()]
    work = work[work["tipo"].isin(["S", "T"])]
    
    # IMPORTANTE: Sin dedup global, solo contar por hoja
    n_t_auditor = int((work["tipo"] == "T").sum())
    n_s_auditor = int((work["tipo"] == "S").sum())
    
    # ========== LÓGICA DEL RESUMEN: Contar raw sin normalización ==========
    df_raw = pd.read_excel(p, sheet_name=sheet_name, header=None)
    
    # Encontrar headers
    header_idx_raw = None
    for i in range(min(8, len(df_raw))):
        vals = [str(v).strip() for v in df_raw.iloc[i].tolist()]
        norm = [v.lower().replace(" ", "") for v in vals]
        if "comuna2" in norm and any("nombreccgrd" in x for x in norm):
            header_idx_raw = i
            break
    
    if header_idx_raw is not None:
        # Contar directamente sin procesar
        data_raw = df_raw.iloc[header_idx_raw + 1 :].copy()
        cols_norm_raw = {str(c).strip().lower().replace(" ", ""): i for i, c in enumerate(df_raw.iloc[header_idx_raw].tolist())}
        col_tipo_idx = cols_norm_raw.get("comuna")
        
        if col_tipo_idx is not None:
            tipo_vals = data_raw.iloc[:, col_tipo_idx].astype(str).str.strip().str.upper()
            # El RESUMEN cuenta cualquier "T" o "S" sin procesar más
            n_t_raw = int((tipo_vals == "T").sum())
            n_s_raw = int((tipo_vals == "S").sum())
        else:
            n_t_raw = 0
            n_s_raw = 0
    else:
        n_t_raw = 0
        n_s_raw = 0
    
    # Comparar con RESUMEN
    # Encontrar el índice de la comunista en RESUMEN
    # Las hojas se llaman C1, C2, ... entonces el índice en RESUMEN es el número
    try:
        sheet_num = int(sheet_name[1:]) if sheet_name.startswith("C") else None
        if sheet_num:
            resumen_row = resumen_data[resumen_data.iloc[:, 1] == sheet_num]
            if len(resumen_row) > 0:
                n_t_resumen = int(resumen_row.iloc[0, 3])  # Col D = # Comités
                n_s_resumen = int(resumen_row.iloc[0, 5])  # Col F = # Comisiones
            else:
                n_t_resumen = 0
                n_s_resumen = 0
        else:
            n_t_resumen = 0
            n_s_resumen = 0
    except:
        n_t_resumen = 0
        n_s_resumen = 0
    
    delta = (n_t_auditor + n_s_auditor) - (n_t_resumen + n_s_resumen)
    
    print(f"{sheet_name:<12} T={n_t_resumen:<3} S={n_s_resumen:<3} T={n_t_auditor:<3} S={n_s_auditor:<3} {delta:>+3}")
    
    grand_total_t_resumen += n_t_resumen
    grand_total_s_resumen += n_s_resumen
    grand_total_t_auditor += n_t_auditor
    grand_total_s_auditor += n_s_auditor

print("-" * 80)
print(f"{'TOTAL':<12} T={grand_total_t_resumen:<3} S={grand_total_s_resumen:<3} T={grand_total_t_auditor:<3} S={grand_total_s_auditor:<3} {(grand_total_t_auditor + grand_total_s_auditor) - (grand_total_t_resumen + grand_total_s_resumen):>+3}")
print()
print(f"RESUMEN: {grand_total_t_resumen} T + {grand_total_s_resumen} S = {grand_total_t_resumen + grand_total_s_resumen}")
print(f"AUDITOR: {grand_total_t_auditor} T + {grand_total_s_auditor} S = {grand_total_t_auditor + grand_total_s_auditor}")
print(f"DELTA: {(grand_total_t_auditor + grand_total_s_auditor) - (grand_total_t_resumen + grand_total_s_resumen)}")
