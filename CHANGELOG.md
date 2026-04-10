# 📝 CHANGELOG - Dashboard DAGRD

## [2.0.0] - 2026-03-18 ⭐ REORGANIZACIÓN Y SEMILLEROS

### 🎯 Cambios Principales

#### Reorganización de Estructura
- ✅ Movimiento de scripts a carpetas lógicas
  - `scripts/etl/` - Scripts de extracción y transformación
  - `scripts/qa/` - Scripts de validación y análisis
  - `scripts/powerbi/` - Scripts de generación de medidas
  - `scripts/dax/` - Definiciones de medidas DAX

#### Nueva Tabla: Dim_Semilleros
- ✅ Tabla confiable con 20 semilleros DAGRD
- ✅ Distribuidos en 9 comunas
- ✅ Columnas: N°, Semillero, Comuna, Comuna_Nombre, Barrio_Organización
- ✅ Integrada en `Modelo_Reporte_Paginas_2026.xlsx` como Hoja 2

#### Nuevas Medidas DAX
- ✅ `Total_Semilleros` (valor: 20)
- ✅ `Semilleros_por_Comuna` (valor: 9)
- ✅ `Semilleros_Activos` (dinámico)
- ✅ `Comuna_Seleccionada_Semilleros` (para slicers)

### 📁 Archivos Nuevos

```
✅ scripts/etl/crear_tabla_semilleros.py
   └─ Crea tabla Dim_Semilleros en Excel
   └─ 20 semilleros con metadatos por comuna

✅ scripts/powerbi/crear_medidas_semilleros.py
   └─ Genera 4 medidas DAX para Semilleros

✅ scripts/dax/medidas_semilleros.dax
   └─ Medidas DAX listas para copiar a Power BI

✅ README.md
   └─ Documentación completa del proyecto

✅ ACCESO_RAPIDO.md
   └─ Guía rápida para usuarios finales

✅ docs/guides/GUIA_AGREGAR_SEMILLEROS_POWERBI.md
   └─ Tutorial paso a paso para Power BI (6 pasos)
```

### 🗑️ Eliminados

```
❌ __pycache__/
❌ .tools/
❌ .github/
❌ Archivos temporales (_tmp_*.py)
```

### 📊 Datos Semilleros

| N° | Semillero | Comuna | Barrio |
|----|-----------|--------|--------|
| 1-5 | IE Fe y Alegría, Embera Dobida, Olaya Herrera, Villatina, El Pesebre | 1-13 | Varios |
| 6-8 | Centro Integrado, IE Ciudadela (x2) | 60 | San Cristóbal |
| 9 | IE Manzanillo | 70 | Altavista |
| 10 | La Isla | 2 | Santa Cruz |
| 11-20 | Moravia Oasis, Palermo, San Cayetano, Álamos, San Nicolas, Campo Valdés, Sevilla, Miranda, Emisora La Cuarta Estación | 4 (9 total) | Aranjuez |

### 🔄 Scripts Movidos

| Script | De | A |
|--------|----|----|
| actualizar_37_satc_final.py | Raíz | scripts/etl/ |
| extraer_consultas_paginas_reporte.py | Raíz | scripts/etl/ |
| extraer_participantes_generales_reporte.py | Raíz | scripts/etl/ |
| extraer_participantes_transaccional_reporte.py | Raíz | scripts/etl/ |
| regenerar_puente_37.py | Raíz | scripts/etl/ |
| analizar_kpis_comunidad.py | Raíz | scripts/qa/ |
| perfil_bloques_comunidad.py | Raíz | scripts/qa/ |
| crear_medidas_satc.py | Raíz | scripts/powerbi/ |
| preparar_modelo_powerbi.py | Raíz | scripts/powerbi/ |

---

## [1.1.0] - 2026-03-18 (Versión anterior: SAT-C estaba incompleto)

### ✅ SAT-C Normalizado a 37
- Completados 37 SAT-C en Dim_SATC
- Normalizados nombres en Hecho_Participacion_General
- Agregada columna `nombre_satc_original` para auditoría
- Validadas 37 SAT-C distintos en datos

### 📊 Medidas SAT-C
- `Total_SATC_Unicos` = 37
- `SATC_Principales` = Activos en datos
- `Actividades_por_SATC` = Conteo
- `Participantes_por_SATC` = Suma
- `Cobertura_SATC_Porcentaje` = Ratio

---

## [1.0.0] - 2026-03-01

### 🚀 Versión Inicial
- Dashboard DAGRD creado
- Estructura de carpetas base
- Scripts de extracción de datos
- Modelo Excel con tablas básicas
- Integración con Power BI (inicial)

---

## 📋 Próximas Versiones Planeadas

### [2.1.0] - (Futuro)
- [ ] Agregar tabla Dim_Comites formal
- [ ] Normalizar Comites (actualmente 7 distintos)
- [ ] Medidas de cobertura SATC + Semilleros + Comites
- [ ] Dashboard de inicio (portada)
- [ ] Drill-down por Comuna

### [2.2.0] - (Futuro)
- [ ] Integración Power BI Service
- [ ] Automatización de refresh diaria
- [ ] RLS (Row Level Security) por Comuna
- [ ] Alertas de anomalías en datos
- [ ] Reportes cronogramas

### [3.0.0] - (Futuro)
- [ ] Migración a SQL Server
- [ ] Data Warehouse DAG
- [ ] BI Avanzado (Análisis Predictivo)
- [ ] Mobile Apps

---

## 📊 Estadísticas de Cambio

| Métrica | Antes | Ahora | Cambio |
|---------|-------|-------|--------|
| Carpetas de scripts | 0 | 4 | +400% |
| Tablas en Excel | 4 | 5 | +1 |
| Semilleros | 0 | 20 | +∞ |
| Medidas DAX | 5 | 9 | +4 |
| Documentos | 0 | 3 | +3 |
| Archivos temporales | N/A | 0 | -100% |

---

## 🎯 Checklist de Actualización

Para actualizar código a v2.0.0:

- [ ] Descargar versión 2.0.0
- [ ] Reemplazar carpeta `scripts/` completa
- [ ] Ejecutar `python scripts/etl/crear_tabla_semilleros.py`
- [ ] Refrescar Power BI (`Ctrl+Shift+R`)
- [ ] Crear relación Dim_Semilleros-Hecho
- [ ] Agregar 4 medidas DAX para Semilleros
- [ ] Crear visuales de Semilleros
- [ ] Validar números (Semilleros=20, Comunas=9)
- [ ] Documentar cambios en PBIX

---

## 📞 Notas Importantes

### Compatibilidad
- ✅ Versión 2.0.0 es **retrocompatible** con versión 1.1.0
- ✅ Todas las medidas SAT-C siguen funcionando
- ✅ No requiere cambios en Power BI existentes
- ✅ Solo agrega nuevas funcionalidades

### Breaking Changes
- ❌ **NINGUNO** - Versión completamente aditiva

### Requisitos
- Python 3.8+
- pandas, openpyxl
- Power BI Desktop (2024+)
- Excel 2019+ o Microsoft 365

---

## 🔗 Referencias

- **Documentation:** [README.md](README.md)
- **Quick Start:** [ACCESO_RAPIDO.md](ACCESO_RAPIDO.md)
- **Power BI Guide:** [docs/guides/GUIA_AGREGAR_SEMILLEROS_POWERBI.md](docs/guides/GUIA_AGREGAR_SEMILLEROS_POWERBI.md)
- **Data:** [data/model/Modelo_Reporte_Paginas_2026.xlsx](data/model/Modelo_Reporte_Paginas_2026.xlsx)

---

**Última actualización:** 2026-03-18  
**Autor:** DAGRD Team  
**Versión actual:** 2.0.0  
**Estado:** ✅ Estable
