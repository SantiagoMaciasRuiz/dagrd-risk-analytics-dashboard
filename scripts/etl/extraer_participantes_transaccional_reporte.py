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
OUTPUT_FILE = BASE_DIR / "data" / "model" / "Participantes_Generales_Transaccional_2026.xlsx"

SHEET_DETALLE = "Sheet1"
SHEET_PIVOT = "Tablas dinámicas"

NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
RID_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

MONTHS_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


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


def _to_float(value: str) -> float | None:
    value = str(value or "").strip()
    if not value:
        return None
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _parse_excel_date(value: str) -> pd.Timestamp | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    # Excel serial date (1900 system)
    serial = _to_float(str(value))
    if serial is not None:
        try:
            dt = pd.to_datetime(serial, unit="D", origin="1899-12-30", errors="coerce")
            return dt.normalize() if pd.notna(dt) else None
        except Exception:
            pass

    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.normalize() if pd.notna(parsed) else None


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
        raise RuntimeError("No se encontró la sección sheets del workbook.")

    for sheet in sheets.findall("m:sheet", NS_MAIN):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(RID_NS)
            target = rel_map.get(rel_id, "")
            if not target:
                break
            return target if target.startswith("xl/") else f"xl/{target}"

    raise RuntimeError(f"No se encontró la hoja '{sheet_name}'.")


def _read_sheet_rows(zf: zipfile.ZipFile, target_xml: str, shared: List[str]) -> List[Tuple[int, Dict[int, str]]]:
    root = ET.fromstring(zf.read(target_xml))
    data = root.find("m:sheetData", NS_MAIN)
    if data is None:
        return []

    out: List[Tuple[int, Dict[int, str]]] = []

    for row in data.findall("m:row", NS_MAIN):
        row_number = int(row.attrib.get("r", "0"))
        row_map: Dict[int, str] = {}

        for cell in row.findall("m:c", NS_MAIN):
            ref = cell.attrib.get("r", "")
            col_idx, _ = _split_ref(ref)
            if col_idx is None:
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

            if value is not None and str(value).strip() != "":
                row_map[col_idx] = str(value).strip()

        if row_map:
            out.append((row_number, row_map))

    return out


def _find_col(headers: Dict[int, str], contains_all: List[str], contains_any: List[str] | None = None) -> int:
    contains_any = contains_any or []
    for idx, name in headers.items():
        n = _normalize_text(name)
        if all(k in n for k in contains_all):
            if not contains_any or any(k in n for k in contains_any):
                return idx
    raise RuntimeError(f"No se encontró columna para criterio: all={contains_all}, any={contains_any}")


def _extract_pivot_totals(sheet2_rows: List[Tuple[int, Dict[int, str]]]) -> Tuple[int | None, int | None]:
    normalized_rows: List[Tuple[int, str, str, str]] = []
    for rnum, row in sheet2_rows:
        c1 = row.get(1, "")
        c2 = row.get(2, "")
        c3 = row.get(3, "")
        normalized_rows.append((rnum, c1, c2, c3))

    header_pos = -1
    for i, (_, c1, c2, c3) in enumerate(normalized_rows):
        if _normalize_text(c1) == "instancia" and "cuenta de actividades" in _normalize_text(c2) and "participaciones" in _normalize_text(c3):
            header_pos = i
            break

    if header_pos == -1:
        return None, None

    for _, c1, c2, c3 in normalized_rows[header_pos + 1 :]:
        if _normalize_text(c1) == "total general":
            return _to_int(c2), _to_int(c3)

    return None, None


def build_transaccional_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not REPORT_FILE.exists():
        raise FileNotFoundError(f"No existe archivo: {REPORT_FILE}")

    with zipfile.ZipFile(REPORT_FILE, "r") as zf:
        shared = _read_shared_strings(zf)

        sheet1_target = _get_sheet_xml_target(zf, SHEET_DETALLE)
        sheet2_target = _get_sheet_xml_target(zf, SHEET_PIVOT)

        sheet1_rows = _read_sheet_rows(zf, sheet1_target, shared)
        sheet2_rows = _read_sheet_rows(zf, sheet2_target, shared)

    if not sheet1_rows:
        raise RuntimeError("No se encontraron filas en Sheet1.")

    header_row_num, header_map = sheet1_rows[0]
    if header_row_num != 1:
        raise RuntimeError("La fila de encabezados de Sheet1 no esta en la fila 1.")

    idx_nata = _find_col(header_map, ["nata"])
    idx_fecha = _find_col(header_map, ["fecha", "actividad"])
    idx_comuna = _find_col(header_map, ["comuna", "corregimiento"])
    idx_instancia = _find_col(header_map, ["instancia"])
    idx_participantes = _find_col(header_map, ["numero", "personas", "participantes"])
    idx_impacto = _find_col(header_map, ["impactadas", "indirectamente"])
    idx_mujeres = _find_col(header_map, ["mujeres"])
    idx_hombres = _find_col(header_map, ["hombres"])
    idx_ninos = _find_col(header_map, ["ninos"], ["nino", "niños"])

    idx_pri_inf = _find_col(header_map, ["primera infancia"])
    idx_nino_adole = _find_col(header_map, ["ninez", "adolescencia"])
    idx_juventud = _find_col(header_map, ["juventud"])
    idx_adulto = _find_col(header_map, ["adulto", "29-54"])
    idx_adulto_may = _find_col(header_map, ["adulto mayor"])
    idx_discap = _find_col(header_map, ["discapacidad"])
    idx_afro = _find_col(header_map, ["afrodescendiente"])
    idx_camp = _find_col(header_map, ["campesinos"])
    idx_vict = _find_col(header_map, ["poblacion", "victima"])
    idx_migr = _find_col(header_map, ["poblacion", "migrante"])
    idx_lgtbi = _find_col(header_map, ["poblacion", "lgtbi"])
    idx_indig = _find_col(header_map, ["poblacion", "indigena"])
    idx_rom = _find_col(header_map, ["poblacion", "rom"])

    records: List[Dict[str, object]] = []

    for row_num, row in sheet1_rows[1:]:
        id_actividad = _to_int(row.get(idx_nata, ""))
        instancia = row.get(idx_instancia, "").strip()
        comuna_cod = _to_int(row.get(idx_comuna, ""))
        participantes = _to_int(row.get(idx_participantes, ""))

        fecha = _parse_excel_date(row.get(idx_fecha, ""))

        # Filtro mínimo de registro útil
        if id_actividad is None and participantes is None and not instancia:
            continue

        record = {
            "id_actividad": id_actividad,
            "fila_origen": row_num,
            "fecha": fecha,
            "anio": int(fecha.year) if pd.notna(fecha) else None,
            "mes_num": int(fecha.month) if pd.notna(fecha) else None,
            "mes_nombre": MONTHS_ES.get(int(fecha.month), None) if pd.notna(fecha) else None,
            "comuna_cod": comuna_cod,
            "instancia": instancia if instancia else None,
            "seccion_tablero": _map_seccion(instancia),
            "participantes": participantes,
            "impacto_indirecto": _to_int(row.get(idx_impacto, "")),
            "mujeres": _to_int(row.get(idx_mujeres, "")),
            "hombres": _to_int(row.get(idx_hombres, "")),
            "ninos": _to_int(row.get(idx_ninos, "")),
            "pri_infanc": _to_int(row.get(idx_pri_inf, "")),
            "nino_adole": _to_int(row.get(idx_nino_adole, "")),
            "juventud": _to_int(row.get(idx_juventud, "")),
            "adulto": _to_int(row.get(idx_adulto, "")),
            "adulto_may": _to_int(row.get(idx_adulto_may, "")),
            "discapacid": _to_int(row.get(idx_discap, "")),
            "afrodescen": _to_int(row.get(idx_afro, "")),
            "campesino": _to_int(row.get(idx_camp, "")),
            "pob_victim": _to_int(row.get(idx_vict, "")),
            "pob_migran": _to_int(row.get(idx_migr, "")),
            "pob_lgtbi": _to_int(row.get(idx_lgtbi, "")),
            "pob_indige": _to_int(row.get(idx_indig, "")),
            "pob_rom": _to_int(row.get(idx_rom, "")),
            "fuente_archivo": REPORT_FILE.name,
            "fuente_hoja": SHEET_DETALLE,
        }
        records.append(record)

    fact_df = pd.DataFrame(records)

    if fact_df.empty:
        raise RuntimeError("La tabla transaccional quedo vacia. Revisar archivo fuente.")

    by_seccion_df = (
        fact_df.groupby("seccion_tablero", dropna=False, as_index=False)[["id_actividad", "participantes"]]
        .agg({"id_actividad": "count", "participantes": "sum"})
        .rename(columns={"id_actividad": "actividades"})
        .sort_values("seccion_tablero")
        .reset_index(drop=True)
    )

    by_comuna_df = (
        fact_df.groupby("comuna_cod", dropna=False, as_index=False)[["id_actividad", "participantes"]]
        .agg({"id_actividad": "count", "participantes": "sum"})
        .rename(columns={"id_actividad": "actividades"})
        .sort_values("comuna_cod")
        .reset_index(drop=True)
    )

    by_fecha_df = (
        fact_df.groupby("fecha", dropna=False, as_index=False)[["id_actividad", "participantes"]]
        .agg({"id_actividad": "count", "participantes": "sum"})
        .rename(columns={"id_actividad": "actividades"})
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    pivot_acts, pivot_parts = _extract_pivot_totals(sheet2_rows)

    total_actividades = int(fact_df["id_actividad"].count())
    total_participantes = int(fact_df["participantes"].fillna(0).sum())

    control_df = pd.DataFrame(
        [
            {
                "archivo_origen": REPORT_FILE.name,
                "hoja_origen_detalle": SHEET_DETALLE,
                "hoja_origen_pivot": SHEET_PIVOT,
                "filas_transaccionales": int(fact_df.shape[0]),
                "total_actividades_transaccional": total_actividades,
                "total_participantes_transaccional": total_participantes,
                "total_actividades_pivot": pivot_acts,
                "total_participantes_pivot": pivot_parts,
                "coinciden_actividades": "SI" if pivot_acts == total_actividades else "NO",
                "coinciden_participantes": "SI" if pivot_parts == total_participantes else "NO",
            }
        ]
    )

    return fact_df, by_seccion_df, by_comuna_df, by_fecha_df, control_df


def main() -> None:
    fact_df, by_seccion_df, by_comuna_df, by_fecha_df, control_df = build_transaccional_tables()

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        fact_df.to_excel(writer, sheet_name="Hecho_Participacion_General", index=False)
        by_seccion_df.to_excel(writer, sheet_name="General_Por_Seccion", index=False)
        by_comuna_df.to_excel(writer, sheet_name="General_Por_Comuna", index=False)
        by_fecha_df.to_excel(writer, sheet_name="General_Por_Fecha", index=False)
        control_df.to_excel(writer, sheet_name="Control_Extraccion", index=False)

    print(f"OK: archivo generado en {OUTPUT_FILE}")
    print(f"- Hecho_Participacion_General: {fact_df.shape[0]} filas x {fact_df.shape[1]} columnas")
    print(f"- General_Por_Seccion: {by_seccion_df.shape[0]} filas x {by_seccion_df.shape[1]} columnas")
    print(f"- General_Por_Comuna: {by_comuna_df.shape[0]} filas x {by_comuna_df.shape[1]} columnas")
    print(f"- General_Por_Fecha: {by_fecha_df.shape[0]} filas x {by_fecha_df.shape[1]} columnas")
    print(f"- Control_Extraccion: {control_df.shape[0]} filas x {control_df.shape[1]} columnas")


if __name__ == "__main__":
    main()
