#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
MODELO = BASE / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"
SATC_VALID = BASE / "data" / "model" / "validacion_satc_2026_03_18.xlsx"
ENTREGABLE_MODELO = BASE / "entregables" / "publicacion_nube_2026-03-20" / "02_datos_modelo" / "Modelo_Reporte_Paginas_2026.xlsx"
DIM_COMITES_CSV = BASE / "data" / "model" / "Dim_Comites_Comisiones_2026.csv"


def build_satc_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    if SATC_VALID.exists():
        satc_raw = pd.read_excel(SATC_VALID, sheet_name="SATC_Validacion")
        satc_df = pd.DataFrame(
            {
                "SATC_ID": satc_raw["satc_codigo"].astype(str),
                "SATC_Nombre": satc_raw["satc_nombre"].astype(str),
                "Comuna_Cod": pd.to_numeric(satc_raw["comuna_cod"], errors="coerce").fillna(0).astype(int),
                "Talleres": pd.to_numeric(satc_raw["talleres_registros"], errors="coerce").fillna(0).astype(int),
                "Comites": pd.to_numeric(satc_raw["comites_registros"], errors="coerce").fillna(0).astype(int),
                "Activo": satc_raw["existe_datos"].map({True: "Sí", False: "No"}).fillna("Sí"),
            }
        )
    else:
        satc_df = pd.DataFrame(columns=["SATC_ID", "SATC_Nombre", "Comuna_Cod", "Talleres", "Comites", "Activo"])

    rel_df = (
        satc_df.groupby("Comuna_Cod", dropna=False)
        .size()
        .reset_index(name="SATC_Cantidad")
        .sort_values("Comuna_Cod")
    )
    return satc_df, rel_df


def build_semilleros_confiable(dim_sem_df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    sem_id = pd.to_numeric(dim_sem_df.get("N°"), errors="coerce")
    fallback = pd.Series(range(1, len(dim_sem_df) + 1), index=dim_sem_df.index, dtype="float64")
    out["semillero_id"] = sem_id.fillna(fallback).astype(int)
    out["semillero_nombre"] = dim_sem_df.get("Semillero", "").astype(str)
    out["comuna_cod"] = pd.to_numeric(dim_sem_df.get("Comuna"), errors="coerce").fillna(0).astype(int)
    out["comuna_nombre"] = dim_sem_df.get("Comuna_Nombre", "").astype(str)
    out["barrio_organizacion"] = dim_sem_df.get("Barrio_Organización", "").astype(str)
    out["fuente_semillero"] = "DAGRD"
    out["activo"] = "Sí"
    return out


def build_dim_semilleros_vacia() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "N°",
            "Semillero",
            "Comuna",
            "Comuna_Nombre",
            "Barrio_Organización",
            "Total_Semilleros",
        ]
    )


def build_dim_comites_desde_csv() -> pd.DataFrame:
    if DIM_COMITES_CSV.exists():
        return pd.read_csv(DIM_COMITES_CSV)
    return pd.DataFrame(columns=["Nombre_Comite", "Comuna_Cod", "Comuna_Nombre", "Tipo"])


def write_df_to_sheet(wb, sheet_name: str, df: pd.DataFrame) -> None:
    if sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        wb.remove(ws)

    ws = wb.create_sheet(title=sheet_name[:31])
    ws.append(list(df.columns))

    for row in df.itertuples(index=False, name=None):
        ws.append(list(row))


def read_sheet_df(path: Path, sheet_name: str, fallback: pd.DataFrame) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except Exception:
        return fallback.copy()


def main() -> None:
    if not MODELO.exists():
        raise FileNotFoundError(f"No existe archivo modelo: {MODELO}")

    wb = load_workbook(MODELO)
    existing_sheets = set(wb.sheetnames)

    satc_existing = read_sheet_df(MODELO, "Dim_SATC", pd.DataFrame())
    sem_existing = read_sheet_df(MODELO, "Dim_Semilleros", pd.DataFrame())

    # SATC requeridos por Power BI
    satc_df, rel_df = build_satc_tables()

    # Blindaje: nunca degradar el catálogo SATC por debajo de 37
    if len(satc_df) < 37:
        if not satc_existing.empty and len(satc_existing) >= 37:
            satc_df = satc_existing.copy()
        elif ENTREGABLE_MODELO.exists():
            try:
                satc_fallback = pd.read_excel(ENTREGABLE_MODELO, sheet_name="Dim_SATC", engine="openpyxl")
                if len(satc_fallback) >= 37:
                    satc_df = satc_fallback
            except Exception:
                pass

        rel_df = (
            satc_df.groupby("Comuna_Cod", dropna=False)
            .size()
            .reset_index(name="SATC_Cantidad")
            .sort_values("Comuna_Cod")
        )

    write_df_to_sheet(wb, "Dim_SATC", satc_df)
    write_df_to_sheet(wb, "Dim_SATC_Relaciones", rel_df)

    # Semilleros requeridos por Power BI
    if "Dim_Semilleros" not in existing_sheets:
        dim_semilleros_df = build_dim_semilleros_vacia()
        if ENTREGABLE_MODELO.exists():
            try:
                dim_semilleros_df = pd.read_excel(ENTREGABLE_MODELO, sheet_name="Dim_Semilleros", engine="openpyxl")
            except Exception:
                dim_semilleros_df = build_dim_semilleros_vacia()
        write_df_to_sheet(wb, "Dim_Semilleros", dim_semilleros_df)
    else:
        dim_semilleros_df = sem_existing if not sem_existing.empty else build_dim_semilleros_vacia()

    sem_conf = build_semilleros_confiable(dim_semilleros_df)
    write_df_to_sheet(wb, "Dim_Semilleros_Confiable", sem_conf)

    # Comités/Comisiones requeridos por consultas del PBIX
    write_df_to_sheet(wb, "Dim_Comites_Comisiones_2026", build_dim_comites_desde_csv())

    wb.save(MODELO)

    print(f"OK: {MODELO}")
    print("Hojas críticas garantizadas:")
    final_sheets = set(wb.sheetnames)
    for n in ["Dim_SATC", "Dim_SATC_Relaciones", "Dim_Semilleros", "Dim_Semilleros_Confiable", "Dim_Comites_Comisiones_2026", "Hecho_Participacion_General", "Hecho_Demografia", "Hecho_Simulacros"]:
        print(f" - {n}: {'SI' if n in final_sheets else 'NO'}")


if __name__ == "__main__":
    main()
