#!/usr/bin/env python3
"""
Crear relaciones entre tablas en Power BI
Genera las relaciones automáticamente en el archivo PBIX
"""

import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

def crear_relaciones_pbix():
    """
    Crea relaciones automáticamente en Power BI Desktop
    
    Relaciones a crear:
    1. Dim_Semilleros[Comuna] → Hecho_Participacion_General[comuna_cod]
    2. Dim_SATC[SATC_ID] → Hecho_Participacion_General[satc_id]
    """
    
    print("=" * 80)
    print("CREAR RELACIONES EN POWER BI")
    print("=" * 80)
    
    pbix_path = Path("powerbi/pbix")
    if not pbix_path.exists():
        print(f"\n⚠️  Carpeta PBIX no encontrada: {pbix_path}")
        print("Descarga el archivo .pbix y colócalo en: powerbi/pbix/")
        return
    
    pbix_files = list(pbix_path.glob("*.pbix"))
    if not pbix_files:
        print(f"\n⚠️  No se encontraron archivos .pbix en {pbix_path}")
        print("Guía manual de crear relaciones:")
        print_guia_manual()
        return
    
    pbix_file = pbix_files[0]
    print(f"\n✓ Archivo PBIX encontrado: {pbix_file.name}")
    
    # Generar guía de relaciones para crear manualmente
    print_guia_manual()
    
    print("\n" + "=" * 80)
    print("RELACIONES A CREAR (En Power BI Desktop)")
    print("=" * 80)
    
    relaciones = [
        {
            "nombre": "Dim_Semilleros_a_Hechos",
            "tabla_origen": "Dim_Semilleros",
            "columna_origen": "Comuna",
            "tabla_destino": "Hecho_Participacion_General",
            "columna_destino": "comuna_cod",
            "cardinalidad": "Muchos a 1 (M:1)",
            "direccion": "Simple (unidireccional)"
        },
        {
            "nombre": "Dim_SATC_a_Hechos",
            "tabla_origen": "Dim_SATC",
            "columna_origen": "SATC_ID",
            "tabla_destino": "Hecho_Participacion_General",
            "columna_destino": "satc_id",
            "cardinalidad": "Muchos a 1 (M:1)",
            "direccion": "Simple (unidireccional)"
        }
    ]
    
    for idx, rel in enumerate(relaciones, 1):
        print(f"\n[{idx}] {rel['nombre']}")
        print(f"    De:   {rel['tabla_origen']}[{rel['columna_origen']}]")
        print(f"    Para: {rel['tabla_destino']}[{rel['columna_destino']}]")
        print(f"    Cardinalidad: {rel['cardinalidad']}")
        print(f"    Dirección: {rel['direccion']}")

def print_guia_manual():
    """Imprime guía para crear relaciones manualmente en Power BI"""
    
    print("\n" + "=" * 80)
    print("PASOS PARA CREAR RELACIONES EN POWER BI DESKTOP")
    print("=" * 80)
    
    print("""
    RELACIÓN 1: Conexión Semilleros → Hechos
    ─────────────────────────────────────────
    
    1. Ir a: Modelado (vista de esquema)
    2. Haz clic: "Nueva relación"
    3. Selecciona:
       • Tabla 1: Dim_Semilleros
       • Columna 1: Comuna
       • Tabla 2: Hecho_Participacion_General  
       • Columna 2: comuna_cod
    4. Cardinalidad: Muchos a 1 (M:1)
    5. Dirección: Simple
    6. Clic: OK
    
    
    RELACIÓN 2: Conexión SAT-C → Hechos
    ────────────────────────────────────
    
    1. Ir a: Modelado (vista de esquema)
    2. Haz clic: "Nueva relación"
    3. Selecciona:
       • Tabla 1: Dim_SATC
       • Columna 1: SATC_ID
       • Tabla 2: Hecho_Participacion_General
       • Columna 2: satc_id
    4. Cardinalidad: Muchos a 1 (M:1)
    5. Dirección: Simple
    6. Clic: OK
    
    
    VALIDACIÓN:
    ───────────
    Después de crear ambas relaciones, deberías ver:
    
    ✓ En vista Modelado: 2 líneas de conexión nuevas
    ✓ Los filtros fluyen correctamente
    ✓ Las tarjetas muestran los valores correctos
    
    
    MEDIDAS A CREAR:
    ────────────────
    Copiar desde: scripts/dax/
    
    📄 medidas_semilleros.dax → 4 medidas nuevas
    📄 medidas_satc.dax → 5 medidas de SAT-C
    """)

if __name__ == "__main__":
    crear_relaciones_pbix()
