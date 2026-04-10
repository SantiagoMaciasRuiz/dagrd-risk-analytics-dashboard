# Análisis de Estructura - Modelo Semántico tableroDAGRD
**Fecha:** 9 de abril de 2026  
**Versión:** tmdl_live  
**Fuente:** Análisis de archivos TMDL  

---

## 📊 Resumen Ejecutivo

El modelo **tableroDAGRD** es un modelo tabular bien estructurado de Power BI con **19 tablas activas** (+ 2 sin usar) que implementa una arquitectura **star schema modificado**. El modelo integra participación comunitaria, datos demográficos, simulacros de emergencia y control de activos móviles (CAM).

| Métrica | Valor |
|---------|-------|
| **Total Tablas** | 21 |
| **Tablas de Hechos** | 3 |
| **Tablas Dimensionales** | 8 |
| **Tablas de Control** | 3 |
| **Tabla de Medidas** | 1 |
| **Tablas de Sistema** | 4 |
| **Total Medidas** | 40 |
| **Relaciones Activas** | 13 |
| **Relaciones Inactivas** | 1 |

---

## 🏈 Arquitectura de Datos

### Patrón Dominante: Star Schema Modificado
```
                    Dim_Fecha ◇←─────┐
                                     │
                    Dim_Seccion ◇←───┼─┐
                                     │ │
┌─────────────────────────────────┐  │ │
│  Hecho_Participacion_General    │──┼─┼──→ Dim_Instancia ◇
│  (id_actividad, participantes)  │  │ │
└─────────────────────────────────┘  │ │
                                     ├─┘
┌─────────────────────────────────┐  │
│  Hecho_Simulacros               │──┼──────→ Dim_Comuna ◇
│  (fila_origen, personas)        │  │           │
└─────────────────────────────────┘  │         [HUB]
                                     │
┌─────────────────────────────────┐  │    Dim_SATC_Relaciones ◇
│  Hecho_Demografia               │──┘    (Comuna_Cod, SATC_Qty)
│  (id_actividad, valores demo)   │         │ │ │ │
└─────────────────────────────────┘         └─┼─┼─┼─→ Dim_SATC
                                              │ │ │
                                              │ │ └──→ Dim_Semilleros
                                              │ └─────→ Dim_Semilleros_Confiable  
                                              └────────→ Dim_SATC (back-relation)

[Aisladas - Sin relaciones]
CAM_Control ○
CAM_Resumen_Zona ○
CAM_Detalle ○
Dim_Comites_Comisiones_2026 ○
```

### Tablas Principales

#### 🔴 **TABLAS DE HECHOS (Fact Tables)**

**1. Hecho_Participacion_General** [CENTRAL]
- **Registros:** 3.202 actividades
- **Medida Principal:** `participantes` (111.694 participaciones)
- **Propósito:** Núcleo del modelo; todas las actividades comunitarias, educativas, empresariales e institucionales
- **Características:**
  - Múltiples públicos: comunitaria, primera infancia, empresarial
  - Múltiples actividades: semilleros, comunitaria, institucional
  - Datos de impacto: impacto_indirecto
- **Relaciones:** ✅ 4 dimensiones (Fecha, Comuna, Seccion, Instancia) + Hub

**2. Hecho_Simulacros** [SECUNDARIO]
- **Registros:** Simulacros de emergencia
- **Medida:** `personas_participantes` (suma)
- **Propósito:** Entrenamientos y simulacros de atención de emergencias
- **Características:**
  - Vinculada a entidades ejecutoras (`nombre_entidad`)
  - Contiene nombre de comuna en texto (`comuna_texto`)
- **Relaciones:** ✅ 4 dimensiones (Fecha, Comuna, Seccion) + Hub
- **⚠️ Issue:** Relación inactiva bidireccional con Hecho_Participacion_General por `fila_origen`

**3. Hecho_Demografia** [COMPLEMENTARIO]
- **Registros:** Análisis demográfico por actividad
- **Propósito:** Profundización en características demográficas de participantes
- **Características:**
  - Seguimiento detallado por instancia y sección
- **Relaciones:** ✅ 4 dimensiones (Fecha, Comuna, Seccion, Instancia) + Hub

---

#### 🟢 **TABLAS DIMENSIONALES (Core)**

| Tabla | Tipo | Fuente | Registros | Propósito |
|-------|------|--------|-----------|----------|
| **Dim_Fecha** | Calculada (DAX) | UNION + CALENDAR | ~400+ | Calendario dinámico de fechas |
| **Dim_Comuna** | Calculada (DAX) | DISTINCT + SWITCH | 16 | Códigos→Nombres de comunas |
| **Dim_Seccion** | Calculada (DATATABLE) | Literal | 5 | Categorías: Comunitaria, Educativa, Empresarial, Institucional, Otros |
| **Dim_Instancia** | Calculada (DISTINCT) | Query | ? | Instancias/Canales de participación |
| **Dim_SATC** | Importada (Excel) | M Query | ? | Sociedades Acción Territorial |
| **Dim_SATC_Relaciones** | Importada (Excel) | M Query | ~16 | **[HUB]** Mapeo Comuna↔SATC cantidad |
| **Dim_Semilleros** | Importada (Excel) | M Query | ? | Semilleros comunitarios (v1) |
| **Dim_Semilleros_Confiable** | Importada (Excel) | M Query | ? | Semilleros validados (v2) + fuente+estado |
| **Dim_Comites_Comisiones_2026** | Importada (CSV) | M Query | ? | Comités y Comisiones por comuna |

**🤔 Observación CRÍTICA:**
- **Dim_Fecha es CALCULADA** → Se regenera cada vez que se refresca; rango dinámico (seguro)
- **Dim_Comuna es CALCULADA** → Aislada pero consistente
- **Dim_Seccion es HARDCODED** → 5 valores fijos (estructura muy estable)
- **Dim_SATC_Relaciones es el HUB** → Conecta 5 diferentes tablas/relaciones

---

#### 🟡 **TABLAS DE CONTROL Y ACTIVOS MÓVILES**

| Tabla | Registros | Columnas | Relaciones | Estado |
|-------|-----------|----------|-----------|--------|
| **CAM_Control** | 1 (agregada) | cam_activos_total, zonas_cam_total, empresas_unicas_global/suma_por_zona | ❌ Ninguna | 🔴 AISLADA |
| **CAM_Resumen_Zona** | ~5-10 | cam_activo_id, zona_cam, empresas_unicas_zona | ❌ Ninguna | 🔴 AISLADA |
| **CAM_Detalle** | ~50-100 | cam_activo_id, zona_cam, empresa, empresa_normalizada | ❌ Ninguna | 🔴 AISLADA |

**⚠️ ISSUE:** Las tablas CAM son independientes del modelo principal. Probablemente son tablas auxiliares para reportes específicos.

---

#### 🔵 **TABLA DE MEDIDAS**

**_Medidas** [Tabla de Rol para KPIs]

Contiene **40 medidas** organizadas en:

**Categorías:**
1. **Generales (Generales factoriales)**
   - GenF_Total_Actividades (3.202)
   - GenF_Total_Participaciones (111.694)
   - GenF_*_Participaciones (por sección: Comunitaria, Educativa, Empresarial, Institucional)

2. **SATC & Semilleros**
   - Num_SATC, Total_SATC_Unicos (desde Dim_SATC)
   - Num_Semilleros, Total_Semilleros (desde Dim_Semilleros)

3. **Simulacros**
   - Base_Simulacros, Base_Simulacros_Personas
   - Simulacros_Registrados_Total

4. **Cobertura**
   - Base_Impacto_Indirecto
   - Cobertura_Total (participantes + impacto indirecto)

5. **Institucional (Detallado)**
   - Participaciones_Institucionales
   - Articulacion_Institucional
   - Mesas_Interinstitucionalidad
   - Acciones_Conjuntas
   - Participantes_Articulacion, Participantes_Mesas, Participantes_Acciones_Conjuntas

6. **Control de Calidad**
   - Ctl_Referencia_Actividades_OK (esperado: 3202 = SI)
   - Ctl_Referencia_Participaciones_OK (esperado: 111694 = SI)

**Patrón de Nomenclatura:**
```
[Nombre] = IF(ISBLANK([Nombre_VAL]), "N/A", FORMAT([Nombre_VAL], "#,##0"))
[Nombre_VAL] = SUM/COUNT/CALCULATE(...)  [isHidden]
```
Esto permite valores formateados visibles en reportes + valores calculables para fórmulas.

---

#### ⚪ **TABLAS DE SISTEMA (Fecha - AutoGenerated)**

Power BI genera automáticamente **4 tablas de fecha**:
1. **DateTableTemplate_cf3939a4-f1ee-4021-bad3-46d914bea584** (oculta, plantilla sistema)
2. **LocalDateTable_8db77276-1d8a-4c80-9ec7-937e69de8c4f** (Hecho_Participacion_General)
3. **LocalDateTable_15b2182d-b46e-4161-8338-943189c4acc8** (Hecho_Simulacros)
4. **LocalDateTable_fdd25ae3-1e7e-47ce-8a87-6344f31146ec** (Hecho_Demografia)

**⚠️ REDUNDANCIA DETECTADA:** 4 tablas de fecha cuando existe Dim_Fecha calculada. Las LocalDateTables se usan en variation relationships, pero esto genera complejidad innecesaria.

---

## 🔗 Matriz de Relaciones

### Relaciones Nombradas (Explícitas)
```
R_DimFecha_HPG      → Hecho_Participacion_General.fecha_date     → Dim_Fecha.fecha
R_DimFecha_HD       → Hecho_Demografia.fecha_date                → Dim_Fecha.fecha
R_DimFecha_HS       → Hecho_Simulacros.fecha_date                → Dim_Fecha.fecha

R_DimComuna_HPG     → Hecho_Participacion_General.comuna_cod     → Dim_Comuna.comuna_cod
R_DimComuna_HD      → Hecho_Demografia.comuna_cod                → Dim_Comuna.comuna_cod
R_DimComuna_HS      → Hecho_Simulacros.comuna_cod                → Dim_Comuna.comuna_cod

R_DimSeccion_HPG    → Hecho_Participacion_General.seccion_tablero → Dim_Seccion.seccion_tablero
R_DimSeccion_HD     → Hecho_Demografia.seccion_tablero           → Dim_Seccion.seccion_tablero
R_DimSeccion_HS     → Hecho_Simulacros.sector_tablero            → Dim_Seccion.seccion_tablero

R_DimInstancia_HPG  → Hecho_Participacion_General.instancia       → Dim_Instancia.instancia
R_DimInstancia_HD   → Hecho_Demografia.instancia                 → Dim_Instancia.instancia
```

### Relaciones AutoDetected (Implícitas por PBI)
```
AutoDetected_f58f1728-78ac-4a8b-a8d0-16fb2fafac8b
  → Hecho_Participacion_General.comuna_cod → Dim_SATC_Relaciones.Comuna_Cod

AutoDetected_503d9cf3-c4c4-4ad8-82ae-92e3b6dc08cd
  → Hecho_Simulacros.comuna_cod → Dim_SATC_Relaciones.Comuna_Cod

AutoDetected_b2ccf614-34b3-4ee2-b6c1-7f2e4238f528
  → Hecho_Demografia.comuna_cod → Dim_SATC_Relaciones.Comuna_Cod

AutoDetected_689423ad-2f28-4f2a-b16b-e8d205bed9b7
  → Dim_Semilleros_Confiable.comuna_cod → Dim_SATC_Relaciones.Comuna_Cod

AutoDetected_edec8387-6468-4a92-80ba-4418def7f14d
  → Dim_SATC.Comuna_Cod → Dim_SATC_Relaciones.Comuna_Cod
```

### Relación Inactiva
```
d0c01280-ea33-e563-9f9e-1d1483561b6a [INACTIVE - both directions]
  ← Hecho_Simulacros.fila_origen (many)
  ← Hecho_Participacion_General.fila_origen (one)
  Motivo probable: Cruzar dos hechos directamente es anti-pattern OLAP
```

---

## 🎯 Patrones Observados

### 1. Convenciones de Nombre

**Prefijos:**
- `Dim_` → Dimensiones (8 tablas)
- `Hecho_` → Tablas de hechos (3 tablas)
- `CAM_` → Control de Activos Móviles (3 tablas)
- `_` → Tabla especial (_Medidas)

**Sufijos en Medidas:**
- `_VAL` → Medida de valor base (oculta, sin formato)
- (sin sufijo) → Medida formateada para visualización

**Casos:**
- **Tablas:** PascalCase (ej: `Hecho_Participacion_General`)
- **Columnas:** snake_case (ej: `commune_cod`, `actividad_semillero`)

### 2. Tipos de Particiones

**Dinámicas (Calculadas - DAX):**
```
Dim_Fecha          → UNION(SELECTCOLUMNS...) → CALENDAR(MinFecha, MaxFecha)
Dim_Comuna         → DISTINCT(UNION...) + SWITCH para nombres
Dim_Seccion        → DATATABLE literal con 5 valores
Dim_Instancia      → DISTINCT(SELECTCOLUMNS...)
```
✅ **Ventaja:** Se recalculan automáticamente; rango dinámico; consistencia garantizada

**Importadas desde Excel (M Language):**
```
Dim_SATC, Dim_SATC_Relaciones, Dim_Semilleros, Dim_Semilleros_Confiable
CAM_Control, CAM_Resumen_Zona, CAM_Detalle
```
📂 **Fuente:** `Modelo_Reporte_Paginas_2026.xlsx`

**Importadas desde CSV (M Language):**
```
Dim_Comites_Comisiones_2026 ← CSV local
```

### 3. Estructura de Hechos

Cada tabla de hechos contiene:
- **1 PK (surrogate)**: `id_actividad` o `fila_origen`
- **Fechas**: `fecha` (dateTime, oculta) + derivadas (`anio`, `mes_num`, `mes_nombre`)
- **FKs de dimensión**: `comuna_cod`, `instancia`, `seccion_tablero`
- **Atributos descriptivos**: múltiples columnas de actividades/públicos
- **Medidas**: `participantes`, `personas_participantes`, `impacto_indirecto`

---

## 🚨 Problemas Identificados

### 🔴 **CRÍTICOS**
Ninguno detectado que impida funcionamiento.

### 🟠 **ALTOS (Recomendación: Resolver)**

**1. Relación Inactiva Entre Hechos**
- **Relación:** `Hecho_Simulacros.fila_origen ← → Hecho_Participacion_General.fila_origen`
- **Estado:** Inactiva, bidireccional
- **Problema:** Cruzar dos hechos directamente es anti-pattern en OLAP
- **Acción:** ¿Se necesita? Si no, eliminar; si sí, documentar razón y evaluar si debe ser unidireccional

**2. Cuatro Tablas de Fecha (Redundancia)**
- Dim_Fecha (calculada, central) + 3 LocalDateTables (autogeneradas)
- **Problema:** Confusión; potencial doble cálculo
- **Acción:** Limpiar tablas de fecha no usadas o consolidar

**3. Dim_Semilleros vs Dim_Semilleros_Confiable**
- Dos versiones de la misma dimensión
- **Problema:** Cuál es la oficial? Se duplican datos en reportes?
- **Acción:** Audit; deprecar una versión

### 🟡 **MEDIOS (Recomendación: Mejorar)**

**4. CAM_* Tablas Aisladas (Sin Relaciones)**
- CAM_Control, CAM_Resumen_Zona, CAM_Detalle no conectan con el modelo
- **Problema:** ¿Son auxiliares? ¿Se usan en reportes? Genera confusión
- **Acción:** Documentar propósito; considerar mover a modelo separado si no se usan

**5. Dim_SATC_Relaciones con Annotation "Exception"**
- Columna `PBI_ResultType = Exception` (debería ser `Table`)
- **Problema:** Podría causar comportamiento inesperado en exploradores
- **Acción:** Verificar y corregir annotation

**6. Tablas Maestras Desde Excel (Sin Versionado)**
- Dim_SATC, Dim_Semilleros, CAM_* cargan de `Modelo_Reporte_Paginas_2026.xlsx`
- **Problema:** ¿Quién mantiene el Excel? ¿Control de versión?
- **Acción:** Documentar SOP; considerar migrar a SQL Server para datos maestros

---

## 📈 Fortalezas del Modelo

✅ **Arquitectura sólida:** Star schema bien definido  
✅ **Separación clara:** Hechos vs Dimensiones explícitos  
✅ **Naming consistente:** Convenciones claras y aplicadas uniformemente  
✅ **Relaciones explícitas:** La mayoría son nombradas (fácil mantener)  
✅ **Medidas centralizadas:** Tabla `_Medidas` facilita mantenimiento  
✅ **Dinámicas inteligentes:** Dimensiones calculadas garantizan consistencia  
✅ **Control de calidad:** Medidas de validación (Ctl_Referencia_*)

---

## 🔧 Sugerencias de Reorganización

### Corto Plazo (Crítica)
1. **Limpiar tablas de fecha:**
   - Verificar si LocalDateTables se usan en relaciones
   - Si no, eliminar (mantener solo Dim_Fecha)

2. **Resolver relación inactiva:**
   - Investigar lógica de `Hecho_Simulacros ← → Hecho_Participacion_General`
   - Si no se necesita, eliminar

3. **Consolidar Semilleros:**
   - Decidir: ¿Dim_Semilleros o Dim_Semilleros_Confiable?
   - Deprecar una, migrar referencias

### Mediano Plazo
4. **Documentar CAM_* tablas:**
   - Cuál es su propósito?
   - Qué reportes las usan?
   - ¿Podrían conectarse al modelo si fuera necesario?

5. **Crear carpetas de medidas:**
   - Agrupar en DisplayFolders por categoría
   - Facilita navegación en Power BI UI

6. **Audit de fuentes de datos:**
   - Identificar propietarios de Dim_SATC, Dim_Semilleros, CAM_*
   - Documentar SOP de actualización

### Largo Plazo
7. **Migración de datos maestros:**
   - Mover Dim_SATC, Dim_Semilleros a SQL Server (o similar)
   - Eliminar dependencia de Excel

8. **Modelo de seguridad RLS:**
   - ¿Se necesita filtrado por Comuna en reportes?
   - Crear medidas y roles si aplica

9. **Documentación de lineage:**
   - ETL → Fuentes Excel/CSV → Modelo TMDL → Power BI Desktop → Reportes
   - Documentar transformaciones clave

---

## 📋 Checklist de Validación

- [ ] ¿Hecho_Participacion_General = 3.202 registros?
- [ ] ¿GenF_Total_Participaciones = 111.694?
- [ ] ¿Ctl_Referencia_Actividades_OK = SI?
- [ ] ¿Ctl_Referencia_Participaciones_OK = SI?
- [ ] ¿Relación inactiva es necesaria?
- [ ] ¿LocalDateTables se usan activamente?
- [ ] ¿CAM_* tablas se usan en algún reporte?
- [ ] ¿Dim_Semilleros_Confiable es más actualizada?
- [ ] ¿Fuentes de Excel están bajo control de versión?

---

## 📊 JSON Schema Complementario

Ver archivo: `ANALISIS_MODELO_SEMANTICO_2026-04-09.json`

Contiene estructura completa en formato máquina-legible:
- Definición detallada de cada tabla
- Todas las columnas con tipos de datos
- Matriz de relaciones
- Patrones de nombramiento
- Diagnostico completo
- Recomendaciones priorizadas

---

**Análisis completado por:** Sistema de Análisis Automático  
**Fecha:** 9 de abril de 2026  
**Datos fuente:** tmdl_live (TMDL format - Version control friendly)
