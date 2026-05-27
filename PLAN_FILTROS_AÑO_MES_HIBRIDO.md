# 📋 PLAN DETALLADO: INTEGRACIÓN FILTROS AÑO/MES - MODELO tableroDAGRDCOPIA
**Fecha**: 26 de mayo de 2026  
**Modelo**: tableroDAGRDCOPIA  
**Opción**: Híbrida (Dimensión Temporal + Fórmulas DAX)

---

## 📊 ESTRUCTURA ACTUAL DE DATOS

### Archivos Fuente Principales
| Archivo | Ubicación | Registros | Columna Fecha Clave |
|---------|-----------|-----------|---------------------|
| **BD PERSONAS ATENDIDAS** | data/model/ | 4,703 | FECHA ATENCIÓN (01-01-2025 a 24-05-2026) |
| **Reporte de actividades 2026** | data/source/ | 3,202 | fecha_ini (variará según página) |
| **Hecho_Participacion_General** | Modelo Excel | 3,202 | fecha (en Modelo_Reporte_Paginas_2026.xlsx) |

### Tablas Dimensión Existentes
- `Dim_Comites_Comisiones_2026` (158 filas)
- `Dim_SATC` (38 filas)
- `Dim_Semilleros` (N filas)
- `Empresas_Detalle` (73 únicas)

### Tabla Hecho Principal
- `Hecho_Participacion_General` (3,202 filas)
  - Columnas: actividad_id, fecha, comuna_cod, participantes, mujeres, hombres, sector, etc.
  - **CRÍTICO**: columna `fecha` puede llegar como Int64 (serial Excel)

---

## 🎯 PLAN EJECUTIVO - ORDEN EXACTO

### FASE 1: PREPARACIÓN (Día 1 - 30 minutos)
**Objetivo**: Validar datos existentes y definir estructura

#### PASO 1.1: Validar Fuente de Fechas
```
Ubicación: c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\data\model\
Archivo: BD PERSONAS ATENDIDAS ORDINARIO 01-01-2025 A 24-05-2026.xlsx
Acción:
1. Abrir en Excel
2. Revisar columna "FECHA ATENCIÓN"
3. Verificar rango: mín=01-01-2025, máx=24-05-2026
4. Formatos: ¿Texto "YYYY-MM-DD"? ¿Formato datetime? ¿Serial?
5. Cuenta de fechas únicas esperada: ~520 días
```

**Salida esperada**: 
- ✅ Formato de fecha confirmado
- ✅ Rango de años: 2025, 2026
- ✅ Rango de meses: 1-12 (todos presentes)

---

#### PASO 1.2: Verificar Estructura Modelo_Reporte_Paginas_2026.xlsx
```
Ubicación: data/model/Modelo_Reporte_Paginas_2026.xlsx
Acción:
1. Abrir en Excel / Power BI
2. Revisar hoja "Hecho_Participacion_General"
3. Buscar columna "fecha" o similar
4. Tipo de dato: ¿Int64 (serial)? ¿Datetime? ¿Texto?
5. Valores muestrales: primeros 5 valores

Resultado esperado:
- Si Int64: necesita conversión DATE(1899,12,30) + [fecha]
- Si datetime: listo para relación directa
- Si texto: parse con DATE() en DAX o Power Query
```

**Salida esperada**:
- ✅ Tipo de dato identificado
- ✅ Conversión necesaria documentada

---

### FASE 2: CREAR DIMENSIÓN TEMPORAL (Día 2 - 1-2 horas)

#### PASO 2.1: Generar Dim_Fecha (Opción A: Python ETL)
```
Archivo a crear: scripts/etl/generar_dim_fecha.py

Script:
├── Entrada: BD PERSONAS ATENDIDAS... .xlsx
├── Extrae columna "FECHA ATENCIÓN"
├── Genera:
│   ├── fecha_date (formato YYYY-MM-DD)
│   ├── año (2025, 2026)
│   ├── mes (1-12)
│   ├── mes_nombre (Enero, Febrero, ... Diciembre)
│   ├── fecha_key (YYYYMMDD para join)
│   ├── trimestre (Q1, Q2, Q3, Q4)
│   ├── semana (1-53)
│   └── día_semana (Monday, Tuesday, ...)
│
├── Output: Dim_Fecha.csv
│   └── Columnas: fecha_key, fecha_date, año, mes, mes_nombre, trimestre, semana, día_semana
│   └── ~520 filas (una por fecha única en rango)
│   └── Ordenado por fecha_date
│
└── Guarda CSV en: data/model/Dim_Fecha.csv
```

**Python pseudo-código**:
```python
import pandas as pd
from datetime import datetime

# Leer BD PERSONAS
df_personas = pd.read_excel(
    "data/model/BD PERSONAS ATENDIDAS ORDINARIO 01-01-2025 A 24-05-2026.xlsx"
)

# Extraer fechas únicas
fechas = pd.to_datetime(df_personas["FECHA ATENCIÓN"]).unique()
fechas = sorted(fechas)

# Crear dimensión
dim_fecha = pd.DataFrame()
dim_fecha["fecha_date"] = fechas
dim_fecha["año"] = dim_fecha["fecha_date"].dt.year
dim_fecha["mes"] = dim_fecha["fecha_date"].dt.month
dim_fecha["mes_nombre"] = dim_fecha["fecha_date"].dt.strftime("%B").map({
    'January': 'Enero', 'February': 'Febrero', ..., 'December': 'Diciembre'
})
dim_fecha["fecha_key"] = dim_fecha["fecha_date"].dt.strftime("%Y%m%d").astype(int)
dim_fecha["trimestre"] = "Q" + (dim_fecha["mes"] // 3 + 1).astype(str)
dim_fecha["semana"] = dim_fecha["fecha_date"].dt.isocalendar().week
dim_fecha["día_semana"] = dim_fecha["fecha_date"].dt.day_name().map({
    'Monday': 'Lunes', 'Tuesday': 'Martes', ..., 'Sunday': 'Domingo'
})

# Guardar
dim_fecha.to_csv("data/model/Dim_Fecha.csv", index=False)
```

**Validación esperada**:
```
✅ Dim_Fecha.csv generado
   - Filas: 521 (01-01-2025 a 24-05-2026)
   - Años únicos: 2 (2025, 2026)
   - Meses: 1-12
   - Columnas: 8
   - Sin nulos
```

---

#### PASO 2.2: Integrar Dim_Fecha.csv en Modelo_Reporte_Paginas_2026.xlsx
```
Acción manual en Excel:
1. Abrir: data/model/Modelo_Reporte_Paginas_2026.xlsx
2. Crear nueva hoja: "Dim_Fecha"
3. Importar datos desde: data/model/Dim_Fecha.csv
4. Estructura final en Excel:
   ├── Hoja: Dim_Fecha
   │   ├── Encabezados: fecha_key, fecha_date, año, mes, mes_nombre, ...
   │   ├── 521 filas de datos
   │   └── Sin formato especial (headers + datos planos)
5. Guardar .xlsx

Alternativa (Power Query):
1. En Power BI Desktop conectado a Modelo_Reporte_Paginas_2026.xlsx
2. New Query → CSV File → Dim_Fecha.csv
3. Cargar como tabla "Dim_Fecha" en el modelo
4. Refresh
```

**Validación**: 
```
✅ Hoja "Dim_Fecha" existe en Excel
✅ 521 filas cargadas
✅ Encabezados exactos: fecha_key, fecha_date, año, mes, mes_nombre, trimestre, semana, día_semana
✅ Sin duplicados en fecha_key
```

---

### FASE 3: ESTABLECER RELACIONES (Día 2 - 45 minutos)

#### PASO 3.1: Identificar Columna de Unión en Hecho_Participacion_General
```
CRÍTICO: Determinar columna fecha en Hecho_Participacion_General

Nombre columna: ?
Tipo actual: Int64 | datetime | texto
Rango valores: 45000-46000 (serial) | 2025-01-01 | "01/01/2025"

Acciones:
1. Abrir Modelo_Reporte_Paginas_2026.xlsx en Excel
2. Localizar hoja "Hecho_Participacion_General"
3. Ver primeras 5 valores en columna fecha
4. Si serial: crear columna calculada en Power BI
5. Si datetime: listo para relación directa

Resultado esperado:
┌─────────────────────────────────────────────────────────────┐
│ Columna nombre: [INSERT_NAME]                              │
│ Tipo: [INSERT_TYPE]                                        │
│ Conversión requerida: SÍ / NO                             │
│ Fórmula DAX si es necesaria: [INSERT_FORMULA]             │
└─────────────────────────────────────────────────────────────┘
```

---

#### PASO 3.2: Crear Columna Calculada en Power BI (si necesaria)
**Dónde**: En el modelo Power BI abierto de tableroDAGRDCOPIA

**SI la columna fecha es Int64 (serial Excel)**:
```DAX
// En tabla "Hecho_Participacion_General"
// Nueva columna calculada:

fecha_convertida = DATE(1899, 12, 30) + [fecha]

// O si es número decimal:
fecha_convertida = INT(DATE(1899, 12, 30) + [fecha])
```

**SI la columna fecha ya es datetime**: Omitir este paso

**SI la columna fecha es texto**:
```DAX
fecha_convertida = DATEVALUE([fecha])
```

---

#### PASO 3.3: Crear Columna fecha_key en Hecho_Participacion_General
```DAX
// En tabla "Hecho_Participacion_General"
// Nueva columna calculada para unir con Dim_Fecha

fecha_key = INT(FORMAT(fecha_convertida, "YYYYMMDD"))

// Esto convierte: 2025-01-15 → 20250115 (número entero para join eficiente)
```

---

#### PASO 3.4: Establecer Relación en Power BI
```
En Power BI Desktop (Model view):
1. Ir a Model tab (vista de diagrama)
2. Localizar tabla Dim_Fecha y Hecho_Participacion_General
3. Crear relación:
   FROM: Dim_Fecha[fecha_key]
   TO: Hecho_Participacion_General[fecha_key]
   
   Propiedades:
   - Cardinalidad: One-to-Many (Dim_Fecha es "1")
   - Cross-filter direction: Single
   - Assume referential integrity: ☐ (NO, por si hay dates huérfanas)

4. Visualizar en diagrama para confirmar la línea de relación
```

**Validación**:
```
✅ Relación visible en Model diagram
✅ Dirección: Dim_Fecha → Hecho_Participacion_General
✅ Cardinalidad: 1-to-Many
✅ Sin errores de constraint
```

---

### FASE 4: CREAR MEDIDAS DAX PARA FILTROS (Día 3 - 1.5 horas)

#### PASO 4.1: Crear Tabla Medidas Auxiliar (Recomendado)
```
En Power BI, crear tabla "Dim_Fechas_Control" (oculta)

Propósito: Centralizar medidas y cálculos de filtros
Ubicación: Nueva tabla en el modelo
```

**Medidas a crear** (agregar a tabla `_Medidas` o nueva tabla):

---

#### PASO 4.2: Medida - Años Disponibles
```DAX
// Medida: Años_Disponibles
// Propósito: Lista dinámicamente años en datos

Años_Disponibles = 
CONCATENATEX(
    DISTINCT(
        FILTER(
            'Dim_Fecha'[año],
            COUNTROWS(
                FILTER(
                    'Hecho_Participacion_General',
                    'Hecho_Participacion_General'[fecha_key] = 'Dim_Fecha'[fecha_key]
                )
            ) > 0
        )
    ),
    'Dim_Fecha'[año],
    ", "
)

// Salida esperada: "2025, 2026"
```

---

#### PASO 4.3: Medida - Meses Disponibles para Año Seleccionado
```DAX
// Medida: Meses_En_Año
// Parámetro: Requiere SLICER en página filtrando Dim_Fecha[año]
// Propósito: Muestra meses disponibles para año seleccionado en filtro

Meses_En_Año = 
VAR año_sel = SELECTEDVALUE('Dim_Fecha'[año])
RETURN
IF(
    ISBLANK(año_sel),
    "N/A",
    CONCATENATEX(
        DISTINCT(
            FILTER(
                'Dim_Fecha'[mes_nombre],
                'Dim_Fecha'[año] = año_sel
            )
        ),
        'Dim_Fecha'[mes_nombre],
        ", "
    )
)

// Salida esperada (si año=2026): "Enero, Febrero, ..., Diciembre"
```

---

#### PASO 4.4: Medida - Total Participantes Filtrado por Año/Mes
```DAX
// Medida: Participantes_Por_Fecha
// Propósito: Suma dinámicamente participantes según filtros Año/Mes

Participantes_Por_Fecha = 
SUM('Hecho_Participacion_General'[participantes])

// Esta medida heredará filtros automáticos de:
// - Dim_Fecha[año] (si hay slicer año)
// - Dim_Fecha[mes] (si hay slicer mes)
// - A través de la relación fecha_key
```

---

#### PASO 4.5: Medida - Total Actividades Filtrado
```DAX
// Medida: Actividades_Por_Fecha
// Propósito: Cuenta actividades únicas por año/mes

Actividades_Por_Fecha = 
DISTINCTCOUNT('Hecho_Participacion_General'[actividad_id])

// También heredará filtros automáticamente
```

---

#### PASO 4.6: Medida - Empresas Únicas Filtradas por Año/Mes
```DAX
// Medida: Empresas_Detalle_Filtrada
// Propósito: Cuenta empresas únicas en rango Año/Mes

Empresas_Detalle_Filtrada = 
CALCULATE(
    DISTINCTCOUNT('Empresas_Detalle'[empresa_id]),
    FILTER(
        'Hecho_Participacion_General',
        'Hecho_Participacion_General'[sector] = "Empresarial"
            && 'Hecho_Participacion_General'[fecha_key] >= 
               VALUE(
                   SELECTEDVALUE('Dim_Fecha'[año], 2026) * 10000 + 
                   SELECTEDVALUE('Dim_Fecha'[mes], 1) * 100 + 1
               )
    )
)

// Alternativa (MÁS LIMPIA, usando relación):
Empresas_Detalle_Filtrada = 
CALCULATE(
    DISTINCTCOUNT('Empresas_Detalle'[empresa_id]),
    'Hecho_Participacion_General',
    FILTER(
        ALL('Hecho_Participacion_General'),
        'Hecho_Participacion_General'[sector] = "Empresarial"
    )
)
// Los filtros Año/Mes viajan automáticamente vía relación Dim_Fecha
```

---

#### PASO 4.7: Medida - Registros Comités/Comisiones por Año/Mes
```DAX
// Medida: Participantes_Comites_Por_Fecha
// Propósito: Participantes en Comités/Comisiones filtrando Año/Mes

Participantes_Comites_Por_Fecha = 
CALCULATE(
    SUM('Hecho_Participacion_General'[participantes]),
    FILTER(
        'Hecho_Participacion_General',
        'Hecho_Participacion_General'[bloque] = "Comunitaria"
            && 'Hecho_Participacion_General'[subbloque] = "Comites y Comisiones"
    )
)

// Los filtros de Dim_Fecha se aplican automáticamente
```

---

### FASE 5: CREAR SLICERS/FILTROS EN POWER BI (Día 3 - 45 minutos)

#### PASO 5.1: Agregar Slicer de Año
```
En Power BI Desktop → Vista Informe (Report view):
1. Ir a página donde mostrar filtros (ej: página 1 o nueva página "Controles")
2. Insert → Slicer
3. Campo: Dim_Fecha[año]
4. Style: Buttons | Dropdown | List
   (Recomendado: Buttons para 2 años)
5. Posicionar en esquina superior izquierda
6. Renombrar: "Año"
```

**Resultado**:
- Botones: [2025] [2026]
- Clicking filtra todas las visuales que usen Hecho_Participacion_General

---

#### PASO 5.2: Agregar Slicer de Mes
```
En Power BI:
1. Insert → Slicer
2. Campo: Dim_Fecha[mes_nombre]
3. Sort: Ascending (por orden calendárico, si es posible)
4. Style: Buttons | Dropdown
   (Recomendado: Dropdown para 12 meses)
5. Posicionar debajo o a la derecha del slicer de Año
6. Renombrar: "Mes"
```

**Resultado**:
- Dropdown: Enero, Febrero, ..., Diciembre (+ "Select All")
- Clicking filtra en cascada

---

#### PASO 5.3: Agregar Visuales de Tarjeta (Cards) para Validación
```
Propósito: Mostrar dinámicamente qué se está viendo

Visual 1: Card con Años_Disponibles
- Valor: [Años_Disponibles]
- Título: "Años en datos"
- Resultado esperado: "2025, 2026"

Visual 2: Card con Meses_En_Año
- Valor: [Meses_En_Año]
- Título: "Meses disponibles"
- Resultado esperado (año=2026): "Enero, Febrero, ..., Mayo"

Visual 3: Card con Participantes_Por_Fecha
- Valor: [Participantes_Por_Fecha]
- Formato: #,##0
- Título: "Total Participantes"
- Resultado: Actualiza al cambiar Año/Mes

Visual 4: Card con Actividades_Por_Fecha
- Valor: [Actividades_Por_Fecha]
- Formato: #,##0
- Título: "Total Actividades"
```

---

### FASE 6: VALIDACIÓN Y AJUSTES (Día 4 - 1 hora)

#### PASO 6.1: Test de Slicers
```
Test casos:
1. Seleccionar Año=2025 → Verificar que todas medidas actualizan
   ✓ Total Participantes ≠ Total 2026
   ✓ Total Actividades ≠ Total 2026
   ✓ Empresas Únicas cambia si hay datos 2025

2. Seleccionar Año=2025, Mes=Enero → Verificar mes específico
   ✓ Totales disminuyen
   ✓ Rango de fechas visible: 01-01-2025 a 31-01-2025

3. Seleccionar Año=2026, Mes=Mayo → Última combinación
   ✓ Totales reflejan mayo 2026
   ✓ Rango: 01-05-2026 a 24-05-2026 (parcial, por corte de datos)

4. Select All en Mes → Ver todos los meses del año
   ✓ Totales son suma de todos los meses
```

---

#### PASO 6.2: Verificar Relaciones
```
En Model diagram:
1. Activar relación Dim_Fecha → Hecho_Participacion_General
2. Con filtro Año=2025 en slicer, verificar línea se ilumina/está activa
3. Hacer ctrl+click en relación para ver detalles
4. Confirmar: cardinalidad 1-to-Many, dirección correcta

Si hay error "The key did not match any row...":
→ Hay fechas en Hecho_Participacion_General sin match en Dim_Fecha
→ Extender Dim_Fecha o revisar conversión fecha_key
```

---

#### PASO 6.3: Performance (si es necesario)
```
Si consultas lenta:
1. Crear índice en Power BI en columnas:
   - 'Dim_Fecha'[fecha_key]
   - 'Hecho_Participacion_General'[fecha_key]
   - 'Hecho_Participacion_General'[sector]

2. Considerar materializar "Participantes_Por_Fecha" en tabla separada:
   ├── AÑO, MES, TOTAL_PARTICIPANTES, TOTAL_ACTIVIDADES
   ├── Generada en ETL mensualmente
   └── Cargar como tabla ágil en lugar de fórmula dinámica

3. Medir tiempos: Ctrl+Alt+Shift+O (Diagnostics) en Power BI
```

---

### FASE 7: INTEGRACIÓN CON VISUALES EXISTENTES (Día 4 - 1.5 horas)

#### PASO 7.1: Conectar Slicers a Visuales Empresarial
```
Objetivo: Filtrar visuales "Empresas_Detalle" por Año/Mes

Acciones:
1. Seleccionar Visual "Total Empresas"
2. En Format panel → Slicer sync → Sincronizar con:
   ☑ Slicer Año
   ☑ Slicer Mes
3. Repetir para visuales:
   - "Empresas por CAM"
   - "Empresas por Sector"
   - "Planes de Ayuda Mutua"
   - Cualquier visual que use Hecho_Participacion_General

4. Test: Cambiar año → Visual actualiza
```

---

#### PASO 7.2: Conectar Slicers a Visuales Comités/Comisiones
```
Similar a 7.1, pero para visuales:
- "Total Comités"
- "Participantes Comités por Comuna"
- "Estado Comités" (Activo/Inactivo con filtro temporal)

Verificar que visuales usan:
- Medida: Participantes_Comites_Por_Fecha (o equivalente)
- Dimensión: Dim_Comites_Comisiones_2026 (mantiene estructura)
```

---

#### PASO 7.3: Documentar Filtros en Visual ToolTips
```
Objetivo: Usuarios entienden qué filtros aplican

En cada visual importante:
1. Format → Tooltips
2. Agregar card custom:
   "Datos filtrados por:
    - Año: <SELECTEDVALUE(Dim_Fecha[año])>
    - Mes: <SELECTEDVALUE(Dim_Fecha[mes_nombre])>
    - Rango: <MINVALUE(Hecho_Participacion_General[fecha])> a <MAXVALUE(...)>"
```

---

## 🔄 PLAN ALTERNATIVO: SIN DIMENSIÓN TEMPORAL (Opción D)

**SI la creación de Dim_Fecha no es viable**, usar fórmulas directas:

#### PASO ALT.1: Crear Columnas Calculadas en Hecho_Participacion_General
```DAX
// En tabla "Hecho_Participacion_General"

// Columna 1: Año
año_calc = YEAR([fecha_convertida])

// Columna 2: Mes
mes_calc = MONTH([fecha_convertida])

// Columna 3: Mes_Nombre
mes_nombre_calc = 
SWITCH(
    [mes_calc],
    1, "Enero",
    2, "Febrero",
    3, "Marzo",
    4, "Abril",
    5, "Mayo",
    6, "Junio",
    7, "Julio",
    8, "Agosto",
    9, "Septiembre",
    10, "Octubre",
    11, "Noviembre",
    12, "Diciembre"
)
```

#### PASO ALT.2: Crear Slicers con Columnas Calculadas
```
1. Insert → Slicer
2. Campo: 'Hecho_Participacion_General'[año_calc]
3. Repetir con [mes_calc] o [mes_nombre_calc]

VENTAJA: Más simple, no requiere dimensión separada
DESVENTAJA: Menor performance, más uso de memoria, medidas más complejas
```

#### PASO ALT.3: Medidas Alternativas (sin Dim_Fecha)
```DAX
Participantes_Año_Mes = 
CALCULATE(
    SUM('Hecho_Participacion_General'[participantes]),
    FILTER(
        'Hecho_Participacion_General',
        'Hecho_Participacion_General'[año_calc] = SELECTEDVALUE('Hecho_Participacion_General'[año_calc])
            && 'Hecho_Participacion_General'[mes_calc] = SELECTEDVALUE('Hecho_Participacion_General'[mes_calc])
    )
)
```

---

## 📋 RESUMEN DE ARCHIVOS A CREAR/MODIFICAR

| # | Acción | Archivo | Prioridad | Estimado |
|---|--------|---------|-----------|----------|
| 1 | Crear script Python | `scripts/etl/generar_dim_fecha.py` | 🔴 CRÍTICA | 30 min |
| 2 | Generar CSV | `data/model/Dim_Fecha.csv` | 🔴 CRÍTICA | 5 min |
| 3 | Integrar en Excel | `data/model/Modelo_Reporte_Paginas_2026.xlsx` (hoja Dim_Fecha) | 🔴 CRÍTICA | 10 min |
| 4 | Crear columnas Power BI | `fecha_convertida`, `fecha_key` en Hecho_Participacion_General | 🟠 ALTA | 15 min |
| 5 | Establecer relación | Relación 1-to-Many en Power BI | 🟠 ALTA | 10 min |
| 6 | Crear medidas DAX | 7 nuevas medidas en tabla `_Medidas` | 🟠 ALTA | 45 min |
| 7 | Agregar slicers | Slicer Año + Slicer Mes en página de control | 🟠 ALTA | 20 min |
| 8 | Validar + ajustar | Tests + performance tuning | 🟡 MEDIA | 60 min |

---

## ✅ CHECKLIST FINAL

### Entregables
- [ ] `scripts/etl/generar_dim_fecha.py` existe y ejecutable
- [ ] `data/model/Dim_Fecha.csv` generado (521 filas, 8 columnas)
- [ ] Hoja `Dim_Fecha` en `Modelo_Reporte_Paginas_2026.xlsx` con datos
- [ ] Columna `fecha_convertida` en Hecho_Participacion_General
- [ ] Columna `fecha_key` en Hecho_Participacion_General
- [ ] Relación Dim_Fecha ↔ Hecho_Participacion_General establecida
- [ ] 7 medidas DAX creadas y visibles
- [ ] Slicer Año funcional (muestra 2025, 2026)
- [ ] Slicer Mes funcional (muestra Enero-Diciembre)
- [ ] Visuales actualizan al cambiar filtros
- [ ] Tooltips documentan filtros activos
- [ ] Performance aceptable (<2s en filtrado)

---

## 🚀 ORDEN RECOMENDADO DE EJECUCIÓN

**Día 1 (Mañana)**:
1. PASO 1.1: Validar BD PERSONAS (15 min)
2. PASO 1.2: Verificar Modelo Excel (15 min)

**Día 2 (Tarde)**:
3. PASO 2.1: Crear generar_dim_fecha.py (45 min)
4. PASO 2.2: Integrar Dim_Fecha en Excel (15 min)
5. PASO 3.1-3.4: Relaciones en Power BI (1 hora)

**Día 3 (Mañana)**:
6. PASO 4.1-4.7: Crear medidas DAX (1.5 horas)
7. PASO 5.1-5.3: Slicers y visuales de control (45 min)

**Día 3 (Tarde)**:
8. PASO 6: Validación (1 hora)
9. PASO 7: Integración con visuales existentes (1.5 horas)

**Día 4 (Mañana)**:
10. Ajustes finales y documentación (1 hora)

---

## 📞 PREGUNTAS PENDIENTES (DEBE RESPONDER USUARIO)

1. ¿Columna de fecha en Hecho_Participacion_General es Int64 (serial)? ¿O datetime directo?
2. ¿El modelo tableroDAGRDCOPIA está en modo Live (XML/A) o modo Import?
3. ¿Los filtros Año/Mes deben estar en página separada de "Controles" o integrados en cada página temática?
4. ¿Se requiere filtro adicional por Trimestre o Semana (más allá de Año/Mes)?
5. ¿Hay visuales que NO deben recibir filtro de Año/Mes (fijas por diseño)?

---

## 📚 REFERENCIAS
- Archivo BD PERSONAS: `data/model/BD PERSONAS ATENDIDAS ORDINARIO 01-01-2025 A 24-05-2026.xlsx`
- Modelo actual: `data/model/Modelo_Reporte_Paginas_2026.xlsx`
- Medidas existentes: `scripts/dax/medidas_comites_comisiones.dax`
- Estructura actual: `/memories/repo/dashboard-estructura-datos.md`

---

**Estado**: 🟢 LISTO PARA EJECUCIÓN  
**Última actualización**: 26 de mayo de 2026  
**Autor**: GitHub Copilot  
**Versión del plan**: 1.0
