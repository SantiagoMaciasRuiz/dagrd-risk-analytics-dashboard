#!/usr/bin/env python3
"""Debug: verificar si el ETL puede encontrar la hoja Simulacros en el archivo source"""

import zipfile
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
REPORT_FILE = BASE / "data" / "source" / "Reporte de actividades equipo social 2026.xlsx"

print(f"Archivo source: {REPORT_FILE}")
print(f"¿Existe? {REPORT_FILE.exists()}")

if REPORT_FILE.exists():
    try:
        with zipfile.ZipFile(REPORT_FILE) as zf:
            # Leer workbook.xml para ver nombres de hojas
            import xml.etree.ElementTree as ET
            workbook_xml = ET.fromstring(zf.read("xl/workbook.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            
            sheets = workbook_xml.find("m:sheets", ns)
            if sheets:
                sheet_names = []
                for sheet in sheets.findall("m:sheet", ns):
                    name = sheet.attrib.get("name", "")
                    sheet_names.append(name)
                print(f"\nHojas en XML (workbook.xml):")
                for i, name in enumerate(sheet_names, 1):
                    print(f"  {i}. {name}")
                    
                # Verificar "Simulacros"
                if "Simulacros" in sheet_names:
                    print(f"\n✓ Hoja 'Simulacros' ENCONTRADA")
                else:
                    print(f"\n✗ Hoja 'Simulacros' NO ENCONTRADA")
                    print(f"   Nombres disponibles: {sheet_names}")
    except Exception as e:
        print(f"Error leyendo XML: {e}")
