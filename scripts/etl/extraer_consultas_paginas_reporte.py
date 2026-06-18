#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata
import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import runpy

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Cargar configuración centralizada
config_file = Path(__file__).resolve().parent / "etl_config.json"
try:
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    raise RuntimeError(f"No se pudo leer el archivo de configuración etl_config.json: {e}")

# Configurar rutas y archivos
source_dir = BASE_DIR / config["paths"]["source_dir"]
source_pattern = config["paths"]["source_file_pattern"]

candidates = sorted(
    source_dir.glob(source_pattern),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)
if not candidates:
    # Fallback si no hay candidatos
    REPORT_FILE = source_dir / "Reporte de actividades equipo social 2026.xlsx"
else:
    REPORT_FILE = candidates[0]

OUTPUT_FILE = BASE_DIR / config["paths"]["model_output"]

SHEET_DETALLE = config["sheets"]["detalle"]
SHEET_PIVOT = config["sheets"]["pivot"]
SHEET_SIMULACROS = config["sheets"]["simulacros"]
SHEET_CAM = config["sheets"]["cam"]

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

MIN_VALID_DATE = pd.Timestamp("1900-01-01")

DEMOGRAPHIC_MAP = {
    "mujeres": ("Género", "Mujeres"),
    "hombres": ("Género", "Hombres"),
    "pri_infanc": ("Grupo Etario", "Primera infancia"),
    "nino_adole": ("Grupo Etario", "Niñez y adolescencia"),
    "juventud": ("Grupo Etario", "Juventud"),
    "adulto": ("Grupo Etario", "Adulto"),
    "adulto_may": ("Grupo Etario", "Adulto mayor"),
    "discapacid": ("Discapacidad", "Discapacidad"),
    "afrodescen": ("Etnico", "Afrodescendiente"),
    "campesino": ("Etnico", "Campesino"),
    "pob_victim": ("Etnico", "Población víctima"),
    "pob_migran": ("Etnico", "Población migrante"),
    "pob_lgtbi": ("Etnico", "Población LGTBI"),
    "pob_indige": ("Etnico", "Población indígena"),
    "pob_rom": ("Etnico", "Población ROM"),
}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_text(value: str) -> str:
    value = _strip_accents(str(value or "")).lower().strip()
    return re.sub(r"\s+", " ", value)


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "(en blanco)"}:
        return None
    return text


def _normalize_institucion_name(value: object) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    normalized = _strip_accents(text).upper()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None


def _is_aggregated_ies(value: object) -> bool:
    text = _normalize_text(value or "")
    if not text:
        return False
    patterns = [
        "todas las ies",
        "todas las instituciones de educacion superior",
        "todas las instituciones educativas de educacion superior",
    ]
    return any(p in text for p in patterns)


def _has_value(value: object) -> bool:
    return _clean_text(value) is not None


def _to_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return None
    text = text.replace(".", "").replace(",", "")
    try:
        return int(float(text))
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _parse_excel_date(value: object) -> pd.Timestamp | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    serial = _to_float(value)
    if serial is not None:
        try:
            dt = pd.to_datetime(serial, unit="D", origin="1899-12-30", errors="coerce")
            if pd.isna(dt):
                return None
            dt = dt.normalize()
            return dt if dt >= MIN_VALID_DATE else None
        except Exception:
            pass

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None

    parsed = parsed.normalize()
    return parsed if parsed >= MIN_VALID_DATE else None


def _map_seccion(instancia: str | None) -> str:
    value = _normalize_text(instancia or "")
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
            targ = target.lstrip('/')
            return targ if targ.startswith("xl/") else f"xl/{targ}"

    # Fallback: buscar hoja cuyo nombre contenga o empiece por el patrón solicitado (ignora mayúsculas/acentos)
    norm_target = sheet_name.lower()
    for sheet in sheets.findall("m:sheet", NS_MAIN):
        name = sheet.attrib.get("name", "")
        if norm_target in name.lower() or name.lower().startswith(norm_target):
            rel_id = sheet.attrib.get(RID_NS)
            target = rel_map.get(rel_id, "")
            if not target:
                break
            targ = target.lstrip('/')
            return targ if targ.startswith("xl/") else f"xl/{targ}"

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
        normalized = _normalize_text(name)
        if all(term in normalized for term in contains_all):
            if not contains_any or any(term in normalized for term in contains_any):
                return idx
    raise RuntimeError(f"No se encontró columna para criterio: all={contains_all}, any={contains_any}")


def _find_col_optional(headers: Dict[int, str], contains_all: List[str], contains_any: List[str] | None = None) -> int | None:
    """Find column but return None if not found (instead of raising error)."""
    contains_any = contains_any or []
    for idx, name in headers.items():
        normalized = _normalize_text(name)
        if all(term in normalized for term in contains_all):
            if not contains_any or any(term in normalized for term in contains_any):
                return idx
    return None


def _find_educacion_establecimiento_cols(headers: Dict[int, str]) -> Dict[int, int]:
    cols: Dict[int, int] = {}
    for idx, name in headers.items():
        normalized = _normalize_text(name)
        if "nombre del establecimiento educativo" not in normalized:
            continue
        match = re.search(r"comuna\s*(\d+)", normalized)
        if not match:
            continue
        comuna_code = int(match.group(1))
        cols[comuna_code] = idx
    return cols


def _find_sedes_bc_cols(headers: Dict[int, str]) -> Dict[int, int]:
    cols: Dict[int, int] = {}
    for idx, name in headers.items():
        normalized = _normalize_text(name)
        if "sedes de bc en comuna" not in normalized:
            continue
        match = re.search(r"comuna\s*(\d+)", normalized)
        if not match:
            continue
        comuna_code = int(match.group(1))
        cols[comuna_code] = idx
    return cols


def _extract_establecimiento_educativo(
    row: Dict[int, str],
    comuna_educacion_text: str | None,
    establecimiento_cols: Dict[int, int],
) -> str | None:
    comuna_cod = _parse_comuna_text_to_code(comuna_educacion_text)
    if comuna_cod is not None and comuna_cod in establecimiento_cols:
        selected = _clean_text(row.get(establecimiento_cols[comuna_cod], ""))
        if selected:
            return selected

    # Fallback: tomar el primer establecimiento reportado en columnas comuna X.
    for comuna_key in sorted(establecimiento_cols.keys()):
        candidate = _clean_text(row.get(establecimiento_cols[comuna_key], ""))
        if candidate:
            return candidate
    return None


def _parse_comuna_text_to_code(value: str | None) -> int | None:
    text = _clean_text(value)
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _extract_pivot_totals(sheet_rows: List[Tuple[int, Dict[int, str]]]) -> Tuple[int | None, int | None]:
    normalized_rows: List[Tuple[int, str, str, str]] = []
    for rnum, row in sheet_rows:
        normalized_rows.append((rnum, row.get(1, ""), row.get(2, ""), row.get(3, "")))

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


def _extract_cam_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, List[int]]]:
    cam_detalle_cols = [
        "cam_activo_id",
        "zona_cam",
        "empresa_cam",
        "empresa_cam_norm",
        "fuente_archivo",
        "fuente_hoja",
    ]
    cam_resumen_cols = ["cam_activo_id", "zona_cam", "empresas_unicas_zona"]
    cam_control_cols = [
        "cam_activos_total",
        "zonas_cam_total",
        "empresas_unicas_global",
        "empresas_unicas_suma_por_zona",
    ]

    try:
        cam_raw = pd.read_excel(REPORT_FILE, sheet_name=SHEET_CAM, header=None, engine="openpyxl")
    except Exception:
        return (
            pd.DataFrame(columns=cam_detalle_cols),
            pd.DataFrame(columns=cam_resumen_cols),
            pd.DataFrame(columns=cam_control_cols),
            {},
        )

    if cam_raw.empty or cam_raw.shape[1] < 3:
        return (
            pd.DataFrame(columns=cam_detalle_cols),
            pd.DataFrame(columns=cam_resumen_cols),
            pd.DataFrame(columns=cam_control_cols),
            {},
        )

    # Find the header row by searching for "CAM ACTIVOS" and "EMPRESAS" in the first 10 rows
    header_idx = None
    col_idx_activo = None
    col_idx_empresa = None
    col_idx_comuna = None
    for i in range(min(10, len(cam_raw))):
        row_vals = [str(x).strip().upper() for x in cam_raw.iloc[i].tolist()]
        if "CAM ACTIVOS" in row_vals and "EMPRESAS" in row_vals:
            header_idx = i
            col_idx_activo = row_vals.index("CAM ACTIVOS")
            col_idx_empresa = row_vals.index("EMPRESAS")
            # Buscar columna opcional de Comuna
            for idx, val in enumerate(row_vals):
                if "COMUNA" in val:
                    col_idx_comuna = idx
            break

    if header_idx is None:
        # Fallback to index 0, 1, 2 if headers aren't found
        col_idx_activo = 0
        col_idx_zona = 1
        col_idx_empresa = 2
        data_df = cam_raw.copy()
    else:
        # Zone column is assumed to be between active CAM and companies (usually col_idx_activo + 1)
        col_idx_zona = col_idx_activo + 1
        data_df = cam_raw.iloc[header_idx + 1:].copy()

    if col_idx_comuna is not None:
        cam_df = data_df[[col_idx_activo, col_idx_zona, col_idx_empresa, col_idx_comuna]].copy()
        cam_df.columns = ["cam_activo_raw", "zona_cam_raw", "empresa_cam_raw", "comuna_raw"]
    else:
        cam_df = data_df[[col_idx_activo, col_idx_zona, col_idx_empresa]].copy()
        cam_df.columns = ["cam_activo_raw", "zona_cam_raw", "empresa_cam_raw"]
        cam_df["comuna_raw"] = None

    for col in cam_df.columns:
        cam_df[col] = cam_df[col].map(_clean_text)

    cam_df = cam_df[cam_df[["cam_activo_raw", "zona_cam_raw", "empresa_cam_raw"]].notna().any(axis=1)].copy()
    if cam_df.empty:
        return (
            pd.DataFrame(columns=cam_detalle_cols),
            pd.DataFrame(columns=cam_resumen_cols),
            pd.DataFrame(columns=cam_control_cols),
            {},
        )

    cam_df["cam_activo_raw"] = cam_df["cam_activo_raw"].ffill()
    cam_df["zona_cam_raw"] = cam_df["zona_cam_raw"].ffill()
    cam_df["comuna_raw"] = cam_df["comuna_raw"].ffill()
    cam_df["empresa_cam"] = cam_df["empresa_cam_raw"].map(_clean_text)
    cam_df = cam_df[cam_df["empresa_cam"].notna()].copy()

    cam_df["cam_activo_id"] = pd.to_numeric(cam_df["cam_activo_raw"], errors="coerce")
    cam_df = cam_df[cam_df["cam_activo_id"].notna()].copy()
    cam_df["cam_activo_id"] = cam_df["cam_activo_id"].astype(int)

    cam_df["zona_cam"] = cam_df["zona_cam_raw"].map(_clean_text)
    cam_df = cam_df[cam_df["zona_cam"].notna()].copy()

    cam_df["empresa_cam_norm"] = cam_df["empresa_cam"].map(_normalize_institucion_name)
    cam_df = cam_df[cam_df["empresa_cam_norm"].notna()].copy()

    cam_detalle = (
        cam_df[["cam_activo_id", "zona_cam", "empresa_cam", "empresa_cam_norm"]]
        .drop_duplicates(subset=["cam_activo_id", "zona_cam", "empresa_cam_norm"])
        .sort_values(["cam_activo_id", "zona_cam", "empresa_cam_norm"])
        .reset_index(drop=True)
    )
    cam_detalle["fuente_archivo"] = REPORT_FILE.name
    cam_detalle["fuente_hoja"] = SHEET_CAM

    cam_resumen_zona = (
        cam_detalle.groupby(["cam_activo_id", "zona_cam"], as_index=False)
        .agg(empresas_unicas_zona=("empresa_cam_norm", "nunique"))
        .sort_values(["cam_activo_id", "zona_cam"])
        .reset_index(drop=True)
    )

    empresas_unicas_suma_por_zona = (
        cam_detalle.groupby("zona_cam", as_index=False)
        .agg(empresas_unicas_zona=("empresa_cam_norm", "nunique"))["empresas_unicas_zona"]
        .sum()
    )

    cam_control = pd.DataFrame(
        [
            {
                "cam_activos_total": int(cam_detalle["cam_activo_id"].nunique()),
                "zonas_cam_total": int(cam_detalle["zona_cam"].nunique()),
                "empresas_unicas_global": int(cam_detalle["empresa_cam_norm"].nunique()),
                "empresas_unicas_suma_por_zona": int(empresas_unicas_suma_por_zona),
            }
        ]
    )

    excel_zone_map = {}
    if col_idx_comuna is not None:
        for _, row in cam_df.iterrows():
            zone = _clean_text(row["zona_cam_raw"])
            comuna_val = row["comuna_raw"]
            if zone and pd.notna(comuna_val) and zone not in excel_zone_map:
                comunas_found = [int(c) for c in re.findall(r'\d+', str(comuna_val))]
                if comunas_found:
                    excel_zone_map[zone] = comunas_found

    return cam_detalle, cam_resumen_zona, cam_control, excel_zone_map


def _classify_comunidad(row: pd.Series) -> str | None:
    if row.get("seccion_tablero") != "Comunitaria":
        return None

    publico = _normalize_text(row.get("publico_comunidad") or "")
    actividad_com = _normalize_text(row.get("actividad_comunitaria") or "")
    procesos = _normalize_text(row.get("procesos") or "")

    if any(
        term in txt
        for txt in [publico, actividad_com, procesos]
        for term in ["hogar seguro", "plan familiar", "planes familiares", "hogar"]
    ):
        return "Hogares seguros y planes familiares"

    if (_has_value(row.get("semillero_grd")) or _has_value(row.get("actividad_semillero"))
            or "semillero" in publico):
        return "Semilleros"
    if _has_value(row.get("nombre_satc")):
        return "SAT-C"
    if any(term in publico for term in ["comite", "comision"]):
        return "Comisiones y comites"
    if publico or row.get("seccion_tablero") == "Comunitaria":
        return "Otros Procesos Organizativos"
    return None


def _classify_educacion(row: pd.Series) -> str | None:
    if row.get("seccion_tablero") != "Educativa":
        return None

    publico_pi = _normalize_text(row.get("publico_primera_infancia") or "")
    publico_edu = _normalize_text(row.get("publico_educacion") or "")
    nivel = _normalize_text(row.get("nivel_educativo") or "")
    institucion = _normalize_text(row.get("institucion_educativa_norm") or "")

    forced_primera_infancia_institutions = {
        "jardin infantil huellitas de angeles",
    }

    forced_media_institutions = {
        "ie ciudadela nuevo occidente",
        "instituto tecnico industrial pascual bravo",
    }

    superior_terms = [
        "superior",
        "univers",
        "institucion universitaria",
        "iu ",
        "tecnolog",
        "politec",
        "sena",
        "ies ",
        "pascual bravo",
    ]

    if _has_value(row.get("publico_primera_infancia")) or _has_value(row.get("actividad_primera_infancia")) or _has_value(row.get("comuna_bc")):
        return "Instituciones Primera Infancia"
    if institucion in forced_primera_infancia_institutions:
        return "Instituciones Primera Infancia"
    if institucion in forced_media_institutions:
        return "Basica Media"
    if any(term in publico_edu for term in superior_terms) or any(term in nivel for term in superior_terms) or any(term in institucion for term in superior_terms):
        return "Educacion Superior"
    if publico_pi or publico_edu or _has_value(row.get("actividad_educacion")) or row.get("seccion_tablero") == "Educativa":
        return "Basica Media"
    return None


def _classify_empresarial(row: pd.Series) -> str | None:
    if row.get("seccion_tablero") != "Empresarial":
        return None

    publico = _normalize_text(row.get("publico_empresarial") or "")
    actividad_emp = _normalize_text(row.get("actividad_empresarial") or "")

    if any(
        term in txt
        for txt in [publico, actividad_emp]
        for term in ["plan de ayuda mutua", "planes de ayuda mutua", "ayuda mutua", "acuerdo de voluntades"]
    ):
        return "Planes de ayuda mutua/Acuerdo de voluntades"

    if _has_value(row.get("nombre_cosegrd")) or "cosegrd" in publico or re.search(r"\bcam\b", publico):
        return "CAM"
    if any(term in txt for txt in [publico, actividad_emp] for term in ["propiedad horizontal", "horizontal", "ph", "bienes y servicios"]):
        return "Propiedades Horizontales"
    if publico or _has_value(row.get("actividad_empresarial")) or row.get("seccion_tablero") == "Empresarial":
        return "Empresas"
    return None


def _classify_institucional(row: pd.Series) -> str | None:
    if row.get("seccion_tablero") != "Institucional":
        return None

    if _has_value(row.get("mesa_institucional")):
        return "Mesas Interinstitucionalidad en el territorio"
    if _has_value(row.get("actividad_pdl_pp")) or _has_value(row.get("actividad_gestion_interna")):
        return "Acciones Conjuntas"
    if _has_value(row.get("actividad_institucional")) or row.get("seccion_tablero") == "Institucional":
        return "Articulacion Institucional"
    return None


def _classify_ambito_institucional(row: pd.Series) -> str | None:
    """Clasifica solo a Institucional Externa. Interna/PDL quedan como None (excluidas de Institucional)."""
    if row.get("seccion_tablero") != "Institucional":
        return None

    instancia = _normalize_text(row.get("instancia") or "")
    # ÚNICAMENTE si es Institucional Externa
    if "institucional" in instancia and "gestion interna" not in instancia and "pdl" not in instancia:
        return "Institucional Externa"
    
    # Todo lo demás (Interna DAGRD, PDL y PP) → None (excluido de Institucional)
    return None


def _classify_subbloque_institucional(row: pd.Series) -> str | None:
    """Solo clasifica subbloques para Institucional Externa. Otros ámbitos → None."""
    if row.get("seccion_tablero") != "Institucional":
        return None

    # Si no es Institucional Externa, no clasificar subbloque
    if row.get("ambito_institucional") != "Institucional Externa":
        return None

    bloque = row.get("bloque_institucional")
    if bloque == "Mesas Interinstitucionalidad en el territorio":
        return "Mesas Territoriales"

    if bloque == "Articulacion Institucional":
        if _has_value(row.get("actividad_institucional")):
            return "Articulacion con detalle"
        return "Articulacion sin detalle"

    return None


def _classify_grupo_ambito_comparacion(row: pd.Series) -> str | None:
    """Solo devuelve 'Externa' para Institucional Externa. El resto quedan como None."""
    if row.get("seccion_tablero") != "Institucional":
        return None

    if row.get("ambito_institucional") == "Institucional Externa":
        return "Externa"
    
    # Interna, PDL, etc. → None
    return None


def _map_simulacro_sector(sector: str | None) -> str:
    value = _normalize_text(sector or "")
    if "comunit" in value:
        return "Comunitaria"
    if "educ" in value:
        return "Educativa"
    if "empres" in value:
        return "Empresarial"
    if "instit" in value:
        return "Institucional"
    return "Otros"


def _aggregate_blocks(df: pd.DataFrame, block_col: str, block_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[block_name, "actividades", "participaciones", "impacto_indirecto", *DEMOGRAPHIC_MAP.keys()])

    work = df.copy()
    numeric_cols = [
        "participantes",
        "impacto_indirecto",
        "mujeres",
        "hombres",
        "ninos",
        "pri_infanc",
        "nino_adole",
        "juventud",
        "adulto",
        "adulto_may",
        "discapacid",
        "afrodescen",
        "campesino",
        "pob_victim",
        "pob_migran",
        "pob_lgtbi",
        "pob_indige",
        "pob_rom",
    ]
    for col in numeric_cols:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    agg_map = {col: (col, "sum") for col in numeric_cols}
    summary = (
        work.groupby(block_col, dropna=False, as_index=False)
        .agg(actividades=(block_col, "count"), **agg_map)
        .rename(columns={block_col: block_name})
        .sort_values(block_name)
        .reset_index(drop=True)
    )
    summary = summary[summary[block_name].notna()]
    return summary


def _build_demografia_unpivot(fact_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for record in fact_df.to_dict(orient="records"):
        for col, (dimension, categoria) in DEMOGRAPHIC_MAP.items():
            value = record.get(col)
            numeric = _to_int(value)
            if numeric is None or numeric == 0:
                continue
            rows.append(
                {
                    "id_actividad": record.get("id_actividad"),
                    "fecha": record.get("fecha"),
                    "anio": record.get("anio"),
                    "mes_num": record.get("mes_num"),
                    "mes_nombre": record.get("mes_nombre"),
                    "comuna_cod": record.get("comuna_cod"),
                    "instancia": record.get("instancia"),
                    "seccion_tablero": record.get("seccion_tablero"),
                    "bloque_comunidad": record.get("bloque_comunidad"),
                    "bloque_educacion": record.get("bloque_educacion"),
                    "bloque_empresarial": record.get("bloque_empresarial"),
                    "bloque_institucional": record.get("bloque_institucional"),
                    "ambito_institucional": record.get("ambito_institucional"),
                    "subbloque_institucional": record.get("subbloque_institucional"),
                    "grupo_ambito_comparacion": record.get("grupo_ambito_comparacion"),
                    "dimension": dimension,
                    "categoria": categoria,
                    "valor": numeric,
                }
            )
    return pd.DataFrame(rows)


def _normalize_gender_to_participantes(fact_df: pd.DataFrame) -> pd.DataFrame:
    # Enforce row-level consistency for dashboard comparability.
    # After this step, for rows with participantes > 0, mujeres + hombres == participantes.
    for col in ["participantes", "mujeres", "hombres"]:
        fact_df[col] = pd.to_numeric(fact_df[col], errors="coerce")

    participantes = fact_df["participantes"].fillna(0)
    mujeres = fact_df["mujeres"].fillna(0)
    hombres = fact_df["hombres"].fillna(0)
    genero_total = mujeres + hombres

    base_mask = (participantes > 0) & (genero_total > 0)
    base_total = genero_total[base_mask].sum()
    ratio_mujeres = float(mujeres[base_mask].sum() / base_total) if base_total > 0 else 0.5

    out_mujeres = mujeres.copy()
    out_hombres = hombres.copy()

    mask_pos = (participantes > 0) & (genero_total > 0)
    if mask_pos.any():
        scaled_mujeres = (mujeres[mask_pos] * participantes[mask_pos] / genero_total[mask_pos]).round()
        scaled_hombres = participantes[mask_pos] - scaled_mujeres
        out_mujeres.loc[mask_pos] = scaled_mujeres
        out_hombres.loc[mask_pos] = scaled_hombres

    mask_zero = (participantes > 0) & (genero_total == 0)
    if mask_zero.any():
        imputed_mujeres = (participantes[mask_zero] * ratio_mujeres).round()
        imputed_hombres = participantes[mask_zero] - imputed_mujeres
        out_mujeres.loc[mask_zero] = imputed_mujeres
        out_hombres.loc[mask_zero] = imputed_hombres

    fact_df["mujeres"] = out_mujeres.astype("Int64")
    fact_df["hombres"] = out_hombres.astype("Int64")
    return fact_df


def _read_sheet3_simulacros_openpyxl() -> List[Tuple[int, Dict[int, str]]]:
    """Fallback: Leer Simulacros con openpyxl cuando XML parsing falla."""
    try:
        df_raw = pd.read_excel(REPORT_FILE, sheet_name=SHEET_SIMULACROS, header=None, engine='openpyxl')
        df_clean = df_raw.dropna(how='all')

        if df_clean.empty:
            return []

        header_row = df_clean.iloc[0]
        df_data = df_clean.iloc[1:].reset_index(drop=True)

        sheet3_rows: List[Tuple[int, Dict[int, str]]] = []
        header_map = {i + 1: str(col).strip() for i, col in enumerate(header_row)}
        sheet3_rows.append((1, header_map))

        for idx, row in df_data.iterrows():
            row_num = idx + 2
            row_map: Dict[int, str] = {}
            for col_idx, value in enumerate(row, 1):
                if pd.notna(value):
                    str_val = str(value).strip()
                    if str_val and str_val.lower() != 'nan':
                        row_map[col_idx] = str_val
            if row_map:
                sheet3_rows.append((row_num, row_map))

        return sheet3_rows
    except Exception:
        return []

def _extract_fact_and_queries() -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DataFrame]:
    if not REPORT_FILE.exists():
        raise FileNotFoundError(f"No existe archivo: {REPORT_FILE}")

    with zipfile.ZipFile(REPORT_FILE, "r") as zf:
        shared = _read_shared_strings(zf)
        sheet1_rows = _read_sheet_rows(zf, _get_sheet_xml_target(zf, SHEET_DETALLE), shared)
        sheet2_rows = _read_sheet_rows(zf, _get_sheet_xml_target(zf, SHEET_PIVOT), shared)
        try:
            sheet3_rows = _read_sheet_rows(zf, _get_sheet_xml_target(zf, SHEET_SIMULACROS), shared)
        except Exception:
            sheet3_rows = []

    if not sheet3_rows:
        sheet3_rows = _read_sheet3_simulacros_openpyxl()

    if not sheet1_rows:
        raise RuntimeError("No se encontraron filas en Sheet1.")

    header_row_num, header_map = sheet1_rows[0]
    if header_row_num != 1:
        raise RuntimeError("La fila de encabezados de Sheet1 no esta en fila 1.")

    idx_nata = _find_col(header_map, ["nata"])
    idx_fecha = _find_col(header_map, ["fecha", "actividad"])
    idx_comuna = _find_col(header_map, ["comuna", "corregimiento"])
    idx_instancia = _find_col(header_map, ["instancia"])
    idx_publico_comunidad = _find_col(header_map, ["publico objeto", "comunidad"])
    idx_semillero = _find_col(header_map, ["semillero", "grd"])
    idx_actividad_semillero = _find_col(header_map, ["actividad realizada", "semillero"])
    # La fuente nueva expone el campo como "Nombre del SAT-C"; mantenemos
    # variantes antiguas para no romper libros previos.
    idx_nombre_satc = _find_col(header_map, ["nombre"], ["sat-c", "satc"])
    idx_actividad_comunitaria = _find_col(header_map, ["actividad asociada", "instancia comunitaria"])
    idx_publico_primera = _find_col(header_map, ["publico objeto", "primera infancia"])
    idx_comuna_bc = _find_col(header_map, ["comuna", "establecimiento de bc"])
    idx_actividad_primera = _find_col(header_map, ["actividad asociada", "instancia primera infancia"])
    idx_actividad_institucional = _find_col(header_map, ["actividad asociada", "instancia institucional"])
    idx_mesa_institucional = _find_col(header_map, ["mesa institucional"])
    idx_publico_empresarial = _find_col(header_map, ["publico objeto", "instancia empresarial"])
    idx_nombre_cosegrd = _find_col(header_map, ["nombre", "cosegrd"])
    idx_actividad_empresarial = _find_col(header_map, ["actividad asociada", "instancia empresarial"])
    idx_actividad_pdl = _find_col(header_map, ["actividad asociada", "pdl", "pp"])
    idx_actividad_gestion = _find_col(header_map, ["actividad asociada", "gestion interna"])
    idx_publico_educacion = _find_col(header_map, ["publico objeto", "educacion"])
    idx_comuna_educacion = _find_col(header_map, ["seleccionar la comuna", "establecimiento educativo"])
    educacion_establecimiento_cols = _find_educacion_establecimiento_cols(header_map)
    if not educacion_establecimiento_cols:
        raise RuntimeError("No se encontraron columnas 'Nombre del Establecimiento Educativo - comuna X'.")
    sedes_bc_cols = _find_sedes_bc_cols(header_map)
    if not sedes_bc_cols:
        raise RuntimeError("No se encontraron columnas 'Sedes de BC en comuna X'.")
    idx_actividad_educacion = _find_col(header_map, ["actividad asociada", "educacion"])
    idx_rel_meta = _find_col(header_map, ["relacion", "metas", "plan de desarrollo"])
    idx_entidades = _find_col(header_map, ["entidades asociadas"])
    idx_modalidad = _find_col(header_map, ["actividad se desarrollo"])
    idx_profesionales = _find_col(header_map, ["otros profesionales"])
    idx_participantes = _find_col(header_map, ["numero", "personas", "participantes"])
    idx_impacto = _find_col(header_map, ["impactadas", "indirectamente"])
    idx_mujeres = _find_col(header_map, ["mujeres"])
    idx_hombres = _find_col(header_map, ["hombres"])
    idx_ninos = _find_col(header_map, ["ninos"])
    idx_pri_inf = _find_col(header_map, ["primera infancia"], ["0-5"])
    idx_nino_adole = _find_col(header_map, ["ninez", "adolescencia"], ["6-17"])
    idx_juventud = _find_col(header_map, ["juventud"], ["18-28"])
    idx_adulto = _find_col(header_map, ["adulto"], ["29-54"])
    idx_adulto_may = _find_col(header_map, ["adulto mayor"], ["55"])
    idx_discap = _find_col(header_map, ["discapacidad"])
    idx_afro = _find_col(header_map, ["afrodescendiente"])
    idx_camp = _find_col(header_map, ["campesinos"])
    idx_vict = _find_col(header_map, ["poblacion", "victima"])
    idx_migr = _find_col(header_map, ["poblacion", "migrante"])
    idx_lgtbi = _find_col(header_map, ["poblacion", "lgtbi"])
    idx_indig = _find_col(header_map, ["poblacion", "indigena"])
    idx_rom = _find_col(header_map, ["poblacion", "rom"])
    idx_procesos = _find_col_optional(header_map, ["procesos"])  # Optional column
    idx_nivel_educativo = _find_col_optional(header_map, ["nivel educativo"])  # Optional column

    fact_rows: List[Dict[str, object]] = []
    for row_num, row in sheet1_rows[1:]:
        id_actividad = _to_int(row.get(idx_nata, ""))
        fecha = _parse_excel_date(row.get(idx_fecha, ""))
        participantes = _to_int(row.get(idx_participantes, ""))
        instancia = _clean_text(row.get(idx_instancia, ""))
        comuna_cod = _to_int(row.get(idx_comuna, ""))
        comuna_educacion_text = _clean_text(row.get(idx_comuna_educacion, ""))
        comuna_educacion_cod = _parse_comuna_text_to_code(comuna_educacion_text)
        comuna_bc_text = _clean_text(row.get(idx_comuna_bc, ""))
        comuna_bc_cod = _parse_comuna_text_to_code(comuna_bc_text)
        establecimiento_educativo = _extract_establecimiento_educativo(
            row=row,
            comuna_educacion_text=comuna_educacion_text,
            establecimiento_cols=educacion_establecimiento_cols,
        )
        sede_bc = _extract_establecimiento_educativo(
            row=row,
            comuna_educacion_text=comuna_bc_text,
            establecimiento_cols=sedes_bc_cols,
        )
        institucion_educativa = sede_bc or establecimiento_educativo
        institucion_educativa_es_agregada = _is_aggregated_ies(institucion_educativa)
        comuna_institucion_educativa_cod = comuna_bc_cod if sede_bc else comuna_educacion_cod

        if id_actividad is None and participantes is None and not instancia:
            continue

        fact_rows.append(
            {
                "id_actividad": id_actividad,
                "fila_origen": row_num,
                "fecha": fecha,
                "anio": int(fecha.year) if pd.notna(fecha) else None,
                "mes_num": int(fecha.month) if pd.notna(fecha) else None,
                "mes_nombre": MONTHS_ES.get(int(fecha.month), None) if pd.notna(fecha) else None,
                "comuna_cod": comuna_cod,
                "instancia": instancia,
                "seccion_tablero": _map_seccion(instancia),
                "publico_comunidad": _clean_text(row.get(idx_publico_comunidad, "")),
                "semillero_grd": _clean_text(row.get(idx_semillero, "")),
                "actividad_semillero": _clean_text(row.get(idx_actividad_semillero, "")),
                "nombre_satc": _clean_text(row.get(idx_nombre_satc, "")),
                "actividad_comunitaria": _clean_text(row.get(idx_actividad_comunitaria, "")),
                "publico_primera_infancia": _clean_text(row.get(idx_publico_primera, "")),
                "comuna_bc": comuna_bc_text,
                "comuna_bc_cod": comuna_bc_cod,
                "sede_bc": sede_bc,
                "sede_bc_norm": _normalize_institucion_name(sede_bc),
                "actividad_primera_infancia": _clean_text(row.get(idx_actividad_primera, "")),
                "actividad_institucional": _clean_text(row.get(idx_actividad_institucional, "")),
                "mesa_institucional": _clean_text(row.get(idx_mesa_institucional, "")),
                "publico_empresarial": _clean_text(row.get(idx_publico_empresarial, "")),
                "nombre_cosegrd": _clean_text(row.get(idx_nombre_cosegrd, "")),
                "actividad_empresarial": _clean_text(row.get(idx_actividad_empresarial, "")),
                "actividad_pdl_pp": _clean_text(row.get(idx_actividad_pdl, "")),
                "actividad_gestion_interna": _clean_text(row.get(idx_actividad_gestion, "")),
                "publico_educacion": _clean_text(row.get(idx_publico_educacion, "")),
                "comuna_educacion": comuna_educacion_text,
                "comuna_educacion_cod": comuna_educacion_cod,
                "establecimiento_educativo": establecimiento_educativo,
                "establecimiento_educativo_norm": _normalize_institucion_name(establecimiento_educativo),
                "institucion_educativa": institucion_educativa,
                "institucion_educativa_norm": None if institucion_educativa_es_agregada else _normalize_institucion_name(institucion_educativa),
                "institucion_educativa_es_agregada": institucion_educativa_es_agregada,
                "comuna_institucion_educativa_cod": comuna_institucion_educativa_cod,
                "actividad_educacion": _clean_text(row.get(idx_actividad_educacion, "")),
                "rel_meta_pdd": _clean_text(row.get(idx_rel_meta, "")),
                "entidades_asociadas": _clean_text(row.get(idx_entidades, "")),
                "modalidad": _clean_text(row.get(idx_modalidad, "")),
                "otros_profesionales": _clean_text(row.get(idx_profesionales, "")),
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
                "procesos": _clean_text(row.get(idx_procesos, "")) if idx_procesos is not None else "",
                "nivel_educativo": _clean_text(row.get(idx_nivel_educativo, "")) if idx_nivel_educativo is not None else "",
                "fuente_archivo": REPORT_FILE.name,
                "fuente_hoja": SHEET_DETALLE,
            }
        )

    fact_df = pd.DataFrame(fact_rows)
    if fact_df.empty:
        raise RuntimeError("La tabla principal quedo vacia. Revisar archivo fuente.")

    fact_df = _normalize_gender_to_participantes(fact_df)

    fact_df["bloque_comunidad"] = fact_df.apply(_classify_comunidad, axis=1)
    fact_df["bloque_educacion"] = fact_df.apply(_classify_educacion, axis=1)
    fact_df["bloque_empresarial"] = fact_df.apply(_classify_empresarial, axis=1)
    fact_df["bloque_institucional"] = fact_df.apply(_classify_institucional, axis=1)
    fact_df["ambito_institucional"] = fact_df.apply(_classify_ambito_institucional, axis=1)
    fact_df["subbloque_institucional"] = fact_df.apply(_classify_subbloque_institucional, axis=1)
    fact_df["grupo_ambito_comparacion"] = fact_df.apply(_classify_grupo_ambito_comparacion, axis=1)

    # POST-PROCESAMIENTO: Limpiar seccion_tablero para filas donde ambito_institucional=NaN
    # (Ej: Gestión Interna y PDL fueron clasificadas como "Institucional" por _map_seccion,
    # pero ambito_institucional=None significa que NO deben estar en Institucional)
    mask_inst_no_valida = (fact_df["seccion_tablero"] == "Institucional") & (fact_df["ambito_institucional"].isna())
    fact_df.loc[mask_inst_no_valida, "seccion_tablero"] = None

    general_por_seccion = _aggregate_blocks(fact_df, "seccion_tablero", "seccion_tablero")
    general_por_comuna = (
        fact_df.groupby("comuna_cod", dropna=False, as_index=False)
        .agg(actividades=("comuna_cod", "count"), participaciones=("participantes", "sum"))
        .sort_values("comuna_cod")
        .reset_index(drop=True)
    )
    general_por_fecha = (
        fact_df.groupby("fecha", dropna=False, as_index=False)
        .agg(actividades=("fecha", "count"), participaciones=("participantes", "sum"))
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    comunidad_resumen = _aggregate_blocks(
        fact_df[fact_df["bloque_comunidad"].notna()],
        "bloque_comunidad",
        "bloque_comunidad",
    )
    educacion_resumen = _aggregate_blocks(
        fact_df[fact_df["bloque_educacion"].notna()],
        "bloque_educacion",
        "bloque_educacion",
    )
    empresarial_resumen = _aggregate_blocks(
        fact_df[fact_df["bloque_empresarial"].notna()],
        "bloque_empresarial",
        "bloque_empresarial",
    )
    institucional_resumen = _aggregate_blocks(
        fact_df[fact_df["bloque_institucional"].notna()],
        "bloque_institucional",
        "bloque_institucional",
    )
    institucional_ambito_resumen = _aggregate_blocks(
        fact_df[fact_df["ambito_institucional"].notna()],
        "ambito_institucional",
        "ambito_institucional",
    )
    institucional_subbloque_resumen = _aggregate_blocks(
        fact_df[fact_df["subbloque_institucional"].notna()],
        "subbloque_institucional",
        "subbloque_institucional",
    )
    institucional_grupo_ambito_resumen = _aggregate_blocks(
        fact_df[fact_df["grupo_ambito_comparacion"].notna()],
        "grupo_ambito_comparacion",
        "grupo_ambito_comparacion",
    )
    interna_dagrd_resumen = _aggregate_blocks(
        fact_df[(fact_df["ambito_institucional"] == "Interna DAGRD") & (fact_df["bloque_institucional"].notna())],
        "bloque_institucional",
        "bloque_institucional",
    )
    pdlpp_resumen = _aggregate_blocks(
        fact_df[(fact_df["ambito_institucional"] == "PDL y PP") & (fact_df["bloque_institucional"].notna())],
        "bloque_institucional",
        "bloque_institucional",
    )
    institucional_externa_resumen = _aggregate_blocks(
        fact_df[(fact_df["ambito_institucional"] == "Institucional Externa") & (fact_df["bloque_institucional"].notna())],
        "bloque_institucional",
        "bloque_institucional",
    )

    demografia_df = _build_demografia_unpivot(fact_df)

    # Simulacros
    simulacros_df = pd.DataFrame()
    if sheet3_rows:
        sim_header_num, sim_header_map = sheet3_rows[0]
        idx_sim_fecha = _find_col(sim_header_map, ["marca temporal"])
        idx_sim_nombre = _find_col(sim_header_map, ["nombre completo"])
        idx_sim_comuna = _find_col(sim_header_map, ["comuna", "pertenece"])
        idx_sim_sector = _find_col(sim_header_map, ["sector pertenece"])
        idx_sim_personas = _find_col(sim_header_map, ["personas", "participaron"])

        sim_rows: List[Dict[str, object]] = []
        for row_num, row in sheet3_rows[1:]:
            fecha = _parse_excel_date(row.get(idx_sim_fecha, ""))
            sector_origen = _clean_text(row.get(idx_sim_sector, ""))
            sim_rows.append(
                {
                    "fila_origen": row_num,
                    "fecha": fecha,
                    "anio": int(fecha.year) if pd.notna(fecha) else None,
                    "mes_num": int(fecha.month) if pd.notna(fecha) else None,
                    "mes_nombre": MONTHS_ES.get(int(fecha.month), None) if pd.notna(fecha) else None,
                    "nombre_entidad": _clean_text(row.get(idx_sim_nombre, "")),
                    "comuna_texto": _clean_text(row.get(idx_sim_comuna, "")),
                    "comuna_cod": _parse_comuna_text_to_code(row.get(idx_sim_comuna, "")),
                    "sector_origen": sector_origen,
                    "sector_tablero": _map_simulacro_sector(sector_origen),
                    "personas_participantes": _to_int(row.get(idx_sim_personas, "")),
                    "fuente_archivo": REPORT_FILE.name,
                    "fuente_hoja": SHEET_SIMULACROS,
                }
            )
        simulacros_df = pd.DataFrame(sim_rows)

    if simulacros_df.empty:
        simulacros_por_sector = pd.DataFrame(columns=["sector_tablero", "registros", "personas_participantes"])
    else:
        simulacros_por_sector = (
            simulacros_df.groupby("sector_tablero", dropna=False, as_index=False)
            .agg(registros=("nombre_entidad", "count"), personas_participantes=("personas_participantes", "sum"))
            .sort_values("sector_tablero")
            .reset_index(drop=True)
        )

    pivot_acts, pivot_parts = _extract_pivot_totals(sheet2_rows)
    control_df = pd.DataFrame(
        [
            {
                "archivo_origen": REPORT_FILE.name,
                "filas_hecho_general": int(fact_df.shape[0]),
                "total_actividades_hecho_general": int(fact_df.shape[0]),
                "total_participaciones_hecho_general": int(fact_df["participantes"].fillna(0).sum()),
                "total_actividades_pivot": pivot_acts,
                "total_participaciones_pivot": pivot_parts,
                "coinciden_actividades": "SI" if pivot_acts == int(fact_df.shape[0]) else "NO",
                "coinciden_participantes": "SI" if pivot_parts == int(fact_df["participantes"].fillna(0).sum()) else "NO",
                "inst_externa_actividades": int((fact_df["ambito_institucional"] == "Institucional Externa").sum()),
                "inst_externa_participaciones": int(
                    fact_df.loc[fact_df["ambito_institucional"] == "Institucional Externa", "participantes"].fillna(0).sum()
                ),
                "inst_interna_dagrd_actividades": int((fact_df["ambito_institucional"] == "Interna DAGRD").sum()),
                "inst_interna_dagrd_participaciones": int(
                    fact_df.loc[fact_df["ambito_institucional"] == "Interna DAGRD", "participantes"].fillna(0).sum()
                ),
                "inst_pdlpp_actividades": int((fact_df["ambito_institucional"] == "PDL y PP").sum()),
                "inst_pdlpp_participaciones": int(
                    fact_df.loc[fact_df["ambito_institucional"] == "PDL y PP", "participantes"].fillna(0).sum()
                ),
                "filas_simulacros": int(simulacros_df.shape[0]),
                "personas_simulacros": int(simulacros_df["personas_participantes"].fillna(0).sum()) if not simulacros_df.empty else 0,
            }
        ]
    )

    cam_detalle, cam_resumen_zona, cam_control, excel_zone_map = _extract_cam_tables()

    # Generar tabla de dimensiones de zonas CAM a partir del mapeo en config y Excel
    zone_map = config.get("cam_zone_comuna_map", {})
    if excel_zone_map:
        # Priorizar mapeo de Excel sobre el de la configuración
        zone_map = {**zone_map, **excel_zone_map}

    zone_rows = []
    for zone, comunas in zone_map.items():
        for comuna in comunas:
            zone_rows.append({"zona_cam": zone, "comuna_cod": int(comuna)})
    dim_zonas_cam = pd.DataFrame(zone_rows)
    if dim_zonas_cam.empty:
        dim_zonas_cam = pd.DataFrame(columns=["zona_cam", "comuna_cod"])

    outputs: Dict[str, pd.DataFrame] = {
        "Hecho_Participacion_General": fact_df,
        "General_Por_Seccion": general_por_seccion,
        "General_Por_Comuna": general_por_comuna,
        "General_Por_Fecha": general_por_fecha,
        "Comunidad_Resumen": comunidad_resumen,
        "Educacion_Resumen": educacion_resumen,
        "Empresarial_Resumen": empresarial_resumen,
        "Institucional_Resumen": institucional_resumen,
        "Institucional_Ambito_Resumen": institucional_ambito_resumen,
        "Institucional_Subbloque_Resumen": institucional_subbloque_resumen,
        "Inst_GrupoAmbito_Resumen": institucional_grupo_ambito_resumen,
        "Interna_DAGRD_Resumen": interna_dagrd_resumen,
        "PDLPP_Resumen": pdlpp_resumen,
        "Institucional_Externa_Resumen": institucional_externa_resumen,
        "Hecho_Demografia": demografia_df,
        "Hecho_Simulacros": simulacros_df,
        "Simulacros_Por_Sector": simulacros_por_sector,
        "CAM_Detalle": cam_detalle,
        "CAM_Resumen_Zona": cam_resumen_zona,
        "CAM_Control": cam_control,
        "Dim_Zonas_CAM": dim_zonas_cam,
        "Control_Extraccion": control_df,
    }
    return fact_df, outputs, control_df


def main() -> None:
    _, outputs, _ = _extract_fact_and_queries()

    temp_output = OUTPUT_FILE.with_name(f"{OUTPUT_FILE.stem}.tmp.xlsx")
    if OUTPUT_FILE.exists():
        shutil.copy2(OUTPUT_FILE, temp_output)
        writer_mode = "a"
        writer_kwargs = {"if_sheet_exists": "replace"}
    else:
        writer_mode = "w"
        writer_kwargs = {}

    with pd.ExcelWriter(temp_output, engine="openpyxl", mode=writer_mode, **writer_kwargs) as writer:
        for sheet_name, df in outputs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    temp_output.replace(OUTPUT_FILE)

    repair_script = BASE_DIR / "scripts" / "etl" / "reparar_hojas_modelo_para_powerbi.py"
    if repair_script.exists() and os.getenv("RUN_MODEL_REPAIR", "0") == "1":
        runpy.run_path(str(repair_script), run_name="__main__")

    print(f"OK: archivo generado en {OUTPUT_FILE}")
    for name, df in outputs.items():
        print(f"- {name}: {df.shape[0]} filas x {df.shape[1]} columnas")


if __name__ == "__main__":
    main()
