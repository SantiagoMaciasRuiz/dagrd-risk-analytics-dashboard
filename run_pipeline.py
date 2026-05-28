#!/usr/bin/env python3
"""
Pipeline ETL para actualizar Power BI con datos de Excel
Fases: Validación -> AutoBuild -> AutoFull -> AutoVis -> Apertura
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api"
SOURCE_DIR = Path(r"C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\source")


def _find_excel_path() -> Path:
    candidates = sorted(
        SOURCE_DIR.glob("Reporte de actividades equipo social*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else SOURCE_DIR / "Reporte de actividades equipo social 2026.xlsx"


EXCEL_PATH = _find_excel_path()

def print_phase(phase_num, phase_name, action):
    """Imprimir encabezado de fase"""
    print("\n" + "=" * 70)
    print(f"⏳ FASE {phase_num}: {phase_name}")
    print(f"   Acción: {action}")
    print("=" * 70)

def print_result(success, message=""):
    """Imprimir resultado"""
    if success:
        print(f"✅ {message}" if message else "✅ Exitoso")
    else:
        print(f"❌ {message}" if message else "❌ Fallo")

def verify_excel():
    """Verificar que el archivo Excel existe"""
    excel_file = Path(EXCEL_PATH)
    if not excel_file.exists():
        print_result(False, f"Archivo Excel no encontrado: {EXCEL_PATH}")
        return False
    print_result(True, f"Excel encontrado: {excel_file.name}")
    print(f"   Tamaño: {excel_file.stat().st_size / 1024:.1f} KB")
    print(f"   Modificado: {time.ctime(excel_file.stat().st_mtime)}")
    return True

def verify_backend():
    """Verificar que el backend está activo"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        data = r.json()
        print_result(True, "Backend activo")
        print(f"   Modelo: {data.get('default_model')}")
        print(f"   Ollama: {data.get('ollama_base_url')}")
        return True
    except Exception as e:
        print_result(False, f"Backend no responde: {e}")
        return False

def run_autobuild():
    """FASE 2: AutoBuild - Crear medidas DAX"""
    print_phase(2, "AUTOBUILD", "Crear medidas DAX automáticas")
    
    payload = {
        "script_name": "autobuild_model_from_loaded_tables.ps1",
        "args": [],
        "confirmed": True
    }
    
    try:
        print("   Enviando solicitud...")
        r = requests.post(
            f"{BASE_URL}/run-powerbi-script",
            json=payload,
            timeout=180  # 3 minutos
        )
        result = r.json()
        
        if result.get("exit_code") == 0:
            print_result(True, "AutoBuild completado")
            if "stdout" in result:
                lines = result["stdout"].split("\n")[:5]
                for line in lines:
                    if line.strip():
                        print(f"   {line[:100]}")
            return True
        else:
            stderr = result.get("stderr", "Sin detalle")
            print_result(False, f"AutoBuild falló")
            print(f"   Error: {stderr[:200]}")
            print(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            return False
    except Exception as e:
        print_result(False, f"Error de conexión: {e}")
        return False

def run_autofull():
    """FASE 3: AutoFull - Generar tema y blueprint"""
    print_phase(3, "AUTOFULL", "Generar tema, blueprint y medidas")
    
    payload = {
        "script_name": "autofull_build_powerbi.ps1",
        "args": [],
        "confirmed": True
    }
    
    try:
        print("   Enviando solicitud...")
        r = requests.post(
            f"{BASE_URL}/run-powerbi-script",
            json=payload,
            timeout=120  # 2 minutos
        )
        result = r.json()
        
        if result.get("exit_code") == 0:
            print_result(True, "AutoFull completado")
            if "stdout" in result:
                lines = result["stdout"].split("\n")[:3]
                for line in lines:
                    if line.strip() and "medidas" in line.lower():
                        print(f"   {line[:100]}")
            return True
        else:
            stderr = result.get("stderr", "Sin detalle")
            print_result(False, f"AutoFull falló")
            print(f"   {stderr[:200]}")
            return False
    except Exception as e:
        print_result(False, f"Error de conexión: {e}")
        return False

def run_autovis():
    """FASE 4: AutoVis - Generar páginas y visuales"""
    print_phase(4, "AUTOVIS", "Generar páginas y visuales inteligentes con LLM")
    
    payload = {
        "script_name": "autovis_build_pbip_smart.py",
        "args": [],
        "confirmed": True
    }
    
    try:
        print("   Enviando solicitud (puede tomar 2-5 minutos)...")
        r = requests.post(
            f"{BASE_URL}/run-powerbi-script-smart",
            json=payload,
            timeout=600  # 10 minutos max
        )
        result = r.json()
        
        if result.get("exit_code") == 0:
            print_result(True, "AutoVis completado")
            if "stdout" in result:
                for keyword in ["páginas", "visuales", "generadas"]:
                    for line in result["stdout"].split("\n"):
                        if keyword in line.lower():
                            print(f"   {line.strip()[:100]}")
                            break
            return True
        else:
            stderr = result.get("stderr", "Sin detalle")
            print_result(False, f"AutoVis falló")
            print(f"   {stderr[:200]}")
            return False
    except Exception as e:
        print_result(False, f"Error de conexión: {e}")
        return False

def open_powerbi():
    """FASE 5: Abrir Power BI Desktop"""
    print_phase(5, "APERTURA", "Abrir Power BI Desktop con dashboard actualizado")
    
    try:
        # Buscar PBIP file más reciente
        project_dir = Path("powerbi")
        pbip_files = list(project_dir.glob("*.pbip"))
        
        if pbip_files:
            pbip_file = max(pbip_files, key=lambda p: p.stat().st_mtime)
            print_result(True, f"Abriendo: {pbip_file.name}")
            print(f"   Ruta: {pbip_file.absolute()}")
            
            # Abrir con Power BI
            import subprocess
            subprocess.Popen(["powershell.exe", "-Command", f'Start-Process "{pbip_file.absolute()}"'])
            print("   ⏳ Esperando apertura en Power BI (30-60 segundos)...")
            time.sleep(3)
            return True
        else:
            print_result(False, "No se encontró archivo PBIP")
            return False
    except Exception as e:
        print_result(False, f"Error al abrir Power BI: {e}")
        return False

def main():
    """Ejecutar pipeline completo"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║  " + " PIPELINE ETL - ACTUALIZACIÓN DASHBOARD ".center(65) + "║")
    print("║  " + " 30 de abril de 2026 ".center(65) + "║")
    print("╚" + "═" * 68 + "╝\n")
    
    # VALIDACIÓN INICIAL
    print_phase(1, "VALIDACIÓN", "Verificar Excel y Backend")
    
    if not verify_excel():
        sys.exit(1)
    
    time.sleep(1)
    
    if not verify_backend():
        sys.exit(1)
    
    # PIPELINE
    time.sleep(2)
    
    if not run_autobuild():
        print("\n❌ Pipeline interrumpido en AutoBuild")
        sys.exit(1)
    
    time.sleep(2)
    
    if not run_autofull():
        print("\n❌ Pipeline interrumpido en AutoFull")
        sys.exit(1)
    
    time.sleep(2)
    
    if not run_autovis():
        print("\n❌ Pipeline interrumpido en AutoVis")
        sys.exit(1)
    
    time.sleep(2)
    
    if not open_powerbi():
        print("\n⚠️  Pipeline completado pero no se pudo abrir Power BI automáticamente")
        print("   Abre manualmente: powerbi/*.pbip")
    
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║  " + "✅ PIPELINE COMPLETADO EXITOSAMENTE".center(65) + "║")
    print("║  " + "Dashboard actualizado con datos del 30/04/2026".center(65) + "║")
    print("╚" + "═" * 68 + "╝\n")

if __name__ == "__main__":
    main()
