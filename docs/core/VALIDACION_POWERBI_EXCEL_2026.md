# Validacion Power BI vs Excel 2026

Fuente principal: data/source/Reporte de actividades equipo social 2026 (1).xlsx

## Archivos generados
- data/reference/powerbi_medidas_mapeo_2026.csv
- data/reference/powerbi_consultas_visuales_2026.csv

Total medidas encontradas: 267
Total visuales encontradas en layout: 107

## Mapeo rapido modelo -> columna Excel
- participantes -> Sheet1 -> Indique el numero de personas participantes
- impacto_indirecto -> Sheet1 -> Cantidad de personas impactadas indirectamente
- seccion_tablero -> Sheet1 -> Instancia (clasificacion)
- bloque_comunidad -> Sheet1 -> Publico objeto en comunidad + campos comunidad (clasificacion)
- bloque_educacion -> Sheet1 -> Publico objeto en educacion + nivel educativo (clasificacion)
- bloque_empresarial -> Sheet1 -> Publico objeto en empresarial + COSEGRD (clasificacion)
- bloque_institucional -> Sheet1 -> Instancia/actividad institucional (clasificacion)
- comuna_cod -> Sheet1 -> Comuna/Corregimiento donde se desarrollo la actividad
- fecha -> Sheet1 -> Fecha actividad
- personas_participantes -> Simulacros -> columna de participantes
- sector_tablero -> Simulacros -> Sector pertenece

## Como validar una medida en Excel
1. Buscar medida en powerbi_medidas_mapeo_2026.csv.
2. Tomar columnas_modelo y filtros_dax.
3. Traducir columnas modelo al Excel usando el mapeo rapido.
4. Aplicar filtros exactos y calcular:
   - COUNTROWS: recuento de filas
   - SUM(columna): suma de columna numerica
   - DISTINCTCOUNT(columna): recuento unico

## Nota
- El layout tiene visuales con agregaciones directas sobre columnas (sin medida DAX).
- Los filtros de cada visual estan serializados en powerbi_consultas_visuales_2026.csv (filtros_visual).