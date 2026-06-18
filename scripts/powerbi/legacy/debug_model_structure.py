#!/usr/bin/env python3
"""
Script de depuración para inspeccionar la estructura del modelo TMDL
y verificar que las visualizaciones se generarían correctamente.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from autovis_build_pbip_smart import ModelAnalyzer


def debug_model(pbip_path: str, verbose: bool = True):
    """Analiza el modelo TMDL y muestra diagnóstico detallado."""
    pbip = Path(pbip_path)
    if not pbip.exists():
        print(f"❌ PBIP no encontrado: {pbip_path}")
        return 1
    
    analyzer = ModelAnalyzer(pbip)
    
    print("\n" + "="*70)
    print("📊 ANÁLISIS DE ESTRUCTURA DEL MODELO TMDL")
    print("="*70)
    
    # Mostrar tablas encontradas
    print(f"\n📌 Tablas detectadas ({len(analyzer.tables)}):")
    for table_name, table_info in analyzer.tables.items():
        print(f"\n   📇 Tabla: '{table_name}'")
        
        if table_info["columns"]:
            print(f"      ✓ Columnas ({len(table_info['columns'])}):")
            for col in table_info["columns"][:5]:  # Primeras 5
                print(f"         - {col}")
            if len(table_info["columns"]) > 5:
                print(f"         ... +{len(table_info['columns']) - 5} más")
        else:
            print(f"      (sin columnas queryable)")
        
        if table_info["measures"]:
            print(f"      📈 Medidas ({len(table_info['measures'])}):")
            for table_m, measure in table_info["measures"][:5]:  # Primeras 5
                print(f"         - {measure}")
            if len(table_info["measures"]) > 5:
                print(f"         ... +{len(table_info['measures']) - 5} más")
        else:
            print(f"      (sin medidas)")
    
    # Mostrar lo que se generaría
    print(f"\n\n🎯 VISUALIZACIONES QUE SE GENERARÍAN (Limit=4):")
    visuals = analyzer.get_best_visuals(limit=4)
    
    for idx, vis in enumerate(visuals, 1):
        vis_type = vis.get("type", "unknown")
        table = vis.get("table", "")
        field = vis.get("field", "")
        is_measure = vis.get("is_measure", False)
        
        print(f"\n   {idx}. {vis_type.upper()}")
        print(f"      Tabla: '{table}'")
        print(f"      Campo: '{field}'")
        print(f"      Tipo: {'📈 MEDIDA' if is_measure else '📋 COLUMNA'}")
        
        if vis_type == "blank":
            print(f"      ⚠️  (vacío)")
        elif table and field:
            # Mostrar qué estructura tendrá la query
            if is_measure:
                print(f"      Query: Measure('{table}', '{field}')")
            else:
                print(f"      Query: Column('{table}', '{field}')")
    
    print("\n" + "="*70)
    print("✅ Análisis completo")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python debug_model_structure.py <ruta_pbip>")
        sys.exit(1)
    
    pbip_path = sys.argv[1].strip('"').strip("'")
    verbose = "-Verbose" in sys.argv or "-v" in sys.argv
    
    sys.exit(debug_model(pbip_path, verbose))
