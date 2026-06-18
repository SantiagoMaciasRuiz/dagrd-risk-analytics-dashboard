"""Genera medidas DAX SATC con nombres existentes en el modelo."""

from pathlib import Path


print("=" * 80)
print("GENERAR MEDIDAS SATC (NOMBRES EXISTENTES)")
print("=" * 80)

dax_script = """-- Medidas SATC con nombres existentes (compatibles con visuales ya creados)

-- Total SAT-C del catalogo vigente
Total_SATC_Unicos =
DISTINCTCOUNT(Dim_SATC[SATC_Nombre])

-- Total SAT-C en actividades comunitarias
SATC_Principales =
CALCULATE(
  DISTINCTCOUNT(Hecho_Participacion_General[nombre_satc]),
  Hecho_Participacion_General[bloque_comunidad] = "SAT-C"
)

Actividades_por_SATC =
CALCULATE(
  COALESCE(COUNTROWS(Hecho_Participacion_General), 0),
  Hecho_Participacion_General[bloque_comunidad] = "SAT-C"
)

Participantes_por_SATC =
CALCULATE(
  COALESCE(SUM(Hecho_Participacion_General[participantes]), 0),
  Hecho_Participacion_General[bloque_comunidad] = "SAT-C"
)

-- Cobertura entre actividades SAT-C y catalogo vigente
Cobertura_SATC_Porcentaje =
DIVIDE(
  [SATC_Principales],
  [Total_SATC_Unicos],
  0
)
"""

instrucciones = """PASO 1: Refrescar datos
1. Ejecuta actualizar_37_satc_final.py
2. Ejecuta regenerar_puente_37.py
3. En Power BI, da Actualizar (Refresh)

PASO 2: Mantener nombres de medidas existentes
1. Total_SATC_Unicos
2. SATC_Principales
3. Actividades_por_SATC
4. Participantes_por_SATC
5. Cobertura_SATC_Porcentaje

PASO 3: Validar resultados esperados
1. Total_SATC_Unicos: 40
2. SATC_Principales: 33
3. Actividades_por_SATC: 200

NOTA
- La fuente vigente es la hoja SAT-C del archivo Reporte de actividades equipo social 2026.xlsx.
"""

dax_file = Path("medidas_satc.dax")
dax_file.write_text(dax_script, encoding="utf-8")

instrucciones_file = Path("instrucciones_crear_medidas_satc.txt")
instrucciones_file.write_text(instrucciones, encoding="utf-8")

print("\nMedidas incluidas:")
for nombre in [
  "Total_SATC_Unicos",
  "SATC_Principales",
  "Actividades_por_SATC",
  "Participantes_por_SATC",
  "Cobertura_SATC_Porcentaje",
]:
  print(f"- {nombre}")

print(f"\nArchivo DAX actualizado: {dax_file}")
print(f"Instrucciones actualizadas: {instrucciones_file}")
print("=" * 80)
