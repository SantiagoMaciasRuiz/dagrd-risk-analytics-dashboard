# 📊 ANÁLISIS ESTRUCTURADO DE DATOS - DASHBOARD GESTION DE RIESGOS

**Fecha de análisis:** 10 de marzo de 2026  
**Carpeta analizada:** `c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard\datos`  
**Total de archivos:** 7 archivos .xls

---

## 📋 RESUMEN EJECUTIVO

| Archivo | Hojas | Filas | Columnas | Período | Información Clave |
|---------|-------|-------|----------|---------|-------------------|
| **talleres_2026-03-10_19-14.xls** | 1 | 282 | 46 | 2025-2026 | Actividades de capacitación y talleres por Comuna |
| **comités_comisiones comunitarios_2026-03-10_19-15.xls** | 1 | 135 | 22 | Actualizado | Comités y comisiones comunitarios activos e inactivos |
| **eventos históricos_2026-03-10_19-15.xls** | 1 | 46 | 19 | 2008-2022 | Eventos desastrosos históricos y víctimas |
| **cosegrd_2026-03-10_19-15.xls** | 1 | 99 | 18 | Actualizado | Comités de SEGRD (Gestión Riesgo Desastres) |
| **estudios_2026-03-10_19-15.xls** | 1 | 118 | 24 | 2008-2022 | Estudios geológicos, geotécnicos e hidrológicos |
| **instituciones educativas (puntos)_2026-03-10_19-15.xls** | 1 | 779 | 29 | 2024 | Escuelas y colegios ubicados en Medellín |
| **obras_2026-03-10_19-14.xls** | 1 | 178 | 23 | 2016-2022 | Obras de mitigación y estabilización ejecutadas |

---

## 1️⃣ TALLERES_2026-03-10_19-14.XLS

**Dimensiones:** 282 filas × 46 columnas  
**Propósito:** Registro de talleres, capacitaciones y actividades comunitarias

### Campos de FECHA (Temporal)
| Campo | Tipo | Descripción | Ejemplos |
|-------|------|-------------|----------|
| `fecha_ini` | Texto (fecha) | Fecha de inicio del taller | 2025-06-21, 2025-01-19, 2025-03-02 |

### Campos de UBICACIÓN/GEOGRAFÍA (Geográfico)
| Campo | Tipo | Valores Únicos | Ejemplos |
|-------|------|----------------|----------|
| `comuna_cod` | Entero | 16 comunas | 11, 70, etc. |
| `comuna_nom` | Texto | 16 comunas | Laureles Estadio, Altavista, Manrique |
| `barrio_nom` | Texto | 227 barrios | Bolivariana, Aguas Frías, etc. |
| `latitud` | Decimal | 282 valores únicos | 6.245510, 6.226953 |
| `longitud` | Decimal | 282 valores únicos | -75.592203, -75.634765 |

### Campos de CANTIDADES/PARTICIPANTES (Numéricos)
| Campo | Tipo | Min | Max | Promedio | Descripción |
|-------|------|-----|-----|----------|------------|
| `partic_num` | Entero | 0 | varios | - | Número de participantes |
| `mujere_num` | Entero | 0 | varios | - | Participantes mujeres |
| `hombre_num` | Entero | 0 | varios | - | Participantes hombres |
| `ninos_num` | Entero | 0 | varios | - | Niños participantes |
| `impac_indi` | Entero | 0 | varios | - | Indicadores de impacto |

### Campos de VULNERABILIDAD/POBLACIÓN ESPECÍFICA (Desgregación)
| Campo | Tipo | Ejemplo |
|-------|------|---------|
| `pri_infanc` | Entero | Primera Infancia |
| `nino_adole` | Entero | Niño-adolescencia |
| `juventud` | Entero | Población joven |
| `adulto` | Entero | Población adulta |
| `adulto_may` | Entero | Adultos mayores |
| `discapacid` | Entero | Personas con discapacidad |
| `afrodescen` | Entero | Población afrodescendiente |
| `campesino` | Entero | Poblacion campesina |
| `pob_victim` | Entero | Población víctima del conflicto |
| `pob_migran` | Entero | Población migrante |
| `pob_lgtbi` | Entero | Población LGTBI |
| `pob_indige` | Entero | Población indígena |
| `pob_rom` | Entero | Población Rrom |

### Campos de CATEGORIZACIÓN
| Campo | Opciones | Descripción |
|-------|----------|-------------|
| `instancia` | Buen Comienzo - Primera Infancia, Comunitario, Institucional, Empresarial, Educativo | Tipo de instancia beneficiaria |
| `tipo_activ` | 41 categorías | Tipos específicos de actividad (Taller Navidad Segura, Capacitación GRD, etc.) |
| `modalidad` | Presencial, Virtual | Forma de ejecución |
| `modulo` | talleres | Módulo base |

### Campos Relacionados con CAPACITACIÓN
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `rel_metPDD` | Texto | Relación con metas del Plan de Desarrollo |
| `cert_activ` | Texto | Certificación de actividades |
| `profesionales` | Texto | Profesionales que dictaron taller |

### ⚠️ Calidad de Datos
- **Campos completamente vacíos (100% nulos):** publicoObjeto, publicoObjetoOtro, nombreComiteComision, nombreSATC, nombreComiteAyudaMutua, nombreMesaInterinstitucional, profe_nom
- **Campos con muchos nulos:** barrio_cod (98.6%), profe_otro (77.7%)
- **Campos limpios:** Datos de participantes, fechas, comunas, ubicación

---

## 2️⃣ COMITÉS_COMISIONES COMUNITARIOS_2026-03-10_19-15.XLS

**Dimensiones:** 135 filas × 22 columnas  
**Propósito:** Registro de comités y comisiones comunitarios (JACs, grupos de gestión de riesgo, etc.)

### Campos de UBICACIÓN/GEOGRAFÍA
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `comuna_cod` | Entero | Código de comuna | 90 |
| `comuna_nom` | Texto | Nombre de comuna | Corregimiento De Santa Elena |
| `barrio_cod` | Entero | Código de barrio | 9003 |
| `barrio_nom` | Texto | Nombre de barrio | Piedras Blancas - Matasano |
| `latitud` | Decimal | Coordenada de ubicación | 6.234925 |
| `longitud` | Decimal | Coordenada de ubicación | -75.516669 |
| `direccion` | Texto | Dirección postal | 45 valores nulos (33.3%) |

### Campos de INFORMACIÓN ORGANIZATIVA
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `nom_titulo` | Texto | 135 | Nombre oficial del comité/comisión |
| `junt_accio` | Texto | 134 | Junta de acción comunal afiliada |
| `coordi_nom` | Texto | 135 | Nombre del coordinador |
| `coo_contac` | Entero | 135 | Teléfono contacto del coordinador |
| `integr_num` | Entero | 135 | Número de integrantes del comité |

### Campos de CATEGORIZACIÓN
| Campo | Opciones | Descripción |
|-------|----------|-------------|
| `estado` | Activo, Inactivo | Estado del comité |

### Campos GEOGRÁFICOS ADICIONALES
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `area` | Decimal | Área de cobertura (m²) |
| `perimetro` | Decimal | Perímetro de cobertura (m) |

### ⚠️ Calidad de Datos
- **Campos completamente vacíos:** descripcio (100%), imagenes (100%), planesAccion (100%), caracterizacion (99.3%), geometry (94.8%)
- **Campos limpios:** Información básica de ubicación, coordinador, estado
- **Datos faltantes:** Dirección (33.3%)

---

## 3️⃣ EVENTOS HISTÓRICOS_2026-03-10_19-15.XLS

**Dimensiones:** 46 filas × 19 columnas  
**Propósito:** Registro de desastres naturales históricos ocurridos en Medellín

### Campos de FECHA (Temporal)
| Campo | Tipo | Rango | Descripción |
|-------|------|-------|-------------|
| `fecha` | Texto (fecha) | 2008-2022 | Fecha del evento desastroso |

### Campos de UBICACIÓN
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `comuna_cod` | Entero | 46 | Código de comuna afectada |
| `comuna_nom` | Texto | 46 | Nombre de comuna afectada |
| `barrio_cod` | Texto | 46 | Código de barrio afectado |
| `barrio_nom` | Texto | 46 | Nombre de barrio afectado |
| `localizaci` | Texto | 12 | Descripción de localización específica |
| `latitud` | Decimal | 46 | Coordenada de ubicación |
| `longitud` | Decimal | 46 | Coordenada de ubicación |

### Campos de VÍCTIMAS/IMPACTO (VULNERABILIDAD)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `vict_fatal` | Entero | Número de víctimas fatales |
| `lesionados` | Entero | Número de personas lesionadas |

### Campos DESCRIPTIVOS Y DE CONOCIMIENTO
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `nom_titulo` | Texto | 46 | Nombre del evento histórico |
| `descripcio` | Texto | 46 | Descripción detallada del evento |
| `fenomenos` | Texto | 46 | Tipo de fenómeno (Movimiento en masa, flujo de lodos, etc.) |
| `nivel` | Texto | 12 | Nivel administrativo afectado (Distrital, Local) |
| `enlaces` | Texto | 21 | Referencias/enlace a fuentes |
| `imagenes` | Texto | 34 | Rutas a imágenes documentales |

### ⚠️ Calidad de Datos
- **Datos incompletos:** localizaci (73.9% nulos), nivel (73.9% nulos), enlaces (54.3% nulos), imagenes (26.1% nulos)
- **Datos completos:** Fechas, ubicación básica, víctimas, descripción, fenómeno
- **Rango temporal:** 14 años (2008-2022)

---

## 4️⃣ COSEGRD_2026-03-10_19-15.XLS

**Dimensiones:** 99 filas × 18 columnas  
**Propósito:** Registro de Comités de SEGRD (Comités de Esquemas de Gestión de Riesgos de Desastres)

### Campos de UBICACIÓN
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comuna_cod` | Entero | Código de comuna |
| `comuna_nom` | Texto | Nombre de comuna |
| `barrio_cod` | Texto | Código de barrio |
| `barrio_nom` | Texto | Nombre de barrio |
| `latitud` | Decimal | Coordenada de ubicación |
| `longitud` | Decimal | Coordenada de ubicación |

### Campos ORGANIZATIVOS
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `nom_titulo` | Texto | 99 | Nombre oficial del CAM (Centro de Atención y Monitoreo) |
| `integrante` | Texto | 99 | Instituciones y actores integrantes del COSEGRD |
| `estado` | Texto | 99 | Estado (Activo/Inactivo) |

### Campos GEOGRÁFICOS Y ADMINISTRATIVOS
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `area` | Decimal | Área de jurisdicción (m²) |
| `perimetro` | Decimal | Perímetro (m) |
| `modulo` | Texto | Módulo de origen |

### ⚠️ Calidad de Datos
- **Campos completamente vacíos:** doc_pdf (100%), planesAccion (100%), caracterizacion (100%)
- **Datos faltantes:** Imágenes (25.3%)
- **Datos completos:** Ubicación, nombre, estado, integrantes
- **Capacidad de almacenamiento:** Registra actores estratégicos en gestión del riesgo

---

## 5️⃣ ESTUDIOS_2026-03-10_19-15.XLS

**Dimensiones:** 118 filas × 24 columnas  
**Propósito:** Registro de estudios técnicos (geológicos, geotécnicos, etc.) realizados

### Campos de FECHA (Temporal)
| Campo | Tipo | Rango | Descripción |
|-------|------|-------|-------------|
| `fecha` | Entero | 2008-2022 | Año de realización del estudio |

### Campos de UBICACIÓN
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comuna_cod` | Entero | Código de comuna estudiada |
| `comuna_nom` | Texto | Nombre de comuna estudiada |
| `barrio_cod` | Entero | Código de barrio |
| `barrio_nom` | Texto | Nombre de barrio |
| `latitud` | Decimal | Coordenada de ubicación |
| `longitud` | Decimal | Coordenada de ubicación |

### Campos TÉCNICOS Y DE CONTRATACIÓN
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `contra_num` | Texto | 118 | Número de contrato |
| `objeto` | Texto | 118 | Objeto/propósito del estudio |
| `contratist` | Texto | 118 | Firma contratista que ejecutó el estudio |
| `ent_ejecut` | Texto | 118 | Entidad ejecutora (DAGRD, etc.) |
| `intervento` | Texto | 9 | Interventor del proyecto |

### Campos de ANÁLISIS Y CATEGORIZACIÓN
| Campo | Valor | Descripción |
|-------|-------|-------------|
| `tipo_estud` | 25 categorías | Tipo de análisis realizados |
| `estado` | Ejecutado | Estado del estudio |

**Ejemplos de tipos de estudio:**
- Geológico, Geotécnico
- Geológico, Geotécnico, Hidrológico, Hidráulico
- Geológico, Geotécnico, Hidrogeotécnico, Análisis de vulnerabilidad
- Geotécnico

### Campos DESCRIPTIVOS
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `nom_titulo` | Texto | 118 | Nombre/título del estudio |
| `descripcion` | Texto | 111 | Descripción detallada del estudio |
| `fenomenos` | Texto | 118 | Fenómenos analizados (Riesgo por Movimientos en masa) |
| `doc_pdf` | Texto | 111 | Enlaces a documentos técnicos (PDF) |
| `imagenes` | Texto | 112 | Referencias a imágenes/mapas |

### ⚠️ Calidad de Datos
- **Datos faltantes:** doc_pdf (5.9%), descripcion (5.9%), intervento (92.4%), geometry (100%)
- **Datos completos:** Ubicación, tipo de estudio, año, contratista
- **Importancia:** Base de conocimiento técnico sobre vulnerabilidades

---

## 6️⃣ INSTITUCIONES EDUCATIVAS (PUNTOS)_2026-03-10_19-15.XLS

**Dimensiones:** 779 filas × 29 columnas  
**Propósito:** Directorio de escuelas y colegios en Medellín (información DANE)

### Campos de UBICACIÓN GEOGRÁFICA
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `latitud` | Decimal | Coordenada de ubicación |
| `longitud` | Decimal | Coordenada de ubicación |
| `nombre_barrio` | Texto | Nombre de barrio |
| `nombre_comuna` | Texto | Nombre de comuna |
| `codigo_barrio` | Texto | Código de barrio |
| `codigo_comuna` | Texto | Código de comuna |
| `direccion` | Texto | Dirección postal de la institución |

### Campos ADMINISTRATIVOS Y DE INFORMACIÓN DANE
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `cbml` | Entero | 779 | Código DANE de establecimiento |
| `codigo_dane` | Entero | 779 | Código DANE |
| `dane_sede` | Entero | 779 | Código DANE de la sede |
| `nombre_establecimiento` | Texto | 779 | Nombre oficial de la institución |
| `nombre_sede` | Texto | 779 | Nombre de la sede educativa |

### Campos de CARACTERIZACIÓN
| Campo | Opciones | Descripción |
|-------|----------|-------------|
| `estado` | Activo | Estado del registro |
| `servicio` | Oficial, No Oficial | Tipo de servicio |
| `sector` | Oficial, No Oficial | Sector educativo |
| `clasificacion` | Oficial-Sede, No Oficial-Principal | Clasificación administrativa |

### Campos ADMINISTRATIVOS ADICIONALES
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `vigencia` | Entero | Año de vigencia (2024) |
| `telefono` | Texto | Teléfono de contacto |
| `cons_sede` | Entero | Consecutivo de sede |
| `nucleo` | Entero | Núcleo educativo |
| `objectid` | Entero | ID de objeto en base de datos |
| `x_origen_nacional` | Decimal | Coordenada X (origen nacional) |
| `y_origen_nacional` | Decimal | Coordenada Y (origen nacional) |

### ⚠️ Calidad de Datos
- **Campos COMPLETAMENTE VACÍOS:** institucion (99.9%), documentos (99.9%), caracterizacion (99.9%)
- **Datos LIMPIOS:** Ubicación, codificación DANE, nombres, estado
- **Cobertura:** 779 instituciones educativas
- **Utilidad:** Mapa de infraestructura educativa para análisis de riesgo para poblaciones escolares

---

## 7️⃣ OBRAS_2026-03-10_19-14.XLS

**Dimensiones:** 178 filas × 23 columnas  
**Propósito:** Registro de obras ejecutadas para mitigación y estabilización de riesgos

### Campos de FECHA (Temporal)
| Campo | Tipo | Rango | Descripción |
|-------|------|-------|-------------|
| `fecha` | Entero | 2016-2022 | Año de ejecución de la obra |

### Campos de UBICACIÓN
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `comuna_cod` | Entero | Código de comuna |
| `comuna_nom` | Texto | Nombre de comuna |
| `barrio_cod` | Entero | Código de barrio |
| `barrio_nom` | Texto | Nombre de barrio |
| `direccion` | Texto | Dirección específica de la obra |
| `latitud` | Decimal | Coordenada de ubicación |
| `longitud` | Decimal | Coordenada de ubicación |

### Campos TÉCNICOS Y DE CONTRATACIÓN
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `contra_num` | Entero | 178 | Número de contrato |
| `objeto` | Texto | 178 | Objeto de la obra |
| `contratist` | Texto | 178 | Empresa contratista ejecutora |
| `ent_ejecut` | Texto | 178 | Entidad ejecutora (generalmente DAGRD) |
| `intervento` | Texto | 4 | Interventor/supervisor |

### Campos de TIPO Y AVANCE
| Campo | Opciones | Descripción |
|-------|----------|-------------|
| `tipo_obra` | 6 categorías | Tipo de intervención |
| `estado` | Ejecutada | Estado final |
| `avance` | 100% | Porcentaje de avance |

**Tipos de obra encontrados:**
- Estabilización, Protección
- Estabilización, Protección, Manejo de aguas
- Protección, Manejo de aguas
- Estabilización
- Protección

### Campos DESCRIPTIVOS Y DE FENÓMENOS
| Campo | Tipo | No Nulos | Descripción |
|-------|------|----------|-------------|
| `nom_titulo` | Texto | 178 | Título de la obra |
| `descripcion` | Texto | 177 | Descripción técnica de la obra |
| `fenomenos` | Texto | 177 | Fenómenos/riesgos que mitiga (Riesgo por Movimientos en masa) |
| `imagenes` | Texto | 47 | Referencias a imágenes/documentación |

### ⚠️ Calidad de Datos
- **Datos faltantes:** tipo_obra (0.6%), descripcion (0.6%), imagenes (73.6%), intervento (97.8%)
- **Datos LIMPIOS:** Ubicación, tipo, estado, año, contratista
- **Completitud:** Muy buena para información operacional
- **Período:** 2016-2022 (6 años de ejecución)

---

## 📊 ANÁLISIS COMPARATIVO Y SÍNTESIS

### Cobertura Temporal
```
2008 ─────── 2016 ──── 2018 ──── 2022 ──── 2023 ──── 2025 ──── 2026
  ↓           ↓        ↓        ↓                      ↓
Eventos   Obras   Estudios  Más Obras           Talleres 2025-2026
```

### Campos Clave Consolidados

#### 1. UBICACIÓN/GEOGRAFÍA (presente en todos)
- **Comuna:** 16 comunas + 5 corregimientos
- **Coordenadas:** Latitud/Longitud disponibles en la mayoría
- **Resolución:** Barrio/ubicación precisa en talleres, instituciones educativas

#### 2. FECHA/TIEMPO (presente en 4 archivos)
- **Talleres:** 2025-2026 (datos recientes)
- **Estudios:** 2008-2022
- **Obras:** 2016-2022
- **Eventos históricos:** 2008-2022

#### 3. POBLACIÓN/VULNERABILIDAD
- **Talleres:** 14 campos de desgregación de población (mujeres, hombres, edad, etnias, migrantes, víctimas)
- **Eventos históricos:** Víctimas fatales y lesionados
- **Instituciones educativas:** 779 escuelas para poblaciones escolares

#### 4. CAPACITACIÓN
- **Talleres:** 282 actividades registradas, 41 tipos diferentes
- **Modalidad:** Presencial y Virtual
- **Alcance:** Múltiples instancias (Buen Comienzo, Comunitario, Institucional, Empresarial, Educativo)

#### 5. VULNERABILIDAD/RIESGO
- **Fenómenos principales:** Riesgo por Movimientos en masa (deslizamientos, flujos de lodo)
- **Mitigación:** 178 obras ejecutadas (2016-2022)
- **Conocimiento técnico:** 118 estudios (geológicos, geotécnicos, hidráulicos)
- **Institucionalidad:** 99 Comités SEGRD + 135 Comités Comunitarios

#### 6. ACTORES/GESTIÓN
- **Coordinadores:** Nombres en comités
- **Contratistas:** Empresas ejecutoras de obras y estudios
- **Entidades ejecutoras:** Principalmente DAGRD
- **Instituciones clave:** AMVA, SIATA, Ejército, Universidad de Antioquia, Metro, etc.

---

## ⚙️ RECOMENDACIONES PARA EXCEL ONLINE

### 1. **Tablas Estructuradas**
```
✓ Crear tabla "tbl_Talleres" con campos: ID, Fecha, Comuna, Tipo, Participantes
✓ Crear tabla "tbl_Obras" con campos: ID, Fecha, Comuna, Tipo, Estado
✓ Crear tabla "tbl_Vulnerabilidad" desgregada por población
```

### 2. **Validaciones a Implementar**
- **Comuna:** Lista desplegable con 16+5 comunas/corregimientos
- **Fecha:** Validación de formato AAAA-MM-DD
- **Modalidad:** Lista (Presencial/Virtual)
- **Estado:** Lista (Activo/Inactivo/Ejecutado/Ejecutada)

### 3. **Análisis con Fórmulas**
- `FILTER()` para filtrar por comuna/período
- `SUMIF()` para sumar participantes por tipo de actividad
- `UNIQUE()` para listar categorías únicas
- `XLOOKUP()` para enlazar instituciones con ubicaciones

### 4. **Tablas de Análisis Recomendadas**
- Participantes por Comuna y Período
- Obras por Tipo de Riesgo
- Eventos Históricos con Mayor Impacto (por víctimas)
- Cobertura de Talleres por Población Vulnerable
- Distribución de Instituciones Educativas

---

**Documento generado:** 10/03/2026  
**Análisis completo:** ✅ Todos los archivos analizados exitosamente
