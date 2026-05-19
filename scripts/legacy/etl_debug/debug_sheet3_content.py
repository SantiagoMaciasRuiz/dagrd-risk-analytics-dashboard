#!/usr/bin/env python3
"""Debug ETL: verificar si sheet3 (Simulacros) está siendo leído correctamente"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"
SHEET_SIMULACROS = "Simulacros"

NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
RID_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

def _get_sheet_xml_target(zf, sheet_name):
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("r:Relationship", NS_REL)}

    sheets = workbook.find("m:sheets", NS_MAIN)
    for sheet in sheets.findall("m:sheet", NS_MAIN):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(RID_NS)
            target = rel_map.get(rel_id, "")
            if not target:
                break
            targ = target.lstrip('/')
            return targ if targ.startswith("xl/") else f"xl/{targ}"
    raise RuntimeError(f"No se encontró la hoja '{sheet_name}'.")

try:
    with zipfile.ZipFile(REPORT_FILE) as zf:
        # Obtener target XML
        target = _get_sheet_xml_target(zf, SHEET_SIMULACROS)
        print(f"✓ Target XML para '{SHEET_SIMULACROS}': {target}")
        
        # Leer XML
        root = ET.fromstring(zf.read(target))
        data = root.find("m:sheetData", NS_MAIN)
        
        if data is None:
            print(f"✗ No sheetData en {target}")
        else:
            rows = data.findall("m:row", NS_MAIN)
            print(f"✓ Filas en sheetData: {len(rows)}")
            
            # Mostrar primeras 3 filas
            for i, row in enumerate(rows[:3]):
                row_num = row.attrib.get("r", "?")
                cells = row.findall("m:c", NS_MAIN)
                print(f"  Fila {row_num}: {len(cells)} celdas")
                
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
