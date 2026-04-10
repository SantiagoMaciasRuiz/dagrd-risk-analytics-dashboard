import pandas as pd

file_path = "Modelo_Reporte_Paginas_2026.xlsx"
df = pd.read_excel(file_path, sheet_name="Hecho_Participacion_General")
com = df[df["seccion_tablero"] == "Comunitaria"].copy()

print("=== VALORES UNICOS PARA TARJETAS COMUNIDAD ===")

# Comites/Comisiones
sub_comites = com[com["bloque_comunidad"] == "Comisiones y comites"].copy()
vals_pc = (
    sub_comites["publico_comunidad"]
    .dropna()
    .astype(str)
    .str.strip()
)
vals_pc = vals_pc[vals_pc != ""]
print("\n[Comites y comisiones] publico_comunidad (valor -> actividades)")
print(vals_pc.value_counts().to_string())
print(f"Distinct publico_comunidad: {vals_pc.nunique()}")

# SAT-C
sub_satc = com[com["bloque_comunidad"] == "SAT-C"].copy()
vals_satc = (
    sub_satc["nombre_satc"]
    .dropna()
    .astype(str)
    .str.strip()
)
vals_satc = vals_satc[vals_satc != ""]
print("\n[SAT-C] nombre_satc (top 50)")
print(vals_satc.value_counts().head(50).to_string())
print(f"Distinct nombre_satc: {vals_satc.nunique()}")

# Semilleros
sub_sem = com[com["bloque_comunidad"] == "Semilleros"].copy()
vals_sem_pub = (
    sub_sem["publico_comunidad"]
    .dropna()
    .astype(str)
    .str.strip()
)
vals_sem_pub = vals_sem_pub[vals_sem_pub != ""]
print("\n[Semilleros] publico_comunidad")
print(vals_sem_pub.value_counts().to_string())
print(f"Distinct publico_comunidad (semilleros): {vals_sem_pub.nunique()}")

vals_sem = (
    sub_sem["semillero_grd"]
    .dropna()
    .astype(str)
    .str.strip()
)
vals_sem = vals_sem[vals_sem != ""]
print("\n[Semilleros] semillero_grd")
print(vals_sem.value_counts().to_string())
print(f"Distinct semillero_grd: {vals_sem.nunique()}")
