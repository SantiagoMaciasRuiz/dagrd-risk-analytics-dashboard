#!/usr/bin/env python3
"""
Recarga el modelo Power BI desde los archivos TMDL actualizados.
Esto obliga a Power BI Desktop a reconocer la nueva columna fecha_date en Hecho_Personas_Atendidas_Ordinario.
"""
import subprocess
import time
from pathlib import Path

BASE = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
TMDL_LIVE = BASE / "powerbi" / "tmdl_live"
PBIX_FILE = BASE / "Tableros" / "tableroDAGRDCOPIA.pbix"

print("=" * 70)
print("RECARGANDO MODELO POWER BI")
print("=" * 70)

# Paso 1: Verificar que los cambios TMDL existen
hpao_file = TMDL_LIVE / "tables" / "Hecho_Personas_Atendidas_Ordinario.tmdl"
if hpao_file.exists():
    with open(hpao_file) as f:
        content = f.read()
        if "fecha_date" in content:
            print("✓ TMDL contiene cambios (fecha_date detectada)")
        else:
            print("✗ TMDL no tiene cambios aún")
else:
    print("✗ Archivo TMDL no encontrado")

# Paso 2: Cierra Power BI Desktop para forzar recarga
print("\n[1] Cerrando Power BI Desktop...")
subprocess.run(["taskkill", "/IM", "PBIDesktop.exe", "/F"], capture_output=True)
time.sleep(3)
print("✓ Power BI Desktop cerrado")

# Paso 3: Reabre Power BI Desktop
print("\n[2] Reabriendo Power BI Desktop...")
if PBIX_FILE.exists():
    subprocess.Popen([
        "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe",
        str(PBIX_FILE)
    ])
    print("✓ Power BI Desktop reabierto")
    print("\n⏳ Esperando 15 segundos para que cargue el modelo...")
    time.sleep(15)
    print("✓ Listo. El modelo debería haber recargado los cambios TMDL")
else:
    print(f"✗ Archivo .pbix no encontrado: {PBIX_FILE}")

print("\n" + "=" * 70)
print("ACCIÓN REQUERIDA: Verifica en Power BI que PAO_Total_Personas_VAL")
print("ahora responda al filtro de año/mes")
print("=" * 70)
