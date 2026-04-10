# 📊 Dashboard DAGRD - Organización y Documentación

**Última actualización:** 18 de marzo de 2026  
**Estado:** ✅ Reorganizado y optimizado

---

## 🚀 Qué Ver Primero (Para Revisores)

Si vas a evaluar el proyecto rápido, revisa en este orden:

1. `docs/core/RESUMEN_EJECUTIVO_DATOS.md`  
	Contexto, alcance y resultado general del proyecto.

2. `scripts/etl/extraer_consultas_paginas_reporte.py`  
	ETL principal que construye el modelo analítico para Power BI.

3. `powerbi/tmdl_live/tables/_Medidas.tmdl`  
	Medidas DAX centralizadas y lógica de indicadores/tablas.

4. `docs/core/VALIDACION_POWERBI_EXCEL_2026.md`  
	Evidencia de validación entre Excel y Power BI.

5. `docs/guides/GUIA_PASO_A_PASO_POWERBI_DAGRD.md`  
	Flujo operativo para reproducir y mantener el tablero.

---

## 📦 Publicación en GitHub

Archivos clave para colaboración y despliegue del entorno:

- `requirements.txt` (dependencias Python)
- `LICENSE` (licencia MIT)
- `CONTRIBUTING.md` (guía de contribución)

Instalación rápida:

```bash
pip install -r requirements.txt
```

---

## 📁 Estructura de Carpetas

```
Dashboard/
│
├── 📂 data/                    # Datos y modelos
│   ├── model/                  # Archivos Excel principales
│   │   ├── Modelo_Reporte_Paginas_2026.xlsx      # ⭐ ARCHIVO PRINCIPAL
│   │   ├── Participantes_Generales_Reporte_2026.xlsx
│   │   ├── Participantes_Generales_Transaccional_2026.xlsx
│   │   ├── Modelo_Reporte_Paginas_2026_BACKUP.xlsx  # Backup
│   │   └── ...
│   ├── raw/                    # Datos sin procesar
│   ├── source/                 # Datos fuente
│   └── reference/              # Datos de referencia
│
├── 📂 scripts/                 # Automatización y procesamiento
│   ├── etl/                    # Extracción, transformación, carga
│   │   ├── crear_tabla_semilleros.py              # ⭐ NUEVO: Crear Dim_Semilleros
│   │   ├── extraer_consultas_paginas_reporte.py
│   │   ├── extraer_participantes_generales_reporte.py
│   │   ├── extraer_participantes_transaccional_reporte.py
│   │   ├── actualizar_37_satc_final.py
│   │   └── regenerar_puente_37.py                 # Normalizar SAT-C
│   │
│   ├── qa/                     # Control de calidad y validación
│   │   ├── analizar_kpis_comunidad.py
│   │   └── perfil_bloques_comunidad.py
│   │
│   ├── powerbi/                # Scripts para Power BI
│   │   ├── crear_medidas_satc.py
│   │   ├── crear_medidas_semilleros.py           # ⭐ NUEVO: Medidas Semilleros
│   │   └── preparar_modelo_powerbi.py
│   │
│   └── dax/                    # Definiciones DAX para Power BI
│       ├── medidas_satc.dax
│       └── medidas_semilleros.dax                # ⭐ NUEVO
│
├── 📂 docs/                    # Documentación
│   ├── core/                   # Documentación principal
│   │   ├── ANALISIS_ESTRUCTURA_DATOS_COMPLETO.md
│   │   ├── EXTRACCION_DATOS_COMPLETA.md
│   │   └── RESUMEN_EJECUTIVO_DATOS.md
│   │
│   ├── guides/                 # Guías paso a paso
│   │   └── GUIA_PASO_A_PASO_POWERBI_DAGRD.md
│   │
│   └── legacy/                 # Documentación antigua
│
├── 📂 powerbi/                 # Configuración Power BI
│   ├── pbix/                   # Archivos Power BI Desktop (.pbix)
│   ├── config/                 # Configuraciones
│   └── dax/                    # Scripts DAX (legacy)
│
├── 📂 Tableros/                # Dashboards e informes
│
├── 📂 .venv/                   # Entorno virtual Python (ignorar)
│
├── 🔵 README.md                # Este archivo
└── 📋 .gitignore               # Archivos ignorados en Git
```

---

## 📊 Tablas Principales en Excel

### ✅ **Dim_Semilleros** (NUEVA - 20 registros)
Tabla confiable de Semilleros DAGRD que incluye:
- **Columnas:** N°, Semillero, Comuna, Comuna_Nombre, Barrio_Organización
- **Registros:** 20 semilleros únicos
- **Comunas:** Distribuidos en 9 comunas
- **Fuente:** Datos oficiales DAGRD
- **Ubicación:** Hoja 2 en `Modelo_Reporte_Paginas_2026.xlsx`

**Cómo usar:**
```dax
Total_Semilleros = DISTINCTCOUNT(Dim_Semilleros[Semillero])  // = 20
```

### ✅ **Dim_SATC** (37 registros)
- **Columnas:** SATC_ID, SATC_Nombre, Comuna_Cod, Talleres, Comites, Activo
- **Registros:** 37 SAT-C validados y normalizados
- **Comunas:** 12 comunas cubiertas

### ✅ **Hecho_Participacion_General** (3,502 registros)
- **Campos clave:** id_actividad, fecha, comuna_cod, nombre_satc, bloque_comunidad, satc_id, participantes
- **Bloques:** SAT-C, Comisiones y comites, Semilleros, Hogares seguros, Otros Procesos Organizativos
- **Cobertura:** 49.6% (1,737 registros con satc_id)

### ✅ **Puente_SATC_Comuna** (37 registros)
- **Mapeo:** Relación entre SATC y Comuna
- **Cardinality:** 1:1 (cada SATC mapea a una comuna)

---

## 🔄 Flujo de Trabajo Recomendado

### 1️⃣ **Actualizar Datos (ETL)**
```bash
# Extraer datos actualizados
python scripts/etl/extraer_consultas_paginas_reporte.py
python scripts/etl/extraer_participantes_generales_reporte.py

# Regenerar SAT-C (si hay cambios)
python scripts/etl/regenerar_puente_37.py

# Crear/actualizar Semilleros
python scripts/etl/crear_tabla_semilleros.py
```

### 2️⃣ **Validar Datos (QA)**
```bash
# Analizar KPIs y estructura
python scripts/qa/analizar_kpis_comunidad.py
python scripts/qa/perfil_bloques_comunidad.py
```

### 3️⃣ **Actualizar Power BI**
```bash
# Generar medidas DAX
python scripts/powerbi/crear_medidas_satc.py
python scripts/powerbi/crear_medidas_semilleros.py

# Luego en Power BI Desktop:
# 1. Ctrl+Shift+R (Refrescar datos)
# 2. Modelado → Nueva medida (copiar de scripts/dax/*.dax)
# 3. Crear/actualizar visuales
```

---

## 📈 Medidas DAX Disponibles

### Para SAT-C
```dax
Total_SATC_Unicos               // = 37
SATC_Principales               // Activos en datos
Actividades_por_SATC           // Conteo por SAT-C
Participantes_por_SATC         // Suma de participantes
Cobertura_SATC_Porcentaje      // % de cobertura
```

### Para Semilleros
```dax
Total_Semilleros               // = 20
Semilleros_por_Comuna          // = 9
Semilleros_Activos             // Con participación
Comuna_Seleccionada_Semilleros // Para slicers
```

**Ubicación:** [scripts/dax/medidas_semilleros.dax](scripts/dax/medidas_semilleros.dax)

---

## 🛠️ Configuración y Requisitos

### Requisitos Previos
- Python 3.8+
- Librerías: pandas, openpyxl, unicodedata
- Power BI Desktop (última versión)
- Excel 2019+ o Microsoft 365

### Instalación
```bash
# 1. Crear entorno virtual (ya existe en .venv/)
python -m venv .venv

# 2. Activar entorno
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install pandas openpyxl
```

---

## 🔐 Datos de Semilleros - Garantía de Confiabilidad

✅ **20 Semilleros Registrados Oficialmente**

| N° | Semillero | Comuna | Barrio/Organización |
|---|---|---|---|
| 1 | IE Fe y Alegría | 1 - Popular | Popular - IE Fe y Alegría |
| 2 | Comunidad Embera Dobida | 80 - San Antonio | San Antonio de Prado |
| 3 | Olaya Herrera | 7 - Robledo | Olaya Herrera - Comisión Riesgo |
| 4 | Villatina | 8 - Villa Hermosa | Villatina |
| 5 | El Pesebre | 13 - San Javier | El Pesebre - Mesa Gestión Riesgo |
| ... | ... | ... | ... |

**Ver tabla completa:** [data/model/Modelo_Reporte_Paginas_2026.xlsx](data/model/Modelo_Reporte_Paginas_2026.xlsx) → Hoja `Dim_Semilleros`

---

## 📝 Archivo de Semilleros en Power BI

### Paso 1: Refrescar datos Excel
1. Abre `Modelo_Reporte_Paginas_2026.xlsx`
2. Verifica que la hoja `Dim_Semilleros` esté presente
3. En Power BI Desktop: `Inicio` → `Refrescar` (Ctrl+Shift+R)

### Paso 2: Crear relaciones (si es necesario)
1. `Modelado` → `Administrar relaciones`
2. Crear relación: `Dim_Semilleros[Comuna]` → `Hecho_Participacion_General[comuna_cod]`
3. Cardinality: **Muchos a 1 (M:1)**

### Paso 3: Agregar medidas
1. `Modelado` → `Nueva medida`
2. Copiar cada medida desde [scripts/dax/medidas_semilleros.dax](scripts/dax/medidas_semilleros.dax)
3. Pegar en la tabla correspondiente

### Paso 4: Crear visuales
1. Tabla o matriz con Semilleros por Comuna
2. Card con Total_Semilleros (= 20)
3. Slicer por Comuna_Nombre

---

## 🗂️ Guía de Archivos Importantes

| Archivo | Propósito | Actualización |
|---------|----------|---------------|
| **Modelo_Reporte_Paginas_2026.xlsx** | Datos maestro para Power BI | Manual o automated |
| **scripts/etl/crear_tabla_semilleros.py** | Generar Dim_Semilleros | Según sea necesario |
| **scripts/dax/medidas_semilleros.dax** | Medidas DAX para Semilleros | Generado automáticamente |
| **docs/guides/GUIA_PASO_A_PASO_POWERBI_DAGRD.md** | Tutoriales paso a paso | Referencia |

---

## ⚡ Comandos Rápidos

```bash
# Activar entorno Python
.\.venv\Scripts\Activate.ps1

# Crear tabla Semilleros
python scripts/etl/crear_tabla_semilleros.py

# Validar datos
python scripts/qa/analizar_kpis_comunidad.py

# Generar medidas DAX
python scripts/powerbi/crear_medidas_semilleros.py

# Ver estructura
tree /F (Windows) o tree -L 3 (Mac/Linux)
```

---

## 📞 Soporte y Preguntas

### Problemas Comunes

**P: Semilleros no aparecen en Power BI**
- ✅ Verificar que `Dim_Semilleros` exista en Excel (script `crear_tabla_semilleros.py`)
- ✅ Ejecutar Refrescar en Power BI (Ctrl+Shift+R)
- ✅ Verificar relaciones en Modelado
- ✅ Confirmar que medidas están creadas

**P: SAT-C no se ven normalizados**
- ✅ Ejecutar `regenerar_puente_37.py`
- ✅ Validar con `analizar_kpis_comunidad.py`
- ✅ Refrescar Power BI

**P: Archivo Excel se ve corrupto**
- ✅ Usar backup: `Modelo_Reporte_Paginas_2026_BACKUP.xlsx`
- ✅ Regenrar desde cero: `python scripts/etl/*.py`

---

## 🎯 Próximos Pasos

- [ ] Ejecutar `crear_tabla_semilleros.py` ✅ HECHO
- [ ] Refrescar Power BI con nuevos datos
- [ ] Crear visuales para Semilleros
- [ ] Validar medidas con datos reales
- [ ] Documentar proceso de actualización mensual

---

**Mantenido por:** DAGRD  
**Última revisión:** 2026-03-18  
**Versión:** 2.0.0
