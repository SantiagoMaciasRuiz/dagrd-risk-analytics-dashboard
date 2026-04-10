#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE_DIR / "data" / "source" / "Reporte de actividades equipo social 2026 (1).xlsx"
OUTPUT_FILE = BASE_DIR / "data" / "model" / "Participantes_Generales_Reporte_2026.xlsx"
TARGET_SHEET = "Tablas dinámicas"

NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
RID_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(value: str) -> str:
    value = _strip_accents(str(value or "")).lower().strip()
    return re.sub(r"\s+", " ", value)


def _to_int(value: str) -> int | None:
    value = str(value or "").strip()
    if not value:
        return None
    value = value.replace(".", "").replace(",", "")
    try:
        return int(float(value))
    except ValueError:
        return None


def _col_to_index(col: str) -> int:
    idx = 0
    for ch in col:
        if ch.isalpha():
            idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx


def _split_ref(cell_ref: str) -> Tuple[int | None, int | None]:
    match = re.match(r"([A-Z]+)(\d+)", cell_ref)
    if not match:
        return None, None
    return _col_to_index(match.group(1)), int(match.group(2))


def _read_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    shared: List[str] = []
    if "xl/sharedStrings.xml" not in zf.namelist():
        return shared

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", NS_MAIN):
        text_node = si.find("m:t", NS_MAIN)
        if text_node is not None and text_node.text is not None:
            shared.append(text_node.text)
            continue

        rich_text = [t.text for t in si.findall(".//m:t", NS_MAIN) if t.text]
        shared.append("".join(rich_text))
    return shared


def _get_sheet_xml_target(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("r:Relationship", NS_REL)}

    sheets = workbook.find("m:sheets", NS_MAIN)
    if sheets is None:
        raise RuntimeError("No se encontro la seccion sheets en el workbook.")

    for sheet in sheets.findall("m:sheet", NS_MAIN):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(RID_NS)
            target = rel_map.get(rel_id, "")
            if not target:
                break
            return target if target.startswith("xl/") else f"xl/{target}"

    raise RuntimeError(f"No se encontro la hoja '{sheet_name}' en el archivo de reporte.")


def _read_sheet_rows(zf: zipfile.ZipFile, target_xml: str, shared: List[str], max_cols: int = 6) -> List[Tuple[int, List[str]]]:
    root = ET.fromstring(zf.read(target_xml))
    data = root.find("m:sheetData", NS_MAIN)
    if data is None:
        return []

    out: List[Tuple[int, List[str]]] = []
    for row in data.findall("m:row", NS_MAIN):
        row_number = int(row.attrib.get("r", "0"))
        values = [""] * max_cols

        for cell in row.findall("m:c", NS_MAIN):
            ref = cell.attrib.get("r", "")
            col_idx, _ = _split_ref(ref)
            if col_idx is None or col_idx < 1 or col_idx > max_cols:
                continue

            cell_type = cell.attrib.get("t")
            value = ""

            if cell_type == "inlineStr":
                inline_node = cell.find("m:is", NS_MAIN)
                if inline_node is not None:
                    text_node = inline_node.find("m:t", NS_MAIN)
                    if text_node is not None and text_node.text is not None:
                        value = text_node.text
            else:
                value_node = cell.find("m:v", NS_MAIN)
                if value_node is not None and value_node.text is not None:
                    raw = value_node.text
                    if cell_type == "s":
                        try:
                            value = shared[int(raw)]
                        except (ValueError, IndexError):
                            value = raw
                    else:
                        value = raw

            values[col_idx - 1] = str(value).strip() if value is not None else ""

        if any(v != "" for v in values):
            out.append((row_number, values))

    return out


def _map_seccion(instancia: str) -> str:
    value = _normalize_text(instancia)
    if "comunit" in value:
        return "Comunitaria"
    if "empres" in value:
        return "Empresarial"
    if "instit" in value or "gestion interna" in value or "pdl" in value:
        return "Institucional"
    if "educ" in value or "primera infancia" in value or "buen comienzo" in value:
        return "Educativa"
    return "Otros"


def extract_general_participation() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not REPORT_FILE.exists():
        raise FileNotFoundError(f"No existe archivo de reporte: {REPORT_FILE}")

    with zipfile.ZipFile(REPORT_FILE, "r") as zf:
        shared = _read_shared_strings(zf)
        target = _get_sheet_xml_target(zf, TARGET_SHEET)
        rows = _read_sheet_rows(zf, target, shared, max_cols=6)

    header_idx = -1
    for idx, (_, values) in enumerate(rows):
        c1 = _normalize_text(values[0])
        c2 = _normalize_text(values[1])
        c3 = _normalize_text(values[2])
        if c1 == "instancia" and "cuenta de actividades" in c2 and "participaciones" in c3:
            header_idx = idx
            break

    if header_idx == -1:
        raise RuntimeError("No se encontro el bloque principal de instancia en la hoja de tablas dinamicas.")

    detail_rows: List[Dict[str, object]] = []
    total_general_actividades: int | None = None
    total_general_participaciones: int | None = None

    start_row_number = rows[header_idx + 1][0] if header_idx + 1 < len(rows) else None

    for row_number, values in rows[header_idx + 1 :]:
        instancia = values[0].strip()
        if not instancia:
            continue

        if _normalize_text(instancia).startswith("actividades y participacion"):
            break

        actividades = _to_int(values[1])
        participaciones = _to_int(values[2])

        if _normalize_text(instancia) == "total general":
            total_general_actividades = actividades
            total_general_participaciones = participaciones
            break

        if actividades is None and participaciones is None:
            continue

        detail_rows.append(
            {
                "orden_fila": len(detail_rows) + 1,
                "fila_origen": row_number,
                "instancia_origen": instancia,
                "seccion_tablero": _map_seccion(instancia),
                "cuenta_actividades": actividades,
                "participaciones": participaciones,
                "fuente_archivo": REPORT_FILE.name,
                "fuente_hoja": TARGET_SHEET,
            }
        )

    if not detail_rows:
        raise RuntimeError("No se encontraron filas de detalle para el bloque de participacion general.")

    detail_df = pd.DataFrame(detail_rows)

    agg_df = (
        detail_df.groupby("seccion_tablero", dropna=False, as_index=False)[["cuenta_actividades", "participaciones"]]
        .sum(min_count=1)
        .sort_values("seccion_tablero")
        .reset_index(drop=True)
    )

    sum_acts = int(detail_df["cuenta_actividades"].fillna(0).sum())
    sum_parts = int(detail_df["participaciones"].fillna(0).sum())

    control_df = pd.DataFrame(
        [
            {
                "archivo_origen": REPORT_FILE.name,
                "hoja_origen": TARGET_SHEET,
                "fila_header_bloque": rows[header_idx][0],
                "fila_inicio_detalle": start_row_number,
                "total_general_actividades": total_general_actividades,
                "total_general_participaciones": total_general_participaciones,
                "suma_detalle_actividades": sum_acts,
                "suma_detalle_participaciones": sum_parts,
                "coinciden_totales": (
                    "SI"
                    if total_general_actividades == sum_acts and total_general_participaciones == sum_parts
                    else "NO"
                ),
                "filas_detalle_extraidas": len(detail_df),
            }
        ]
    )

    return detail_df, agg_df, control_df


def main() -> None:
    detail_df, agg_df, control_df = extract_general_participation()

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        detail_df.to_excel(writer, sheet_name="Participacion_General_Detalle", index=False)
        agg_df.to_excel(writer, sheet_name="Participacion_General_Seccion", index=False)
        control_df.to_excel(writer, sheet_name="Control_Extraccion", index=False)

    print(f"OK: archivo generado en {OUTPUT_FILE}")
    print(f"- Participacion_General_Detalle: {detail_df.shape[0]} filas x {detail_df.shape[1]} columnas")
    print(f"- Participacion_General_Seccion: {agg_df.shape[0]} filas x {agg_df.shape[1]} columnas")
    print(f"- Control_Extraccion: {control_df.shape[0]} filas x {control_df.shape[1]} columnas")


if __name__ == "__main__":
    main()
