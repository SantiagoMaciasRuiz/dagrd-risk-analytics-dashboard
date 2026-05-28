"""Regenera puente SATC y normaliza nombre_satc contra el catálogo vigente."""

from pathlib import Path
import re
import unicodedata

import pandas as pd


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / "data").exists() or (candidate / "datos").exists():
            return candidate
    return Path.cwd()


ROOT_DIR = _find_project_root()


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value))
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _norm_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^C\s*(\d+)\s*-\s*", "", text, flags=re.IGNORECASE)
    text = _strip_accents(text).lower().strip()
    return text


def _build_alias_by_comuna() -> dict[int, dict[str, str]]:
    return {
        2: {
            "playon de los comuneros": "Playón de Comuneros",
        },
            "san isidro (choco chiquito)": "Chocó Chiquito",
        4: {
            "la bermejala (el hueco)": "El Hoyo",
            "el hueco": "El Hoyo",
        },
        6: {
            "john f. kennedy": "Picacho",
            "kennedy cantera sur": "Miramar",
        },
        7: {
            "nueva villa de iguana": "Nueva Villa de La Iguaná",
            "olaya herrera": "Olaya Herrera 1",
            "olaya herrera 1 (la arenera)": "Olaya Herrera 1",
        },
        8: {
            "villatina la torre": "Villatina La Torre",
            "la castro": "La Paz",
            "colinas de enciso": "Colinas de Enciso",
            "santa lucia-barrio las estancias": "Santa Lucía",
        },
        9: {
            "las estancias": "Las Estancias",
            "santa lucia-barrio las estancias": "Santa Lucía",
        },
        60: {
            "la honda - sector caracolí": "La Honda",
            "la honda - sector caracoli": "La Honda",
        },
        70: {
            "las playitas-vereda san pablo": "La Playita- Aguas Frías",
            "el guamo": "Guamo",
            "san vicente": "La Unión",
            "aguas frías parte alta": "Aguas Frías-Antigua Terminal",
            "aguas frias parte alta": "Aguas Frías-Antigua Terminal",
            "los tanques": "Morro Corazón Los Tanques",
        },
        80: {
            "santa rita-vereda la verde": "Santa Rita",
            "las playas-vereda el salado": "Salado-Playas",
            "el paraiso-vereda el salado": "Salado-Paraíso",
        },
    }


def _build_catalogo_por_comuna(satc_df: pd.DataFrame) -> dict[int, list[str]]:
    catalogo_por_comuna: dict[int, list[str]] = {}
    if satc_df.empty:
        return catalogo_por_comuna

    work = satc_df.copy()
    if "SATC_ID" in work.columns:
        work["_satc_order"] = pd.to_numeric(work["SATC_ID"], errors="coerce").fillna(0).astype(int)
        order_cols = ["Comuna_Cod", "_satc_order"]
    else:
        order_cols = ["Comuna_Cod"]

    for comuna, group in work.sort_values(order_cols).groupby("Comuna_Cod", dropna=False):
        nombres = [str(value).strip() for value in group["SATC_Nombre"].tolist() if str(value).strip()]
        if nombres:
            catalogo_por_comuna[int(comuna)] = nombres
    return catalogo_por_comuna


def _normalize_nombre_satc_in_hechos(df: pd.DataFrame, satc_df: pd.DataFrame) -> pd.DataFrame:
    alias_by_comuna = _build_alias_by_comuna()
    catalogo_por_comuna = _build_catalogo_por_comuna(satc_df)
    canonical_norm = {comuna: {_norm_text(name): name for name in names} for comuna, names in catalogo_por_comuna.items()}

    if "nombre_satc_original" not in df.columns:
        df["nombre_satc_original"] = df["nombre_satc"]

    # Orden estable para repartir ambiguos y garantizar cobertura de cada comuna.
    sort_cols = [c for c in ["comuna_cod", "id_actividad", "fila_origen"] if c in df.columns]
    work = df.sort_values(sort_cols).copy() if sort_cols else df.copy()

    for idx, row in work.iterrows():
        bloque = str(row.get("bloque_comunidad") or "").strip()
        if bloque != "SAT-C":
            continue

        comuna_raw = row.get("comuna_cod")
        if pd.isna(comuna_raw):
            work.at[idx, "nombre_satc"] = None
            continue

        comuna = int(comuna_raw)
        if comuna not in catalogo_por_comuna:
            # Comunas fuera del catalogo SAT-C vigente.
            work.at[idx, "nombre_satc"] = None
            continue

        canonical_list = catalogo_por_comuna[comuna]
        raw_name = row.get("nombre_satc")
        key = _norm_text(raw_name)

        mapped = None

        # 1) Match exacto al canónico por comuna.
        if key in canonical_norm[comuna]:
            mapped = canonical_norm[comuna][key]

        # 2) Alias por comuna.
        if mapped is None and key in alias_by_comuna.get(comuna, {}):
            mapped = alias_by_comuna[comuna][key]

        # 3) Match blando por inclusión de texto.
        if mapped is None and key:
            for k_can, name_can in canonical_norm[comuna].items():
                if key in k_can or k_can in key:
                    mapped = name_can
                    break

        # 4) Ambiguos o no mapeados: conservar el valor original para no
        # inventar una correspondencia que luego distorsione el hecho.
        if mapped is None:
            if key and "todos" in key and "sat" in key:
                mapped = None
            else:
                mapped = str(raw_name).strip() if pd.notna(raw_name) and str(raw_name).strip() else None

        work.at[idx, "nombre_satc"] = mapped

    if sort_cols:
        work = work.sort_index()

    return work


def main() -> None:
    print("=" * 80)
    print("REGENERAR PUENTE SATC - 37 SATC")
    print("=" * 80)

    modelo_file = ROOT_DIR / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"

    try:
        satc_df = pd.read_excel(modelo_file, sheet_name="Dim_SATC")
        print(f"✓ Dim_SATC: {len(satc_df)} SATC")
    except Exception as e:
        print(f"✗ Error cargando Dim_SATC: {e}")
        raise SystemExit(1)

    try:
        hechos_df = pd.read_excel(modelo_file, sheet_name="Hecho_Participacion_General")
        print(f"✓ Hecho_Participacion_General: {len(hechos_df)} registros")
    except Exception as e:
        print(f"✗ Error cargando hechos: {e}")
        raise SystemExit(1)

    print("\n" + "=" * 80)
    print("CREAR TABLA PUENTE")
    print("=" * 80)

    puente_df = satc_df[["SATC_ID", "Comuna_Cod"]].copy()
    puente_df = puente_df.sort_values(["Comuna_Cod", "SATC_ID"]).reset_index(drop=True)
    print(f"\n✓ Tabla puente: {len(puente_df)} relaciones")

    satc_df_sorted = satc_df.copy()
    satc_df_sorted["_satc_order"] = pd.to_numeric(satc_df_sorted["SATC_ID"], errors="coerce").fillna(0).astype(int)
    satc_primario = satc_df_sorted.sort_values(["Comuna_Cod", "_satc_order"]).drop_duplicates("Comuna_Cod")[["Comuna_Cod", "SATC_ID"]].copy()
    satc_primario.rename(columns={"SATC_ID": "SATC_ID_Primario"}, inplace=True)
    print(f"✓ SATC primario: {len(satc_primario)} comunas")

    print("\n" + "=" * 80)
    print("ENRIQUECER HECHOS")
    print("=" * 80)

    if "satc_id" in hechos_df.columns:
        hechos_df.drop("satc_id", axis=1, inplace=True)

    hechos_actualizado = hechos_df.merge(
        satc_primario,
        left_on="comuna_cod",
        right_on="Comuna_Cod",
        how="left",
    )
    hechos_actualizado.rename(columns={"SATC_ID_Primario": "satc_id"}, inplace=True)
    hechos_actualizado.drop("Comuna_Cod", axis=1, inplace=True)

    hechos_actualizado = _normalize_nombre_satc_in_hechos(hechos_actualizado, satc_df)

    hechos_con_satc = hechos_actualizado["satc_id"].notna().sum()
    cobertura = hechos_con_satc / len(hechos_actualizado) * 100

    satc_mask = hechos_actualizado.get("bloque_comunidad").astype(str).str.strip().eq("SAT-C")
    satc_unicos_hecho = hechos_actualizado.loc[satc_mask, "nombre_satc"].dropna().astype(str).str.strip().nunique()

    print("\n✓ Hechos enriquecidos:")
    print(f"  Con satc_id: {hechos_con_satc} / {len(hechos_actualizado)} ({cobertura:.1f}%)")
    print(f"  Distinct nombre_satc en bloque SAT-C: {satc_unicos_hecho}")

    print("\n" + "=" * 80)
    print("GUARDAR CAMBIOS")
    print("=" * 80)

    with pd.ExcelWriter(modelo_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        hechos_actualizado.to_excel(writer, sheet_name="Hecho_Participacion_General", index=False)
        puente_df.to_excel(writer, sheet_name="Puente_SATC_Comuna", index=False)

    print("\n✓ Hecho_Participacion_General (actualizada con satc_id + nombre_satc normalizado)")
    print("✓ Puente_SATC_Comuna (regenerada)")

    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(
        f"""
✓ SATC:                    {len(satc_df)}
✓ Comunas:                 {satc_df["Comuna_Cod"].nunique()}
✓ Relaciones en puente:    {len(puente_df)}
✓ Hechos con satc_id:      {hechos_con_satc} ({cobertura:.1f}%)
✓ SAT-C distintos en hecho: {satc_unicos_hecho}

Cambios en Excel:
  - Dim_SATC: {len(satc_df)} registros
  - Puente_SATC_Comuna: {len(puente_df)} relaciones
  - Hecho_Participacion_General: satc_id actualizada
  - Hecho_Participacion_General: nombre_satc normalizado al catalogo vigente

Archivo: {modelo_file}
"""
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
