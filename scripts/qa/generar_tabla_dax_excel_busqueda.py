#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
IN_CSV = BASE / "data" / "reference" / "powerbi_medidas_mapeo_2026.csv"
OUT_CSV = BASE / "data" / "reference" / "tabla_dax_vs_excel_busqueda_2026.csv"
OUT_MD = BASE / "docs" / "core" / "TABLA_DAX_VS_EXCEL_BUSQUEDA_2026.md"

MODEL_TO_EXCEL = {
    "participantes": ("Sheet1", "Indique el número de personas participantes"),
    "impacto_indirecto": ("Sheet1", "Cantidad de personas impactadas indirectamente"),
    "seccion_tablero": ("Sheet1", "Instancia"),
    "bloque_comunidad": ("Sheet1", "Público objeto en comunidad (clasificación en modelo)"),
    "bloque_educacion": ("Sheet1", "Público objeto en educación / nivel educativo (clasificación en modelo)"),
    "bloque_empresarial": ("Sheet1", "Público objeto en empresarial / nombre COSEGRD (clasificación en modelo)"),
    "bloque_institucional": ("Sheet1", "Instancia + actividad institucional (clasificación en modelo)"),
    "subbloque_institucional": ("Sheet1", "Actividad institucional (clasificación en modelo)"),
    "ambito_institucional": ("Sheet1", "Instancia (derivado a ámbito en modelo)"),
    "grupo_ambito_comparacion": ("Sheet1", "Instancia (derivado a grupo ámbito en modelo)"),
    "publico_comunidad": ("Sheet1", "Público objeto en comunidad"),
    "nombre_satc": ("Sheet1", "Nombre SAT-C"),
    "entidades_asociadas": ("Sheet1", "Entidad/Institución asociada"),
    "actividad_educacion": ("Sheet1", "Actividad asociada a la instancia Educativa"),
    "instancia": ("Sheet1", "Instancia"),
    "fecha": ("Sheet1", "Fecha en la que se realizó la actividad"),
    "mes_num": ("Sheet1", "Fecha en la que se realizó la actividad (mes)"),
    "anio": ("Sheet1", "Fecha en la que se realizó la actividad (año)"),
    "personas_participantes": ("Simulacros", "Número de personas participantes"),
    "sector_tablero": ("Simulacros", "Sector pertenece"),
    "nombre_entidad": ("Simulacros", "Nombre completo"),
    "pri_infanc": ("Sheet1", "Primera infancia"),
    "nino_adole": ("Sheet1", "Niñez y adolescencia"),
    "juventud": ("Sheet1", "Juventud"),
    "adulto": ("Sheet1", "Adulto"),
    "adulto_may": ("Sheet1", "Adulto mayor"),
    "discapacid": ("Sheet1", "Discapacidad"),
    "afrodescen": ("Sheet1", "Afrodescendiente"),
    "campesino": ("Sheet1", "Campesino"),
    "pob_indige": ("Sheet1", "Población indígena"),
    "pob_rom": ("Sheet1", "Población ROM"),
    "pob_victim": ("Sheet1", "Población víctima"),
    "pob_migran": ("Sheet1", "Población migrante"),
    "pob_lgtbi": ("Sheet1", "Población LGTBI"),
    "valor": ("Sheet1", "Campos demográficos (normalizados al modelo)"),
}


def extract_model_columns(columnas_modelo: str) -> list[str]:
    cols = []
    for token in str(columnas_modelo or "").split("|"):
        token = token.strip()
        m = re.search(r"\[([^\]]+)\]", token)
        if m:
            cols.append(m.group(1).strip())
    return list(dict.fromkeys(cols))


def extract_filters(filtros_dax: str) -> list[tuple[str, str]]:
    pairs = []
    text = str(filtros_dax or "")
    for m in re.finditer(r"\[([^\]]+)\]\s*=\s*\"([^\"]+)\"", text):
        pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def main() -> None:
    rows = []
    with IN_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            medida = r.get("medida", "")
            cols = extract_model_columns(r.get("columnas_modelo", ""))
            filters = extract_filters(r.get("filtros_dax", ""))

            # hoja/columna principal a buscar
            hojas = []
            columnas_excel = []
            for c in cols:
                if c in MODEL_TO_EXCEL:
                    h, ce = MODEL_TO_EXCEL[c]
                    hojas.append(h)
                    columnas_excel.append(ce)

            hoja_principal = hojas[0] if hojas else "Sheet1"
            columna_principal = columnas_excel[0] if columnas_excel else "Revisar en modelo (columna derivada)"

            if not filters:
                rows.append(
                    {
                        "medida_dax": medida,
                        "hoja_excel": hoja_principal,
                        "columna_principal_buscar": columna_principal,
                        "filtro_columna_excel": "(sin filtro fijo)",
                        "filtro_valor": "(sin filtro fijo)",
                        "columnas_apoyo": " | ".join(columnas_excel) if columnas_excel else "",
                        "tipo_calculo": "COUNTROWS/SUM/DISTINCTCOUNT según medida",
                    }
                )
            else:
                for fc, fv in filters:
                    if fc in MODEL_TO_EXCEL:
                        hf, cf = MODEL_TO_EXCEL[fc]
                    else:
                        hf, cf = (hoja_principal, f"{fc} (derivada en modelo)")

                    rows.append(
                        {
                            "medida_dax": medida,
                            "hoja_excel": hf,
                            "columna_principal_buscar": columna_principal,
                            "filtro_columna_excel": cf,
                            "filtro_valor": fv,
                            "columnas_apoyo": " | ".join(columnas_excel) if columnas_excel else "",
                            "tipo_calculo": "COUNTROWS/SUM/DISTINCTCOUNT según medida",
                        }
                    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "medida_dax",
                "hoja_excel",
                "columna_principal_buscar",
                "filtro_columna_excel",
                "filtro_valor",
                "columnas_apoyo",
                "tipo_calculo",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    # markdown resumen legible
    preview = rows[:60]
    lines = [
        "# Tabla DAX vs Excel para validación",
        "",
        "Archivo fuente para validar: data/source/Reporte de actividades equipo social 2026 (1).xlsx",
        "",
        f"Filas generadas: {len(rows)}",
        "",
        "## Tabla",
        "| Medida DAX | Hoja Excel | Columna principal | Columna filtro | Valor filtro |",
        "|---|---|---|---|---|",
    ]
    for r in preview:
        lines.append(
            f"| {r['medida_dax']} | {r['hoja_excel']} | {r['columna_principal_buscar']} | {r['filtro_columna_excel']} | {r['filtro_valor']} |"
        )

    lines.extend(
        [
            "",
            "Nota: el detalle completo está en data/reference/tabla_dax_vs_excel_busqueda_2026.csv.",
            "",
            "## Cómo usar",
            "1. Filtra por medida_dax en el CSV.",
            "2. Abre la hoja indicada (Sheet1 o Simulacros).",
            "3. Aplica filtro en filtro_columna_excel = filtro_valor.",
            "4. Calcula suma/conteo según tipo de medida en Power BI.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK CSV: {OUT_CSV}")
    print(f"OK MD: {OUT_MD}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
