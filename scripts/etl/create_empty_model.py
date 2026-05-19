#!/usr/bin/env python3
"""Crear archivo modelo vacío para ser completado por reparar_hojas_modelo_para_powerbi.py"""

from openpyxl import Workbook
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
MODELO = BASE / "data" / "model" / "Modelo_Reporte_Paginas_2026.xlsx"

# Crear workbook con hoja vacía
wb = Workbook()
ws = wb.active
ws.title = "Temp"

# Guardar
wb.save(MODELO)
print(f"✓ Archivo modelo creado: {MODELO}")
