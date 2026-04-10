# Plan 4 Agentes - Validacion y Migracion 2026-03-20

## Alcance ejecutado
Se ejecuto trabajo paralelo con 4 agentes sobre:
1. Plantilla de auditoria Excel.
2. Validacion automatica de pagina Estrategia.
3. Validacion consolidada de todas las paginas.
4. Plan de migracion de visuales a medidas DAX.

## Entregables creados
- data/reference/plantilla_auditoria_visuales_2026.csv
- scripts/qa/validar_estrategia_2026.py
- scripts/qa/resumen_validacion_todas_paginas_2026.py

## Hallazgos integrados
- En layout hay 189 visuales.
- El uso predominante es de agregaciones directas sobre columnas (ejemplo: Sum(Sheet1....), Min(Sheet1....)).
- Las medidas DAX existen en el modelo (80), pero en el layout actual no son la referencia principal.
- Cobertura de validacion automatica esperada: aprox. 60-70% (cards con SUM/MIN/COUNT).

## Opcion 1 - Plantilla auditoria
Se creo la plantilla base CSV con columnas para:
- identificacion de visual
- query y filtros
- valor power bi
- valor excel
- diferencia y porcentaje de variacion
- estado, notas y trazabilidad de auditor

## Opcion 2 - Estrategia automatizada
Script: scripts/qa/validar_estrategia_2026.py
- Filtra pagina Estrategia
- Toma cards con SUM/MIN/COUNT
- Calcula valor sobre Sheet1 aplicando filtros cuando existen
- Marca casos no auditables (consultas con Base completa para PBI)
- Exporta resultados:
  - data/reference/validacion_estrategia_resultados_2026.csv
  - data/reference/validacion_estrategia_resumen_2026.json

## Opcion 3 - Todas las paginas
Script: scripts/qa/resumen_validacion_todas_paginas_2026.py
- Resume total visuales por pagina
- Calcula auditables automaticos y cobertura por pagina
- Genera top 20 para auditoria manual
- Exporta resultados:
  - data/reference/resumen_validacion_todas_paginas_2026.csv
  - data/reference/resumen_validacion_todas_paginas_2026.json

## Opcion 4 - Migracion a medidas DAX
Linea base recomendada:
- Quick wins: reemplazar patrones Sum(Sheet1.participantes) por medidas base ya existentes cuando aplique contexto.
- Riesgo alto: visuales con Min(...Instancia) usados como etiqueta y visuales que dependen de Base completa para PBI.Personalizado.1.
- Crear medidas de etiqueta/control antes de migrar visual por visual.

## Orden recomendado de ejecucion
1. Ejecutar validacion Estrategia y corregir filtros/columnas no trazables.
2. Ejecutar resumen total para priorizar visuales de alto impacto.
3. Definir lote de quick wins para migracion DAX (10-20 visuales primero).
4. Validar paridad de valores antes de cada despliegue.
