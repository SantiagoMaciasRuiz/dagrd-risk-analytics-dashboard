#!/usr/bin/env python3
"""
Auditoría completa del modelo Power BI: medidas usadas, huérfanas, duplicadas, quebradas, obsoletas.
Genera un JSON con clasificación detallada.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

BASE = Path(__file__).parent.parent.parent

TMDL_FILE = BASE / "powerbi" / "tmdl_live" / "tables" / "_Medidas.tmdl"
VISUALES_CSV = BASE / "data" / "reference" / "powerbi_consultas_visuales_2026.csv"
OUT_AUDIT = BASE / "data" / "reference" / "audit_medidas_2026.json"

# Patrones de obsolescencia
OBSOLETE_PATTERNS = [
    r"^OLD_",
    r"^LEGACY_",
    r"^DEPRECAT",
    r"_V[0-9]+$",
    r"_BORRAR$",
    r"^TEMP_",
    r"_BACKUP$",
]

# Categorías de medidas
CATEGORY_KEYWORDS = {
    "GenF_": "General",
    "Ctl_": "Control/Validación",
    "Dem_": "Demografía",
    "Actividades_": "Actividades",
    "Participantes_": "Participantes",
    "Simulacros_": "Simulacros",
    "Impacto_": "Impacto",
    "Cobertura_": "Cobertura",
    "CAM_": "CAM/Empresarial",
    "Lista_": "Listas/Detalle",
    "Edu_": "Educación",
    "Articul": "Institucional",
    "Mesas_": "Institucional",
    "Acciones_": "Institucional",
}

def parse_measures() -> Dict[str, Dict]:
    """Parse todas las medidas del archivo TMDL."""
    with open(TMDL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    measures = {}
    # Regex para extraer medidas
    pattern = r"measure\s+([A-Za-z0-9_]+)\s*=\s*(.+?)(?=^\s*measure\s+|^\s*column\s+|^\s*partition\s+|\Z)"
    
    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        name = match.group(1)
        expr = match.group(2).strip()
        
        # Detectar si es oculta
        is_hidden = "isHidden" in expr
        
        # Extraer displayFolder si existe
        display_folder = ""
        folder_match = re.search(r'displayFolder:\s*([^\n]+)', expr)
        if folder_match:
            display_folder = folder_match.group(1).strip()
        
        # Detectar si es VAL (backing measure)
        is_val_measure = name.endswith("_VAL")
        
        # Limitar expresión para almacenar (primeras 200 chars)
        expr_short = expr[:200].replace('\n', ' ').replace('\t', ' ')
        
        measures[name] = {
            "name": name,
            "expression": expr_short,
            "full_expression": expr,
            "is_hidden": is_hidden,
            "is_val_measure": is_val_measure,
            "display_folder": display_folder,
            "category": categorize_measure(name),
        }
    
    return measures

def categorize_measure(name: str) -> str:
    """Categoriza medida por su nombre."""
    for prefix, category in CATEGORY_KEYWORDS.items():
        if prefix in name:
            return category
    return "Otra"

def extract_referenced_measures(full_expr: str) -> Set[str]:
    """Extrae medidas referenciadas en una expresión DAX."""
    # Busca referencias como [Medida_Nombre]
    pattern = r'\[([A-Za-z0-9_]+)\]'
    refs = set(re.findall(pattern, full_expr))
    
    # Filtrar referencias a tablas/columnas comunes
    filtered = set()
    for ref in refs:
        if not any(common in ref for common in ["participantes", "actividades", "personas", "valores", "impacto", "fecha", "comuna", "instancia"]):
            filtered.add(ref)
    return filtered

def check_dax_errors(expr: str) -> List[str]:
    """Detecta posibles errores en DAX."""
    errors = []
    
    # Buscar CALCULATE mal formado
    if re.search(r'CALCULATE\s*\(\s*(?:REMOVEFILTERS|KEEPFILTERS)?\s*\)', expr):
        # Si después hay argumentos, no es error
        if not re.search(r'CALCULATE\s*\([^)]*[A-Za-z]', expr):
            errors.append("CALCULATE potencialmente sin argumentos válido")
    
    # Contar paréntesis de forma simple
    open_parens = expr.count('(')
    close_parens = expr.count(')')
    
    # Si hay gran diferencia en paréntesis, podría haber error
    if abs(open_parens - close_parens) > 2:
        errors.append(f"Paréntesis desbalanceados ({open_parens} vs {close_parens})")
    
    # Buscar DIVIDE sin 3er argumento para alternativa (menos crítico, pero worth noting)
    # DIVIDE(a, b) es válido - retorna blanco si b=0
    # DIVIDE(a, b, c) es mejor - retorna c si b=0
    
    return errors

def is_obsolete(name: str) -> bool:
    """Detecta si una medida es obsoleta."""
    return any(re.search(pattern, name, re.IGNORECASE) for pattern in OBSOLETE_PATTERNS)

def find_duplicates(measures: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Encuentra medidas que podrían ser duplicadas."""
    duplicates = defaultdict(list)
    
    # Agrupar por raíz del nombre (sin _VAL)
    roots = defaultdict(list)
    for name in measures.keys():
        root = name.replace("_VAL", "").replace("_2", "").replace("_v2", "")
        roots[root].append(name)
    
    for root, names in roots.items():
        if len(names) > 1:
            duplicates[root] = sorted(names)
    
    return duplicates

def extract_visual_measures(visuales_csv: Path) -> Set[str]:
    """Extrae el nombres de medidas usadas en visuales desde CSV."""
    used = set()
    
    if not visuales_csv.exists():
        return used
    
    with open(visuales_csv, 'r', encoding='utf-8') as f:
        for line in f:
            # Buscar referencias a medidas en los query_refs
            # El formato es como "Sum(Sheet1.Indique...)" o "[Medida_Nombre]"
            
            # Extraer nombres entre corchetes [...]
            refs = re.findall(r'\[([A-Za-z0-9_]+)\]', line)
            used.update(refs)
            
            # También buscar nombres después de operadores
            for op in ['Sum\\(', 'Min\\(', 'Max\\(', 'Count\\(', 'CountNonNull\\(', 'Avg\\(']:
                matches = re.findall(rf'{op}([A-Za-z0-9_\.]+)', line)
                for m in matches:
                    if '.' not in m:  # es una medida, no columna
                        used.add(m)
    
    return used

def find_measure_relationships(measures: Dict[str, Dict]) -> Dict[str, Set[str]]:
    """
    Construye grafo de relaciones entre medidas.
    Retorna un dict donde key=medida y value=set de medidas que la referencian.
    """
    relationships = defaultdict(set)
    
    for name, measure_info in measures.items():
        refs = extract_referenced_measures(measure_info["full_expression"])
        for ref in refs:
            if ref in measures:  # Solo si es una medida del modelo
                relationships[ref].add(name)
    
    return relationships

def classify_measures(measures: Dict[str, Dict], used_measures: Set[str], duplicates: Dict[str, List[str]]) -> Dict:
    """Clasifica medidas en categorías."""
    
    classification = {
        "ACTIVAS": [],
        "HUÉRFANAS": [],
        "DUPLICADAS": [],
        "QUEBRADAS": [],
        "OBSOLETAS": [],
    }
    
    # Construir grafo de relaciones
    measure_relationships = find_measure_relationships(measures)
    
    # Medidas que son referenciadas por otras
    referenced_by_others = set(measure_relationships.keys())
    
    # Medidas que completan pares VAL
    paired_measures = set()
    for name in measures.keys():
        if name.endswith("_VAL"):
            base_name = name[:-4]
            if base_name in measures:
                paired_measures.add(base_name)
                paired_measures.add(name)
    
    for name, measure_info in measures.items():
        # VAL measures son supporting measures
        if measure_info["is_val_measure"]:
            continue
        
        errors = check_dax_errors(measure_info["full_expression"])
        is_obsol = is_obsolete(name)
        
        # Determinar si es activa
        is_active = (
            name in used_measures or           # Usado directamente en visual
            name in referenced_by_others or     # Referenciado por otra medida
            name in paired_measures or          # Tiene su VAL pair
            name.startswith("Lista_") or        # Listas de soporte
            name.startswith("Eje_") or          # Ejes
            measure_info["display_folder"]      # Tiene carpeta asignada
        )
        
        # Clasificar
        if is_obsol:
            classification["OBSOLETAS"].append({
                "nombre": name,
                "carpeta": measure_info["display_folder"],
                "categoría": measure_info["category"],
                "patrón_obsoleto": "Detectado en nombre",
            })
        elif errors:
            classification["QUEBRADAS"].append({
                "nombre": name,
                "carpeta": measure_info["display_folder"],
                "categoría": measure_info["category"],
                "errores": errors,
            })
        elif is_active:
            use_types = []
            if name in used_measures:
                use_types.append("Visual directo")
            if name in referenced_by_others:
                use_types.append("Referenciada por otra")
            if name in paired_measures:
                use_types.append("Componente de par VAL")
            
            classification["ACTIVAS"].append({
                "nombre": name,
                "carpeta": measure_info["display_folder"],
                "categoría": measure_info["category"],
                "uso": " / ".join(use_types) if use_types else "Función auxiliar",
            })
        else:
            classification["HUÉRFANAS"].append({
                "nombre": name,
                "carpeta": measure_info["display_folder"],
                "categoría": measure_info["category"],
            })
    
    # Medidas duplicadas (mismos nombres raíz pero versiones múltiples)
    for root, names in duplicates.items():
        if len(names) > 1:
            # Filtrar VAL measures
            non_val = [n for n in names if not n.endswith("_VAL")]
            if len(non_val) > 1:
                for name in non_val:
                    if name in measures:
                        classification["DUPLICADAS"].append({
                            "nombre": name,
                            "carpeta": measures[name]["display_folder"],
                            "categoría": measures[name]["category"],
                            "grupo_duplicado": non_val,
                        })
    
    # Remover duplicados en DUPLICADAS
    seen = set()
    unique_dups = []
    for item in classification["DUPLICADAS"]:
        key = item["nombre"]
        if key not in seen:
            unique_dups.append(item)
            seen.add(key)
    classification["DUPLICADAS"] = unique_dups
    
    return classification

def generate_summary(measures: Dict[str, Dict], classification: Dict) -> Dict:
    """Genera resumen ejecutivo."""
    
    total = len([m for m in measures.values() if not m["is_val_measure"]])
    
    return {
        "fecha_auditoria": str(Path(__file__).stat().st_mtime),
        "total_medidas": total,
        "medidas_vales_support": len([m for m in measures.values() if m["is_val_measure"]]),
        "resumen": {
            "activas": len(classification["ACTIVAS"]),
            "huérfanas": len(classification["HUÉRFANAS"]),
            "duplicadas": len(set(m["nombre"] for m in classification["DUPLICADAS"])),
            "quebradas": len(classification["QUEBRADAS"]),
            "obsoletas": len(classification["OBSOLETAS"]),
        },
        "porcentajes": {
            "utilizadas": f"{len(classification['ACTIVAS']) * 100 / total:.1f}%",
            "huérfanas": f"{len(classification['HUÉRFANAS']) * 100 / total:.1f}%",
            "problema": f"{(len(classification['QUEBRADAS']) + len(classification['OBSOLETAS'])) * 100 / total:.1f}%",
        }
    }

def main():
    print("[*] Leyendo medidas del modelo TMDL...")
    measures = parse_measures()
    print(f"[✓] {len(measures)} medidas encontradas")
    
    print("[*] Extrayendo medidas usadas en visuales...")
    used_measures = extract_visual_measures(VISUALES_CSV)
    print(f"[✓] {len(used_measures)} medidas referenciadas en visuales")
    
    print("[*] Detectando duplicados...")
    duplicates = find_duplicates(measures)
    print(f"[✓] {len(duplicates)} grupos de posibles duplicados")
    
    print("[*] Clasificando medidas...")
    classification = classify_measures(measures, used_measures, duplicates)
    
    print("[*] Generando resumen...")
    summary = generate_summary(measures, classification)
    
    # Compile final audit
    audit = {
        "metadata": {
            "modelo": "tableroDAGRD",
            "archivo_fuente": str(TMDL_FILE),
            "descripción": "Auditoría completa de medidas DAX - estado, uso, errores, duplicación",
        },
        "resumen_ejecutivo": summary,
        "clasificación": {
            "ACTIVAS": {
                "descripción": "Medidas que se usan en visuales o son referenciadas por otras medidas",
                "count": len(classification["ACTIVAS"]),
                "medidas": sorted(classification["ACTIVAS"], key=lambda x: x["nombre"]),
            },
            "HUÉRFANAS": {
                "descripción": "Medidas no usadas en ningún visual y no referenciadas por otras",
                "count": len(classification["HUÉRFANAS"]),
                "medidas": sorted(classification["HUÉRFANAS"], key=lambda x: x["nombre"]),
            },
            "DUPLICADAS": {
                "descripción": "Múltiples versiones de la misma medida (diferentes nombres para el mismo cálculo)",
                "count": len(set(m["nombre"] for m in classification["DUPLICADAS"])),
                "medidas": sorted(list({
                    m["nombre"]: m for m in classification["DUPLICADAS"]
                }.values()), key=lambda x: x["nombre"]),
            },
            "QUEBRADAS": {
                "descripción": "Medidas con errores potenciales en DAX",
                "count": len(classification["QUEBRADAS"]),
                "medidas": sorted(classification["QUEBRADAS"], key=lambda x: x["nombre"]),
            },
            "OBSOLETAS": {
                "descripción": "Medidas con patrones de nombre que sugieren ser antigua/descontinuada",
                "count": len(classification["OBSOLETAS"]),
                "medidas": sorted(classification["OBSOLETAS"], key=lambda x: x["nombre"]),
            },
        },
        "sugerencias_limpieza": generate_cleanup_suggestions(classification, measures),
    }
    
    # Write JSON
    with open(OUT_AUDIT, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    
    print(f"[✓] Auditoría guardada en: {OUT_AUDIT}")
    
    # Print resumen
    print("\n" + "="*70)
    print("RESUMEN DE AUDITORÍA")
    print("="*70)
    print(f"Total de medidas:       {summary['total_medidas']}")
    print(f"Medidas VAL (support):  {summary['medidas_vales_support']}")
    print()
    print(f"✓ ACTIVAS:              {summary['resumen']['activas']:3d}  ({summary['porcentajes']['utilizadas']})")
    print(f"✗ HUÉRFANAS:            {summary['resumen']['huérfanas']:3d}  ({summary['porcentajes']['huérfanas']})")
    print(f"⚠ DUPLICADAS:           {summary['resumen']['duplicadas']:3d}")
    print(f"✗ QUEBRADAS:            {summary['resumen']['quebradas']:3d}")
    print(f"✗ OBSOLETAS:            {summary['resumen']['obsoletas']:3d}")
    print()
    print(f"Problema total:         {summary['porcentajes']['problema']}")
    print("="*70)

def generate_cleanup_suggestions(classification: Dict, measures: Dict[str, Dict]) -> List[str]:
    """Genera sugerencias de limpieza basadas en la auditoría."""
    suggestions = []
    
    # Huérfanas
    if classification["HUÉRFANAS"]:
        suggestions.append(f"HUÉRFANAS ({len(classification['HUÉRFANAS'])}): Considerar eliminar medidas no usadas. Crear tabla con estas para validar antes de eliminar.")
    
    # Duplicadas
    if classification["DUPLICADAS"]:
        dup_names = set(m["nombre"] for m in classification["DUPLICADAS"])
        suggestions.append(f"DUPLICADAS ({len(dup_names)}): Consolidar medidas múltiples con el mismo propósito. Usar la más consistente y redirigir referencias.")
    
    # Quebradas
    if classification["QUEBRADAS"]:
        suggestions.append(f"QUEBRADAS ({len(classification['QUEBRADAS'])}): Revisar expresiones DAX. Posibles causas: CALCULATE vacío, paréntesis desbalanceados, DIVIDE sin alternativa.")
    
    # Obsoletas
    if classification["OBSOLETAS"]:
        suggestions.append(f"OBSOLETAS ({len(classification['OBSOLETAS'])}): Revisar historiquement y confirmar si aún se necesitan. Considerar renombrar o deprecar.")
    
    # Medidas VAL
    val_measures = [m for m in measures.values() if m["is_val_measure"]]
    suggestions.append(f"NOTA: {len(val_measures)} medidas '_VAL' (backing measures) encontradas. Estas son soporte para medidas formateadas y no deben ser borradas.")
    
    return suggestions

if __name__ == "__main__":
    main()
