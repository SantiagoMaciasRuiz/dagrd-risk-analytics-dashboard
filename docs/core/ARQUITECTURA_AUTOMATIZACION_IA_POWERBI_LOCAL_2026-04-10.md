# Arquitectura de Automatizacion Inteligente Local para Power BI Desktop

**Fecha:** 10 de abril de 2026  
**Estado:** Automatizacion local consolidada en `scripts/powerbi` y `scripts/etl`; la app de chat fue retirada del repo.

## 1. Memoria de proyecto consolidada (contexto historico)

## 1.1 Objetivo general del proyecto

Construir y mantener un tablero Power BI DAGRD con ETL en Python, modelo semantico estable y validaciones cruzadas Excel vs Power BI, priorizando consistencia de KPI y automatizacion operativa.

## 1.2 Estado actual real (evidencia repo)

- ETL productivo consolidado en `scripts/etl/extraer_consultas_paginas_reporte.py` y derivados.
- Modelo semantico vivo en TMDL (`powerbi/tmdl_live`) con tabla `_Medidas` y alta cobertura de medidas activas (97.8%).
- Scripts operativos de Power BI ya existentes en `scripts/powerbi` (incluye automatizacion con TOM/XMLA via PowerShell).
- Documentacion de arquitectura de datos y auditoria actualizada al 2026-04-09.
- No existia frontend web de chat en el repositorio.

## 1.3 Componentes existentes reutilizables

- ETL y normalizacion de datos por bloques/secciones.
- Scripts de aplicacion de medidas y gobierno de modelo en Power BI Desktop.
- Configuracion DAX y artefactos TMDL para auditoria y evolucion.
- Evidencia de trabajo paralelo por agentes para validacion/migracion.

## 1.4 Pendientes detectados

- Crear control conversacional centralizado (chat + orquestador + trazabilidad).
- Estandarizar tool calling con guardrails.
- Reducir reprocesamiento/token con cache local.
- Integrar mejor contexto historico del proyecto en cada decision automatizada.

## 2. Arquitectura propuesta e implementada

```mermaid
flowchart LR
    U[Usuario Web] --> F[Frontend Chat HTML CSS JS]
    F --> B[Backend FastAPI Local]
    B --> M[(SQLite Memoria + Cache)]
    B --> O[Ollama Local]
    B --> A[Orquestador de Agentes]
    A --> T[Tool Registry Whitelist]
    T --> P1[scripts/powerbi/*.ps1|*.py]
    T --> P2[scripts/etl/*.py]
    T --> C[Lectura de contexto docs/core]
    P1 --> PB[Power BI Desktop XMLA/TOM]
```

## 2.1 Frontend

- Stack: HTML + CSS + JS vanilla.
- Vista tipo chat + panel de acciones ejecutadas.
- Conversacion persistida por `conversation_id`.

## 2.2 Backend

- Stack: Python + FastAPI + HTTPX + Pydantic.
- Responsabilidades:
  - Exponer API de chat y salud.
  - Gestionar memoria persistente y cache.
  - Orquestar razonamiento con modelo local.
  - Ejecutar herramientas seguras en whitelist.

## 2.3 Modelo IA local

- Motor: Ollama local (`http://127.0.0.1:11434`).
- Modelo por defecto: `llama3.1:8b` (configurable por request).
- Modo de bajo costo token:
  - Prompt de sistema corto y estructurado.
  - Respuesta JSON obligatoria para reducir ambiguedad.
  - Cache por hash de consulta.

## 2.4 Sistema de agentes

- Agente orquestador (implementado): interpreta intencion, decide herramientas y consolida respuesta final.
- Agente Power BI (via tools): ejecuta scripts Power BI existentes.
- Agente Datos (via tools): ejecuta scripts ETL existentes.

Nota: En esta primera version, los agentes especializados se implementan como herramientas de ejecucion controlada. Se puede evolucionar a sub-agentes dedicados sin romper API.

## 2.5 Tool calling implementado

Herramientas disponibles:

1. `list_powerbi_scripts`
2. `run_powerbi_script`
3. `run_etl_script`
4. `read_project_context`

Guardrails:

- Solo scripts de `scripts/powerbi` y `scripts/etl` (nombre exacto).
- Sin ejecucion arbitraria de comandos de sistema.
- Timeout, captura de stderr/stdout y log persistente.

## 3. Como conectar IA local con acciones reales en Power BI

## 3.1 Ruta principal

1. Usuario pide accion en chat (ej: "aplica medidas educativas").
2. Orquestador consulta herramientas permitidas.
3. Ejecuta `run_powerbi_script` con script existente, por ejemplo:
   - `aplicar_medidas_educacion_instituciones.ps1`
4. Script se conecta a `localhost:<port>` del modelo tabular de Power BI Desktop (XMLA/TOM).
5. Resultado (ok/error + salida) se registra en memoria y se muestra en UI.

## 3.2 Beneficio clave

Se reutiliza tu automatizacion ya probada (PowerShell + TOM + scripts ETL) en vez de crear conectores nuevos de alto riesgo.

## 4. Flujo completo de ejemplo (usuario -> IA -> accion real)

1. Usuario: "Lista scripts de Power BI y ejecuta aplicar_medidas_educacion_instituciones.ps1".
2. IA (orquestador):
   - tool_call 1: `list_powerbi_scripts`
   - tool_call 2: `run_powerbi_script` con `script_name=aplicar_medidas_educacion_instituciones.ps1`
3. Tool registry valida whitelist y ejecuta PowerShell.
4. Power BI Desktop recibe cambios del script sobre el modelo tabular.
5. IA responde con resultado resumido y log de salida.
6. Queda evidencia en SQLite para auditoria.

## 5. Estructura de carpetas actual

```text
scripts/
  powerbi/
  etl/
data/
  reference/
    autobuild/
  nuget/
docs/
  core/
```

## 6. Escalabilidad y rendimiento (proximas mejoras)

1. Separar cache por tipo de consulta:
- cache de respuesta conversacional
- cache de metadata de scripts
- cache de contexto documental resumido

2. Implementar RAG local sobre docs/tmdl:
- embeddings locales + indice vectorial ligero
- retrieval por seccion/medida/tabla

3. Orquestacion por colas:
- tareas largas ETL/Power BI en worker asincorno
- UI con estado `queued/running/succeeded/failed`

4. Politica de memoria por ventana:
- resumen automatico de conversaciones largas
- recorte de historial irrelevante para bajar tokens

5. Seguridad operativa:
- control por perfiles de herramientas
- confirmacion humana para acciones destructivas
- bitacora de aprobaciones

## 7. Decision de stack (justificacion)

Se selecciona Python por coherencia con tu base actual:

- ETL ya construido en Python.
- Scripts y conocimiento operativo existentes en el equipo.
- Integracion natural con FastAPI y llamadas a scripts Power BI/PowerShell.

Resultado: menor friccion, menor costo de integracion y mayor velocidad de adopcion.
