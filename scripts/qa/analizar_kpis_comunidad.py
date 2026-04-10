import pandas as pd
from pathlib import Path

file_path = Path("Modelo_Reporte_Paginas_2026.xlsx")
sheet = "Hecho_Participacion_General"

print(f"Archivo: {file_path}")
print(f"Hoja: {sheet}")

df = pd.read_excel(file_path, sheet_name=sheet)

print(f"Filas: {len(df)}")
print(f"Columnas: {len(df.columns)}")

print("\nColumnas principales:")
for c in df.columns:
    if any(k in c.lower() for k in ["comunidad", "sat", "comite", "comision", "semill", "publico", "bloque", "seccion", "instancia", "comuna"]):
        print(f" - {c}")

# Filtro comunitaria
com = df[df["seccion_tablero"] == "Comunitaria"].copy()
print("\n=== BASE COMUNITARIA ===")
print(f"Registros Comunitaria: {len(com)}")

# Resumen de bloque_comunidad
if "bloque_comunidad" in com.columns:
    print("\nActividades por bloque_comunidad:")
    vc = com["bloque_comunidad"].value_counts(dropna=False)
    print(vc.to_string())

# Candidatos de KPI comites
print("\n=== CANDIDATOS KPI COMITES ===")
com_comites = com[com["bloque_comunidad"] == "Comisiones y comites"].copy() if "bloque_comunidad" in com.columns else com.iloc[0:0]
print(f"Registros bloque Comisiones y comites: {len(com_comites)}")

for col in [
    "comuna_cod",
    "publico_comunidad",
    "actividad_comunitaria",
    "instancia",
    "nombre_satc",
]:
    if col in com_comites.columns:
        series = com_comites[col].dropna().astype(str).str.strip()
        series = series[series != ""]
        print(f"Distinct {col}: {series.nunique()}")

# Candidatos de KPI semilleros
print("\n=== CANDIDATOS KPI SEMILLEROS ===")
com_sem = com[com["bloque_comunidad"] == "Semilleros"].copy() if "bloque_comunidad" in com.columns else com.iloc[0:0]
print(f"Registros bloque Semilleros: {len(com_sem)}")
for col in [
    "comuna_cod",
    "semillero_grd",
    "actividad_semillero",
    "publico_comunidad",
]:
    if col in com_sem.columns:
        series = com_sem[col].dropna().astype(str).str.strip()
        series = series[series != ""]
        print(f"Distinct {col}: {series.nunique()}")

# Candidatos de KPI SATC
print("\n=== CANDIDATOS KPI SATC ===")
com_satc = com[com["bloque_comunidad"] == "SAT-C"].copy() if "bloque_comunidad" in com.columns else com.iloc[0:0]
print(f"Registros bloque SAT-C: {len(com_satc)}")
if "nombre_satc" in com_satc.columns:
    s = com_satc["nombre_satc"].dropna().astype(str).str.strip()
    s = s[s != ""]
    print(f"Distinct nombre_satc (raw): {s.nunique()}")

    # Normalizacion ligera
    s_norm = (
        s.str.replace("–", "-", regex=False)
        .str.replace(r"^C\s*(\d+)\s*-\s*", "", regex=True)
        .str.replace(r"^C(\d+)\s*-\s*", "", regex=True)
        .str.replace("  ", " ", regex=False)
        .str.strip()
    )
    s_norm = s_norm[s_norm.str.lower() != "todos los sat-c"]
    s_norm = s_norm[s_norm != ""]
    print(f"Distinct nombre_satc (normalizado): {s_norm.nunique()}")

# combinación de tarjeta por comuna distinta por bloque
print("\n=== DISTINCT COMUNA POR BLOQUE ===")
for block in ["Comisiones y comites", "Semilleros", "SAT-C"]:
    sub = com[com["bloque_comunidad"] == block]
    if "comuna_cod" in sub.columns:
        vals = pd.to_numeric(sub["comuna_cod"], errors="coerce").dropna().astype(int)
        print(f"{block}: {vals.nunique()} comunas ({sorted(vals.unique().tolist())})")
