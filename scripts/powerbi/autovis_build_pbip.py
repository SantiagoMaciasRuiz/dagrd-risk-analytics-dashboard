#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_id() -> str:
    return uuid.uuid4().hex[:20]


def _clean_path_value(raw_value: str) -> str:
    return str(raw_value or "").strip().strip('"').strip("'")


def _resolve_report_definition(pbip_path: Path) -> Path:
    if pbip_path.is_dir():
        if pbip_path.name.endswith(".Report"):
            definition = pbip_path / "definition"
            if definition.exists():
                return definition
        if pbip_path.name == "definition" and (pbip_path / "pages").exists():
            return pbip_path

    if pbip_path.suffix.lower() == ".pbip":
        stem = pbip_path.stem
        report_dir = pbip_path.parent / f"{stem}.Report"
        definition = report_dir / "definition"
        if definition.exists():
            return definition
        
        # Fallback: buscar en hermanos el .Report más cercano
        for sibling in pbip_path.parent.iterdir():
            if sibling.is_dir() and sibling.name.endswith(".Report"):
                fallback_def = sibling / "definition"
                if fallback_def.exists():
                    return fallback_def

    raise RuntimeError(f"No se pudo resolver carpeta definition de reporte PBIP desde: {pbip_path}. Verifica que el PBIP esté bien formado.")


def _resolve_semantic_tables_dir(pbip_path: Path) -> Path | None:
    if pbip_path.suffix.lower() != ".pbip":
        return None
    stem = pbip_path.stem
    tables_dir = pbip_path.parent / f"{stem}.SemanticModel" / "definition" / "tables"
    return tables_dir if tables_dir.exists() else None


def _sync_pages_metadata(report_def: Path, pages_meta: dict) -> dict:
    pages_meta.setdefault(
        "$schema",
        "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    )
    pages_dir = report_def / "pages"
    ordered = list(pages_meta.get("pageOrder") or [])
    valid_order: list[str] = []
    for page_id in ordered:
        page_json_path = pages_dir / page_id / "page.json"
        if not page_json_path.exists():
            continue
        valid_order.append(page_id)
    pages_meta["pageOrder"] = valid_order
    active = str(pages_meta.get("activePageName") or "")
    if active not in valid_order:
        pages_meta["activePageName"] = valid_order[0] if valid_order else ""
    # El schema pagesMetadata/1.0.0 no permite la propiedad "pages".
    pages_meta.pop("pages", None)
    return pages_meta


def _parse_measures_from_blueprint(blueprint_path: Path) -> list[tuple[str, str]]:
    if not blueprint_path.exists():
        return []

    # Formato esperado: "- Tabla.Campo -> Medida, tipo: ..."
    pattern = re.compile(r"^-\s+([^\.\s]+)\.[^\s]+\s+->\s+([^,\s]+)")
    out: list[tuple[str, str]] = []
    for line in blueprint_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        table = m.group(1).strip()
        measure = m.group(2).strip()
        if table and measure:
            out.append((table, measure))
    return out


def _parse_measures_from_tmdl_tables(tables_dir: Path | None) -> list[tuple[str, str]]:
    if not tables_dir or not tables_dir.exists():
        return []

    table_re = re.compile(r"^\s*table\s+'?([^']+)'?\s*$", re.IGNORECASE)
    measure_re = re.compile(r"^\s*measure\s+'?([^'=]+?)'?\s*=", re.IGNORECASE)

    refs: list[tuple[str, str]] = []
    for tmdl in sorted(tables_dir.glob("*.tmdl")):
        text = tmdl.read_text(encoding="utf-8", errors="ignore")
        table_name = tmdl.stem
        for ln in text.splitlines():
            tm = table_re.match(ln)
            if tm:
                table_name = tm.group(1).strip()
                break

        for ln in text.splitlines():
            mm = measure_re.match(ln)
            if not mm:
                continue
            measure_name = mm.group(1).strip()
            if measure_name:
                refs.append((table_name, measure_name))

    # Priorizamos AB_* si existen, para alinear con autobuild/autofull
    ab_refs = [x for x in refs if x[1].upper().startswith("AB_")]
    return ab_refs or refs


def _pick_visual_metrics(blueprint_refs: list[tuple[str, str]], model_refs: list[tuple[str, str]]) -> list[tuple[str, str] | None]:
    source = blueprint_refs or model_refs
    if not source:
        return [None, None, None, None, None, None]

    unique: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in source:
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)

    selected = unique[:6]
    while len(selected) < 6:
        selected.append(unique[len(selected) % len(unique)])
    return selected


def _remove_existing_autovis_page(report_def: Path, pages_meta: dict, display_name: str) -> tuple[dict, int]:
    pages_dir = report_def / "pages"
    removed = 0
    current_order = list(pages_meta.get("pageOrder") or [])
    new_order: list[str] = []

    for page_id in current_order:
        page_json_path = pages_dir / page_id / "page.json"
        if not page_json_path.exists():
            continue

        try:
            page_obj = _read_json(page_json_path)
        except Exception:
            new_order.append(page_id)
            continue

        if str(page_obj.get("displayName") or "").strip().lower() == display_name.strip().lower():
            page_folder = pages_dir / page_id
            if page_folder.exists() and page_folder.is_dir():
                for child in sorted(page_folder.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                page_folder.rmdir()
            removed += 1
            continue

        new_order.append(page_id)

    pages_meta["pageOrder"] = new_order
    active = str(pages_meta.get("activePageName") or "")
    if active not in new_order:
        pages_meta["activePageName"] = new_order[0] if new_order else ""

    return pages_meta, removed


def _build_card_visual_json(visual_id: str, x: int, y: int, w: int, h: int, idx: int, metric: tuple[str, str] | None) -> dict:
    visual: dict = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": 10 + idx,
            "width": w,
            "height": h,
            "tabOrder": idx,
        },
        "visual": {
            "visualType": "card",
        },
    }

    if metric is not None:
        table_name, measure_name = metric
        query_ref = f"{table_name}.{measure_name}"
        visual["visual"]["query"] = {
            "queryState": {
                "Values": {
                    "projections": [
                        {
                            "field": {
                                "Measure": {
                                    "Expression": {
                                        "SourceRef": {
                                            "Entity": table_name
                                        }
                                    },
                                    "Property": measure_name,
                                }
                            },
                            "queryRef": query_ref,
                        }
                    ]
                }
            }
        }

    return visual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-PbipPath", required=True, help="Ruta al archivo .pbip o carpeta .Report")
    parser.add_argument("-BlueprintPath", default="", help="Ruta opcional al blueprint generado por autobuild")
    args = parser.parse_args()

    pbip_path = Path(_clean_path_value(args.PbipPath)).expanduser()
    report_def = _resolve_report_definition(pbip_path)

    pages_meta_path = report_def / "pages" / "pages.json"
    if not pages_meta_path.exists():
        raise RuntimeError(f"No existe pages.json en: {pages_meta_path}")

    pages_meta = _read_json(pages_meta_path)
    page_order = list(pages_meta.get("pageOrder") or [])

    pages_meta, removed_pages = _remove_existing_autovis_page(report_def, pages_meta, "AutoVis IA")
    page_order = list(pages_meta.get("pageOrder") or [])

    # Tomamos alto/ancho desde la primera pagina existente cuando sea posible.
    width, height = 1280, 720
    if page_order:
        sample_page = report_def / "pages" / page_order[0] / "page.json"
        if sample_page.exists():
            sample = _read_json(sample_page)
            width = int(sample.get("width") or width)
            height = int(sample.get("height") or height)

    repo_root = Path(__file__).resolve().parents[2]
    blueprint = Path(args.BlueprintPath) if args.BlueprintPath else (repo_root / "data" / "reference" / "autobuild" / "AUTOBUILD_REPORT_BLUEPRINT.md")

    blueprint_refs = _parse_measures_from_blueprint(blueprint)
    model_refs = _parse_measures_from_tmdl_tables(_resolve_semantic_tables_dir(pbip_path))
    selected_metrics = _pick_visual_metrics(blueprint_refs, model_refs)

    new_page_id = _make_id()
    page_dir = report_def / "pages" / new_page_id
    visuals_dir = page_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)

    page_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": new_page_id,
        "displayName": "AutoVis IA",
        "displayOption": "FitToPage",
        "height": height,
        "width": width,
        "annotations": [
            {
                "name": "autovis.version",
                "value": "pbip.v2"
            }
        ],
    }
    _write_json(page_dir / "page.json", page_json)

    x0, y0 = 30, 60
    w, h = 390, 220
    gx, gy = 25, 30

    created_visuals: list[str] = []
    for i, metric in enumerate(selected_metrics):
        r = i // 3
        c = i % 3
        vid = _make_id()
        vdir = visuals_dir / vid
        vdir.mkdir(parents=True, exist_ok=True)

        vx = x0 + c * (w + gx)
        vy = y0 + r * (h + gy)

        vjson = _build_card_visual_json(vid, vx, vy, w, h, i, metric)
        _write_json(vdir / "visual.json", vjson)
        created_visuals.append(vid)

    if new_page_id not in page_order:
        page_order.append(new_page_id)
    pages_meta["pageOrder"] = page_order
    pages_meta["activePageName"] = new_page_id
    pages_meta = _sync_pages_metadata(report_def, pages_meta)
    _write_json(pages_meta_path, pages_meta)

    print("AUTOVIS_PBIP_OK: SI")
    print(f"PBIP_INPUT: {pbip_path}")
    print(f"REPORT_DEFINITION: {report_def}")
    print(f"PAGE_CREATED: {new_page_id}")
    print(f"VISUALS_CREATED: {len(created_visuals)}")
    print(f"PAGES_REPLACED: {removed_pages}")
    print(f"MEASURES_FROM_BLUEPRINT: {len(blueprint_refs)}")
    print(f"MEASURES_FROM_MODEL: {len(model_refs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
