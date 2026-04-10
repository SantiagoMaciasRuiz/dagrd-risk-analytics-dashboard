#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
MED_FILE = BASE / "powerbi" / "tmdl_live" / "tables" / "_Medidas.tmdl"
LAYOUT_FILE = BASE / "_pbix_temp" / "Report" / "Layout"
OUT_MEASURES = BASE / "data" / "reference" / "powerbi_medidas_mapeo_2026.csv"
OUT_MEASURES_USED = BASE / "data" / "reference" / "powerbi_medidas_usadas_en_visuales_2026.csv"
OUT_VISUALS = BASE / "data" / "reference" / "powerbi_consultas_visuales_2026.csv"
OUT_VISUAL_VALIDATION = BASE / "data" / "reference" / "powerbi_consultas_validacion_excel_2026.csv"
OUT_MD = BASE / "docs" / "core" / "VALIDACION_POWERBI_EXCEL_2026.md"


def parse_measures() -> list[dict[str, str]]:
    text = MED_FILE.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r"(?ms)^\s*measure\s+([A-Za-z0-9_]+)\s*=\s*(.+?)(?=^\s*measure\s+|^\s*partition\s+|\Z)"
    )

    rows: list[dict[str, str]] = []
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        expr = " ".join(m.group(2).strip().split())

        cols = sorted(set(re.findall(r"([A-Za-z0-9_]+\[[^\]]+\])", expr)))
        filters = sorted(set(re.findall(r"([A-Za-z0-9_]+\[[^\]]+\]\s*=\s*\"[^\"]+\")", expr)))

        rows.append(
            {
                "medida": name,
                "columnas_modelo": " | ".join(cols),
                "filtros_dax": " | ".join(filters),
                "expresion": expr,
            }
        )

    return rows


def parse_layout() -> list[dict[str, str]]:
    raw_bytes = LAYOUT_FILE.read_bytes()
    if b"\x00" in raw_bytes[:256]:
        raw = raw_bytes.decode("utf-16-le", errors="ignore")
    else:
        raw = raw_bytes.decode("utf-8", errors="ignore")

    layout: dict = {}
    try:
        layout = json.loads(raw)
    except json.JSONDecodeError:
        first_obj = raw.find("{")
        first_arr = raw.find("[")
        starts = [i for i in [first_obj, first_arr] if i != -1]
        start = min(starts) if starts else 0
        try:
            layout = json.loads(raw[start:])
        except json.JSONDecodeError:
            layout = {}

    sections = layout.get("sections", []) if isinstance(layout, dict) else []
    rows: list[dict[str, str]] = []

    # Fallback: algunos archivos Layout vienen en formato no-JSON estricto.
    # En ese caso extraemos visuales por bloques de cadenas serializadas.
    if not sections:
        return _parse_layout_fallback(raw)

    for section in sections:
        page_name = section.get("displayName") or section.get("name") or "(sin nombre)"
        for vc in section.get("visualContainers", []):
            conf = vc.get("config", "")
            filt = vc.get("filters", "")

            visual_name = ""
            visual_type = ""
            query_refs: set[str] = set()
            filter_json: list[str] = []

            if conf:
                try:
                    conf_obj = json.loads(conf)
                    sv = conf_obj.get("singleVisual", {})
                    visual_name = conf_obj.get("name", "")
                    visual_type = sv.get("visualType", "")

                    for vals in (sv.get("projections", {}) or {}).values():
                        if isinstance(vals, list):
                            for item in vals:
                                if isinstance(item, dict):
                                    qr = item.get("queryRef")
                                    if qr:
                                        query_refs.add(qr)

                    proto = sv.get("prototypeQuery", {})
                    for sel in proto.get("Select", []) if isinstance(proto, dict) else []:
                        if isinstance(sel, dict) and sel.get("Name"):
                            query_refs.add(sel["Name"])
                except Exception:
                    pass

            if filt:
                try:
                    flist = json.loads(filt)
                    for f in flist if isinstance(flist, list) else []:
                        fil = f.get("filter", {}) if isinstance(f, dict) else {}
                        where = fil.get("Where", []) if isinstance(fil, dict) else []
                        if where:
                            filter_json.append(json.dumps(where, ensure_ascii=False))
                except Exception:
                    pass

            rows.append(
                {
                    "pagina": page_name,
                    "visual_name": visual_name,
                    "visual_tipo": visual_type,
                    "query_refs": " | ".join(sorted(query_refs)),
                    "filtros_visual": " | ".join(filter_json),
                    "posicion": f"x={vc.get('x')},y={vc.get('y')},z={vc.get('z')}",
                }
            )

    return rows


def _decode_json_string(value: str) -> str:
    value = value.replace("\\r", "").replace("\\n", "")
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value


def _parse_layout_fallback(raw: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    page_pattern = re.compile(r'"displayName":"([^\"]+)"')
    pages = [(m.start(), m.group(1)) for m in page_pattern.finditer(raw)]

    visual_pattern = re.compile(
        r'"x":(?P<x>[-0-9\.]+),"y":(?P<y>[-0-9\.]+),"z":(?P<z>[-0-9\.]+).*?'
        r'"config":"(?P<config>.*?)"(?:,\s*"filters":"(?P<filters>.*?)")?',
        re.DOTALL,
    )

    for vm in visual_pattern.finditer(raw):
        start = vm.start()
        page = "(sin nombre)"
        for pos, name in pages:
            if pos <= start:
                page = name
            else:
                break

        conf_raw = vm.group("config") or ""
        filt_raw = vm.group("filters") or ""
        conf_text = _decode_json_string(conf_raw)
        filt_text = _decode_json_string(filt_raw)

        visual_name = ""
        visual_type = ""
        query_refs: set[str] = set()
        filter_json: list[str] = []

        try:
            conf_obj = json.loads(conf_text)
            sv = conf_obj.get("singleVisual", {})
            visual_name = conf_obj.get("name", "")
            visual_type = sv.get("visualType", "")

            for vals in (sv.get("projections", {}) or {}).values():
                if isinstance(vals, list):
                    for item in vals:
                        if isinstance(item, dict):
                            qr = item.get("queryRef")
                            if qr:
                                query_refs.add(qr)

            proto = sv.get("prototypeQuery", {})
            for sel in proto.get("Select", []) if isinstance(proto, dict) else []:
                if isinstance(sel, dict) and sel.get("Name"):
                    query_refs.add(sel["Name"])
        except Exception:
            # Fallback minimo por regex dentro del config serializado.
            for qr in re.findall(r'"queryRef":"([^\"]+)"', conf_text):
                query_refs.add(qr)
            vtype = re.search(r'"visualType":"([^\"]+)"', conf_text)
            if vtype:
                visual_type = vtype.group(1)

        if filt_text:
            try:
                flist = json.loads(filt_text)
                for f in flist if isinstance(flist, list) else []:
                    fil = f.get("filter", {}) if isinstance(f, dict) else {}
                    where = fil.get("Where", []) if isinstance(fil, dict) else []
                    if where:
                        filter_json.append(json.dumps(where, ensure_ascii=False))
            except Exception:
                filter_json.append(filt_text)

        rows.append(
            {
                "pagina": page,
                "visual_name": visual_name,
                "visual_tipo": visual_type,
                "query_refs": " | ".join(sorted(query_refs)),
                "filtros_visual": " | ".join(filter_json),
                "posicion": f"x={vm.group('x')},y={vm.group('y')},z={vm.group('z')}",
            }
        )

    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(measure_rows: list[dict[str, str]], visual_rows: list[dict[str, str]]) -> None:
    model_to_excel = {
        "participantes": "Sheet1 -> Indique el numero de personas participantes",
        "impacto_indirecto": "Sheet1 -> Cantidad de personas impactadas indirectamente",
        "seccion_tablero": "Sheet1 -> Instancia (clasificacion)",
        "bloque_comunidad": "Sheet1 -> Publico objeto en comunidad + campos comunidad (clasificacion)",
        "bloque_educacion": "Sheet1 -> Publico objeto en educacion + nivel educativo (clasificacion)",
        "bloque_empresarial": "Sheet1 -> Publico objeto en empresarial + COSEGRD (clasificacion)",
        "bloque_institucional": "Sheet1 -> Instancia/actividad institucional (clasificacion)",
        "comuna_cod": "Sheet1 -> Comuna/Corregimiento donde se desarrollo la actividad",
        "fecha": "Sheet1 -> Fecha actividad",
        "personas_participantes": "Simulacros -> columna de participantes",
        "sector_tablero": "Simulacros -> Sector pertenece",
    }

    lines = [
        "# Validacion Power BI vs Excel 2026",
        "",
        "Fuente principal: data/source/Reporte de actividades equipo social 2026 (1).xlsx",
        "",
        "## Archivos generados",
        "- data/reference/powerbi_medidas_mapeo_2026.csv",
        "- data/reference/powerbi_consultas_visuales_2026.csv",
        "",
        f"Total medidas encontradas: {len(measure_rows)}",
        f"Total visuales encontradas en layout: {len(visual_rows)}",
        "",
        "## Mapeo rapido modelo -> columna Excel",
    ]

    for k, v in model_to_excel.items():
        lines.append(f"- {k} -> {v}")

    lines.extend(
        [
            "",
            "## Como validar una medida en Excel",
            "1. Buscar medida en powerbi_medidas_mapeo_2026.csv.",
            "2. Tomar columnas_modelo y filtros_dax.",
            "3. Traducir columnas modelo al Excel usando el mapeo rapido.",
            "4. Aplicar filtros exactos y calcular:",
            "   - COUNTROWS: recuento de filas",
            "   - SUM(columna): suma de columna numerica",
            "   - DISTINCTCOUNT(columna): recuento unico",
            "",
            "## Nota",
            "- El layout tiene visuales con agregaciones directas sobre columnas (sin medida DAX).",
            "- Los filtros de cada visual estan serializados en powerbi_consultas_visuales_2026.csv (filtros_visual).",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def generate_used_measures(measure_rows: list[dict[str, str]], visual_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    used_names: set[str] = set()
    for vr in visual_rows:
        query_refs = vr.get("query_refs", "")
        for token in [t.strip() for t in query_refs.split("|") if t.strip()]:
            # QueryRef puede venir como [Medida] o Tabla[Columna]
            if token.startswith("[") and token.endswith("]"):
                used_names.add(token[1:-1])
            else:
                m = re.match(r"^([A-Za-z0-9_]+)$", token)
                if m:
                    used_names.add(m.group(1))

    rows: list[dict[str, str]] = []
    for mr in measure_rows:
        if mr["medida"] in used_names:
            rows.append(mr)
    return rows


def build_visual_validation_rows(visual_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    for vr in visual_rows:
        query_refs = [t.strip() for t in vr.get("query_refs", "").split("|") if t.strip()]
        filter_raw = vr.get("filtros_visual", "")

        filter_cols = re.findall(r'"Property":\s*"([^\"]+)"', filter_raw)
        filter_vals = re.findall(r'"Value":\s*"\'([^\"]*)\'"', filter_raw)

        for qr in query_refs if query_refs else [""]:
            agg = ""
            excel_col = ""

            m = re.match(r"^(Sum|Min|Max|Count|DistinctCount)\((.+)\)$", qr, flags=re.IGNORECASE)
            if m:
                agg = m.group(1).upper()
                excel_col = m.group(2)
            elif qr:
                excel_col = qr

            out.append(
                {
                    "pagina": vr.get("pagina", ""),
                    "visual_name": vr.get("visual_name", ""),
                    "visual_tipo": vr.get("visual_tipo", ""),
                    "query_ref": qr,
                    "agregacion": agg,
                    "columna_excel_o_modelo": excel_col,
                    "filtro_columnas": " | ".join(sorted(set(filter_cols))),
                    "filtro_valores": " | ".join(sorted(set(filter_vals))),
                }
            )

    return out


def main() -> None:
    measures = parse_measures()
    visuals = parse_layout()
    used_measures = generate_used_measures(measures, visuals)
    visual_validation = build_visual_validation_rows(visuals)

    write_csv(
        OUT_MEASURES,
        ["medida", "columnas_modelo", "filtros_dax", "expresion"],
        measures,
    )
    write_csv(
        OUT_MEASURES_USED,
        ["medida", "columnas_modelo", "filtros_dax", "expresion"],
        used_measures,
    )
    write_csv(
        OUT_VISUALS,
        ["pagina", "visual_name", "visual_tipo", "query_refs", "filtros_visual", "posicion"],
        visuals,
    )
    write_csv(
        OUT_VISUAL_VALIDATION,
        [
            "pagina",
            "visual_name",
            "visual_tipo",
            "query_ref",
            "agregacion",
            "columna_excel_o_modelo",
            "filtro_columnas",
            "filtro_valores",
        ],
        visual_validation,
    )
    write_summary(measures, visuals)

    print(f"Medidas: {len(measures)}")
    print(f"Medidas usadas en visuales: {len(used_measures)}")
    print(f"Visuales: {len(visuals)}")
    print(f"OK: {OUT_MEASURES}")
    print(f"OK: {OUT_MEASURES_USED}")
    print(f"OK: {OUT_VISUALS}")
    print(f"OK: {OUT_VISUAL_VALIDATION}")
    print(f"OK: {OUT_MD}")


if __name__ == "__main__":
    main()
