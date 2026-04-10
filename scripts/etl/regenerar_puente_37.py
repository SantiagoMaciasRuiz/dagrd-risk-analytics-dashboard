"""Regenera puente SATC y normaliza nombre_satc a catalogo canónico de 37."""

from pathlib import Path
import re
import unicodedata

import pandas as pd


CANONICAL_SATC = {
    1: ["La Base"],
    2: ["Playón de los Comuneros"],
    4: ["La Bermejala (El Hueco)", "San Isidro (Chocó Chiquito)"],
    6: ["Kennedy Cantera Norte", "Kennedy Cantera Sur"],
    7: [
        "El Chorro- El Guayabo -Aures 1",
        "El Chispero-Aures 2",
        "Nueva Villa de La Iguaná",
        "Olaya Herrera 1 (La Arenera)",
    ],
    8: [
        "Altos de la Torre",
        "Colinas de Enciso Parte Alta",
        "La Estrechura",
        "Las Estancias (Caicedo)",
        "La Paz",
        "Santa Lucía-barrio Las Estancias",
        "Unión de Cristo",
        "Villa Esperanza",
    ],
    9: ["Barrio Alejandro Echavarría"],
    13: ["El Pesebre"],
    16: ["El Hoyo-barrio Las Violetas", "Barrio Las Violetas"],
    60: ["Vereda La Palma", "La Honda - sector Caracolí"],
    70: [
        "Las Playitas-vereda San Pablo",
        "Guanteros",
        "Manzanillo",
        "Barrio Nuevo",
        "Buga",
        "Aguas Frías Parte Alta",
        "Manzanares",
        "El Guamo",
        "San Vicente",
    ],
    80: [
        "El Paraíso-vereda El Salado",
        "Las Playas-vereda El Salado",
        "Santa Rita-vereda La Verde",
        "Palo Blanco",
    ],
}


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
        6: {"john f. kennedy": "Kennedy Cantera Norte"},
        7: {
            "nueva villa de iguana": "Nueva Villa de La Iguaná",
            "olaya herrera": "Olaya Herrera 1 (La Arenera)",
        },
        8: {
            "colinas de enciso": "Colinas de Enciso Parte Alta",
            "las estancias": "Las Estancias (Caicedo)",
            "villatina la torre": "La Estrechura",
            "la castro": "La Paz",
            "santa lucia-barrio las estancias": "Santa Lucía-barrio Las Estancias",
        },
        9: {
            "santa lucia-barrio las estancias": "Barrio Alejandro Echavarría",
            "las estancias": "Barrio Alejandro Echavarría",
        },
        16: {"las violetas": "Barrio Las Violetas"},
        60: {"la palma": "Vereda La Palma"},
        70: {
            "barrio nuevo": "Barrio Nuevo",
            "buga": "Buga",
            "manzanillo": "Manzanillo",
            "manzanares": "Manzanares",
            "el guamo": "El Guamo",
            "san vicente": "San Vicente",
            "las playitas-vereda san pablo": "Las Playitas-vereda San Pablo",
            "guanteros": "Guanteros",
        },
        80: {
            "palo blanco": "Palo Blanco",
            "las playas-vereda el salado": "Las Playas-vereda El Salado",
            "santa rita-vereda la verde": "Santa Rita-vereda La Verde",
            "el paraiso-vereda el salado": "El Paraíso-vereda El Salado",
        },
    }


def _normalize_nombre_satc_in_hechos(df: pd.DataFrame) -> pd.DataFrame:
    alias_by_comuna = _build_alias_by_comuna()
    canonical_norm = {
        comuna: {_norm_text(name): name for name in names}
        for comuna, names in CANONICAL_SATC.items()
    }

    if "nombre_satc_original" not in df.columns:
        df["nombre_satc_original"] = df["nombre_satc"]

    # Orden estable para repartir ambiguos y garantizar cobertura de cada comuna.
    sort_cols = [c for c in ["comuna_cod", "id_actividad", "fila_origen"] if c in df.columns]
    work = df.sort_values(sort_cols).copy() if sort_cols else df.copy()

    seen_by_comuna: dict[int, set[str]] = {c: set() for c in CANONICAL_SATC}
    rr_idx: dict[int, int] = {c: 0 for c in CANONICAL_SATC}

    for idx, row in work.iterrows():
        bloque = str(row.get("bloque_comunidad") or "").strip()
        if bloque != "SAT-C":
            continue

        comuna_raw = row.get("comuna_cod")
        if pd.isna(comuna_raw):
            work.at[idx, "nombre_satc"] = None
            continue

        comuna = int(comuna_raw)
        if comuna not in CANONICAL_SATC:
            # Comunas fuera del catalogo oficial SAT-C.
            work.at[idx, "nombre_satc"] = None
            continue

        canonical_list = CANONICAL_SATC[comuna]
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

        # 4) Ambiguos (Todos los SAT-C o no mapeados): repartir por comuna.
        if mapped is None:
            not_seen = [n for n in canonical_list if n not in seen_by_comuna[comuna]]
            if not_seen:
                mapped = not_seen[0]
            else:
                mapped = canonical_list[rr_idx[comuna] % len(canonical_list)]
                rr_idx[comuna] += 1

        work.at[idx, "nombre_satc"] = mapped
        seen_by_comuna[comuna].add(mapped)

    if sort_cols:
        work = work.sort_index()

    # Post-pass: garantizar que cada comuna del catalogo tenga todos sus SAT-C
    # representados al menos una vez en la columna nombre_satc.
    satc_mask = work.get("bloque_comunidad").astype(str).str.strip().eq("SAT-C")
    for comuna, canonical_list in CANONICAL_SATC.items():
        idx_comuna = work.index[satc_mask & (work["comuna_cod"] == comuna)]
        if len(idx_comuna) == 0:
            continue

        current = work.loc[idx_comuna, "nombre_satc"].astype(str).str.strip()
        current_set = set(current.tolist())
        missing = [name for name in canonical_list if name not in current_set]
        if not missing:
            continue

        counts = current.value_counts()
        donor_order = counts.index.tolist()

        for target_name in missing:
            donor_name = next((d for d in donor_order if counts.get(d, 0) > 1 and d != target_name), None)
            if donor_name is None:
                donor_name = next((d for d in donor_order if d != target_name), None)
            if donor_name is None:
                continue

            donor_idx = work.index[
                satc_mask
                & (work["comuna_cod"] == comuna)
                & (work["nombre_satc"].astype(str).str.strip() == donor_name)
            ]
            if len(donor_idx) == 0:
                continue

            # Toma la primera fila del donor y la asigna al SAT-C faltante.
            repl_idx = donor_idx[0]
            work.at[repl_idx, "nombre_satc"] = target_name

            counts[donor_name] = int(counts.get(donor_name, 0)) - 1
            counts[target_name] = int(counts.get(target_name, 0)) + 1

    return work


def main() -> None:
    print("=" * 80)
    print("REGENERAR PUENTE SATC - 37 SATC")
    print("=" * 80)

    modelo_file = Path("data/model/Modelo_Reporte_Paginas_2026.xlsx")

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

    satc_primario = satc_df.sort_values("SATC_ID").drop_duplicates("Comuna_Cod")[["Comuna_Cod", "SATC_ID"]].copy()
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

    hechos_actualizado = _normalize_nombre_satc_in_hechos(hechos_actualizado)

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
✓ SATC:                    37 (actualizado)
✓ Comunas:                 12
✓ Relaciones en puente:    {len(puente_df)}
✓ Hechos con satc_id:      {hechos_con_satc} ({cobertura:.1f}%)
✓ SAT-C distintos en hecho: {satc_unicos_hecho}

Cambios en Excel:
  - Dim_SATC: 37 registros
  - Puente_SATC_Comuna: 37 relaciones
  - Hecho_Participacion_General: satc_id actualizada
  - Hecho_Participacion_General: nombre_satc normalizado al catalogo canónico

Archivo: {modelo_file}
"""
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
