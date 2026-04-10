#!/usr/bin/env python3
"""
Script para agregar relaciones automáticamente a un archivo PBIX
Modifica el modelo semántico dentro del PBIX sin abrir Power BI
"""

import json
import zipfile
import shutil
from pathlib import Path
import tempfile

def crear_relaciones_automaticamente():
    """
    Agrega relaciones al archivo PBIX modificando su contenido XML/JSON
    """
    
    print("=" * 80)
    print("AGREGAR RELACIONES AL ARCHIVO PBIX")
    print("=" * 80)
    
    # Buscar archivo PBIX
    pbix_path = Path("powerbi/pbix")
    if not pbix_path.exists():
        print(f"❌ Carpeta {pbix_path} no existe")
        return False
    
    pbix_files = list(pbix_path.glob("*.pbix"))
    if not pbix_files:
        print(f"❌ No se encontraron archivos .pbix en {pbix_path}")
        return False
    
    pbix_file = pbix_files[0]
    print(f"\n✓ Archivo encontrado: {pbix_file.name}")
    
    # Crear backup
    backup_file = pbix_file.with_stem(pbix_file.stem + "_BACKUP")
    shutil.copy2(pbix_file, backup_file)
    print(f"✓ Backup creado: {backup_file.name}")
    
    try:
        # Extraer PBIX (es un ZIP)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Descomprimir
            with zipfile.ZipFile(pbix_file, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            print("✓ Archivo PBIX descomprimido")
            
            # Buscar archivo del modelo
            model_file = temp_path / "DataModel" / "model.json"
            if not model_file.exists():
                # Probar otra ruta common
                model_files = list(temp_path.glob("**/model.json"))
                if model_files:
                    model_file = model_files[0]
                else:
                    print("❌ Archivo model.json no encontrado")
                    return False
            
            print(f"✓ Modelo encontrado: {model_file}")
            
            # Cargar modelo
            with open(model_file, 'r', encoding='utf-8') as f:
                model = json.load(f)
            
            # Agregar relaciones si no existen
            if 'relationships' not in model:
                model['relationships'] = []
            
            print(f"✓ Relaciones actuales: {len(model.get('relationships', []))}")
            
            # RELACIÓN 1: Dim_Semilleros → Hecho_Participacion_General
            rel1 = {
                "name": "Dim_Semilleros_to_Hecho",
                "fromTable": "Dim_Semilleros",
                "fromColumn": "Comuna",
                "toTable": "Hecho_Participacion_General",
                "toColumn": "comuna_cod",
                "fromCardinality": "many",
                "toCardinality": "one",
                "isActive": True
            }
            
            # RELACIÓN 2: Dim_SATC → Hecho_Participacion_General
            rel2 = {
                "name": "Dim_SATC_to_Hecho",
                "fromTable": "Dim_SATC",
                "fromColumn": "SATC_ID",
                "toTable": "Hecho_Participacion_General",
                "toColumn": "satc_id",
                "fromCardinality": "many",
                "toCardinality": "one",
                "isActive": True
            }
            
            # Verificar si ya existen
            rel_names = [r.get('name') for r in model.get('relationships', [])]
            
            if rel1['name'] not in rel_names:
                model['relationships'].append(rel1)
                print("✓ Relación 1 agregada (Semilleros → Hecho)")
            else:
                print("⚠ Relación 1 ya existe")
            
            if rel2['name'] not in rel_names:
                model['relationships'].append(rel2)
                print("✓ Relación 2 agregada (SATC → Hecho)")
            else:
                print("⚠ Relación 2 ya existe")
            
            # Guardar modelo
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(model, f, indent=2)
            
            print("✓ Modelo actualizado")
            
            # Recomprimir
            with zipfile.ZipFile(pbix_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zip_ref.write(file_path, arcname)
            
            print("✓ Archivo PBIX recomprimido")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"⚠ Restaurando desde backup...")
        shutil.copy2(backup_file, pbix_file)
        return False
    
    print("\n" + "=" * 80)
    print("✅ RELACIONES CREADAS EXITOSAMENTE")
    print("=" * 80)
    print("\nProximos pasos:")
    print("1. Cierra Power BI si está abierto")
    print("2. Reabre el archivo PBIX")
    print("3. Ve a Modelado y verifica las relaciones")
    print("4. Deberías ver 2 líneas azules nuevas")
    
    return True

if __name__ == "__main__":
    crear_relaciones_automaticamente()
