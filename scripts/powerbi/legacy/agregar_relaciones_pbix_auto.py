#!/usr/bin/env python3
"""
Script para agregar relaciones al PBIX de Power BI Desktop
Modifica el archivo PBIX directo (es un ZIP con JSON)
"""

import zipfile
import json
import shutil
from pathlib import Path

def agregar_relaciones_pbix():
    """Agrega relaciones al PBIX existente"""
    
    pbix_folder = Path("powerbi/pbix")
    pbix_files = list(pbix_folder.glob("*.pbix"))
    
    if not pbix_files:
        print("❌ No se encontró archivo .pbix")
        return False
    
    pbix_file = pbix_files[0]
    print(f"📄 Archivo encontrado: {pbix_file.name}")
    
    # Crear backup
    backup_file = pbix_file.with_suffix(".pbix.backup")
    shutil.copy(pbix_file, backup_file)
    print(f"✓ Backup creado: {backup_file.name}")
    
    try:
        # Extraer PBIX (que es un ZIP)
        extract_dir = Path("_pbix_temp")
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        
        with zipfile.ZipFile(pbix_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"✓ PBIX extraído")
        
        # Buscar archivo de modelo
        model_files = list(extract_dir.glob("**/Model-*.json"))
        if not model_files:
            print("❌ No se encontró archivo de modelo JSON")
            return False
        
        model_file = model_files[0]
        print(f"✓ Modelo encontrado: {model_file.name}")
        
        # Cargar JSON del modelo
        with open(model_file, 'r', encoding='utf-8') as f:
            model = json.load(f)
        
        # Verificar que la sección de relationships existe
        if "relationships" not in model:
            model["relationships"] = []
        
        print(f"\n📊 MODELO ACTUAL:")
        print(f"   Tablas: {len(model.get('tables', []))}")
        print(f"   Relaciones: {len(model.get('relationships', []))}")
        
        # Listar tablas
        print(f"\n📋 TABLAS DISPONIBLES:")
        for table in model.get('tables', []):
            print(f"   ✓ {table.get('name')}")
        
        # Crear relaciones nuevas
        relaciones_nuevas = [
            {
                "name": "Dim_Semilleros_to_Hecho",
                "fromTable": "Dim_Semilleros",
                "fromColumn": "Comuna",
                "toTable": "Hecho_Participacion_General",
                "toColumn": "comuna_cod",
                "crossFilteringBehavior": "oneDirection",
                "type": "regular"
            },
            {
                "name": "Dim_SATC_to_Hecho",
                "fromTable": "Dim_SATC",
                "fromColumn": "SATC_ID",
                "toTable": "Hecho_Participacion_General",
                "toColumn": "satc_id",
                "crossFilteringBehavior": "oneDirection",
                "type": "regular"
            }
        ]
        
        # Agregar relaciones
        print(f"\n🔗 CREANDO RELACIONES:")
        for rel in relaciones_nuevas:
            model["relationships"].append(rel)
            print(f"   ✓ {rel['name']}")
            print(f"     {rel['fromTable']}[{rel['fromColumn']}] → {rel['toTable']}[{rel['toColumn']}]")
        
        # Guardar modelo actualizado
        with open(model_file, 'w', encoding='utf-8') as f:
            json.dump(model, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Modelo actualizado con 2 relaciones nuevas")
        
        # Comprimir nuevamente (recrear PBIX)
        with zipfile.ZipFile(pbix_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file in extract_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(extract_dir)
                    zip_ref.write(file, arcname)
        
        print(f"✓ PBIX regenerado")
        
        # Limpiar temp
        shutil.rmtree(extract_dir)
        
        print(f"\n" + "="*80)
        print(f"✅ RELACIONES AGREGADAS EXITOSAMENTE")
        print(f"="*80)
        print(f"\nProximos pasos:")
        print(f"1. Cierra Power BI Desktop completamente")
        print(f"2. Vuelve a abrir: {pbix_file.name}")
        print(f"3. Ve a Modelado y verifica las 2 relaciones nuevas")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    agregar_relaciones_pbix()
