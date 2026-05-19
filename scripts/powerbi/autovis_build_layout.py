#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


def read_json_with_detected_encoding(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    for enc in ("utf-16-le", "utf-16-be", "utf-8"):
        try:
            obj = json.loads(raw.decode(enc))
            return obj, enc
        except Exception:
            continue
    raise RuntimeError(f"No se pudo parsear JSON de Layout: {path}")


def write_json_with_encoding(path: Path, data: dict, enc: str) -> None:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_bytes(text.encode(enc))


def parse_measures_from_blueprint(blueprint_path: Path) -> list[tuple[str, str]]:
    if not blueprint_path.exists():
        return []

    pattern = re.compile(r"^-\s+([^.\s]+)\.[^\s]+\s+->\s+([^,\s]+)")
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


def find_card_template(layout: dict) -> dict:
    for section in layout.get("sections", []):
        for vc in section.get("visualContainers", []):
            cfg_raw = vc.get("config")
            if not isinstance(cfg_raw, str):
                continue
            try:
                cfg = json.loads(cfg_raw)
            except Exception:
                continue
            if cfg.get("singleVisual", {}).get("visualType") == "card":
                return vc
    raise RuntimeError("No se encontro plantilla card en Layout")


def build_card_config(template_cfg: dict, table: str, measure: str, visual_name: str) -> dict:
    cfg = deepcopy(template_cfg)
    single = cfg.setdefault("singleVisual", {})
    single["visualType"] = "card"

    query_ref = f"{table}.{measure}"
    single["projections"] = {"Values": [{"queryRef": query_ref}]}
    single["prototypeQuery"] = {
        "Version": 2,
        "From": [{"Name": "t", "Entity": table, "Type": 0}],
        "Select": [
            {
                "Measure": {
                    "Expression": {"SourceRef": {"Source": "t"}},
                    "Property": measure,
                },
                "Name": query_ref,
                "NativeReferenceName": measure,
            }
        ],
        "OrderBy": [
            {
                "Direction": 2,
                "Expression": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "t"}},
                        "Property": measure,
                    }
                },
            }
        ],
    }

    vc_objects = single.get("vcObjects", {})
    title = vc_objects.get("title")
    if isinstance(title, list) and title:
        title_entry = title[0]
        props = title_entry.setdefault("properties", {})
        props["text"] = {"expr": {"Literal": {"Value": f"'{measure}'"}}}
        props["show"] = {"expr": {"Literal": {"Value": "true"}}}

    cfg["name"] = visual_name
    return cfg


def ensure_min_6(measures: list[tuple[str, str]]) -> list[tuple[str, str]]:
    if not measures:
        raise RuntimeError("No se encontraron medidas para construir visuales. Ejecuta /autobuild o /autofull primero.")
    out = measures[:6]
    while len(out) < 6:
        out.append(measures[0])
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Port", type=int, default=0)
    parser.add_argument("-DatabaseName", default="")
    parser.add_argument("-LayoutPath", default="")
    parser.add_argument("-BlueprintPath", default="")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    layout_path = Path(args.LayoutPath) if args.LayoutPath else (repo_root / "Tableros" / "_pbix_extract_temp" / "Report" / "Layout")
    blueprint_path = Path(args.BlueprintPath) if args.BlueprintPath else (repo_root / "data" / "reference" / "autobuild" / "AUTOBUILD_REPORT_BLUEPRINT.md")

    if not layout_path.exists():
        raise RuntimeError(f"No existe Layout para autovis: {layout_path}")

    layout, encoding = read_json_with_detected_encoding(layout_path)
    if not layout.get("sections"):
        raise RuntimeError("Layout sin secciones")

    measures = parse_measures_from_blueprint(blueprint_path)
    picked = ensure_min_6(measures)

    template_vc = find_card_template(layout)
    template_cfg = json.loads(template_vc["config"])

    section_template = deepcopy(layout["sections"][0])
    section_template["name"] = f"AutoVisSection_{Path(layout_path).stat().st_mtime_ns}"
    section_template["displayName"] = "AutoVis IA"
    section_template["ordinal"] = len(layout["sections"])
    section_template["visualContainers"] = []
    section_template["filters"] = "[]"

    x0, y0 = 30, 60
    w, h = 390, 220
    gx, gy = 25, 30

    for i, (table, measure) in enumerate(picked):
        row = i // 3
        col = i % 3
        vc = deepcopy(template_vc)
        vc["x"] = x0 + col * (w + gx)
        vc["y"] = y0 + row * (h + gy)
        vc["z"] = 10 + i
        vc["width"] = w
        vc["height"] = h
        vc["filters"] = "[]"

        cfg = build_card_config(template_cfg, table, measure, f"AutoVisCard_{i+1}")
        vc["config"] = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
        section_template["visualContainers"].append(vc)

    layout["sections"].append(section_template)
    write_json_with_encoding(layout_path, layout, encoding)

    print("AUTOVIS_OK: SI")
    print(f"LAYOUT_ACTUALIZADO: {layout_path}")
    print(f"SECCION_AGREGADA: {section_template['displayName']}")
    print(f"VISUALES_CREADOS: {len(section_template['visualContainers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
