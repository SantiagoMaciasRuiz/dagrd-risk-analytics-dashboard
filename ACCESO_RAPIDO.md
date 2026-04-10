# 🚀 ACCESO RÁPIDO - Dashboard DAGRD

**Estado:** ✅ Organizado | 📊 Semilleros Agregados | 🔄 Listo para usar

---

## ⭐ ARCHIVOS MÁS USADOS

### 📊 Datos Maestro
- **Excel Principal:** `data/model/Modelo_Reporte_Paginas_2026.xlsx`
  - Dim_Semilleros (NUEVO - 20 semilleros)
  - Dim_SATC (37 SAT-C)
  - Hecho_Participacion_General (3,502 registros)

### 🐍 Scripts para Ejecutar
```
✅ Crear Semilleros:
   python scripts/etl/crear_tabla_semilleros.py

✅ Validar datos:
   python scripts/qa/analizar_kpis_comunidad.py

✅ Generar medidas DAX:
   python scripts/powerbi/crear_medidas_semilleros.py
```

### 📐 Medidas DAX Generadas
- `scripts/dax/medidas_semilleros.dax` (4 medidas nuevas)
- `scripts/dax/medidas_satc.dax` (5 medidas existentes)

### 📖 Documentación
- `README.md` - Estructura completa
- `docs/guides/GUIA_PASO_A_PASO_POWERBI_DAGRD.md` - Tutoriales
- `docs/core/` - Análisis detallados
- `docs/core/TABLA_DAX_VS_EXCEL_BUSQUEDA_2026.md` - Tabla para validar cada medida DAX en el Excel fuente

### ✅ Validación DAX contra Excel (nuevo)
- Tabla completa (CSV): `data/reference/tabla_dax_vs_excel_busqueda_2026.csv`
- Versión legible (MD): `docs/core/TABLA_DAX_VS_EXCEL_BUSQUEDA_2026.md`
- Generador automático: `scripts/qa/generar_tabla_dax_excel_busqueda.py`

---

## 📋 CHECKLIST DE CONFIGURACIÓN

### Primer Uso
- [ ] Activar `.venv` → `.\.venv\Scripts\Activate.ps1`
- [ ] Ejecutar `crear_tabla_semilleros.py`
- [ ] Abrir Power BI Desktop
- [ ] Refrescar datos (Ctrl+Shift+R)
- [ ] Agregar medidas DAX desde `scripts/dax/`
- [ ] Crear visuales de Semilleros

### Actualización Mensual
- [ ] `python scripts/etl/crear_tabla_semilleros.py` (si hay cambios)
- [ ] `python scripts/qa/analizar_kpis_comunidad.py` (validar)
- [ ] Refrescar Power BI
- [ ] Verificar tarjetas y gráficos

---

## 📊 DATOS DE SEMILLEROS

**20 Semilleros en 9 Comunas**

```
Comunas con Semilleros:
├─ Comuna 1 (Popular): 1 semillero
├─ Comuna 2 (Santa Cruz): 1 semillero
├─ Comuna 4 (Aranjuez): 9 semilleros ★ Más activos
├─ Comuna 7 (Robledo): 1 semillero
├─ Comuna 8 (Villa Hermosa): 1 semillero
├─ Comuna 13 (San Javier): 1 semillero
├─ Comuna 60 (San Cristóbal): 3 semilleros
├─ Comuna 70 (Altavista): 1 semillero
└─ Comuna 80 (San Antonio): 1 semillero
```

---

## 🔗 TABLA DE SEMILLEROS (COMPLETA)

| N° | Semillero | Comuna | Barrio/Organización |
|----|-----------|--------|-------------------|
| 1 | Semillero IE Fe y Alegría | 1 | Popular - IE Fe y Alegría |
| 2 | Comunidad Embera Dobida | 80 | San Antonio de Prado |
| 3 | Olaya Herrera | 7 | Olaya Herrera - Comisión Riesgo |
| 4 | Villatina | 8 | Villatina |
| 5 | El Pesebre | 13 | El Pesebre - Mesa Riesgo |
| 6 | Centro Integrado San Cristóbal | 60 | Centralidad - Unidad discapacidad |
| 7 | IE Ciudadela Nuevo Occidente (Pedregal) | 60 | Pedregal Bajo |
| 8 | IE Ciudadela Nuevo Occidente | 60 | Nuevo Occidente |
| 9 | IE Manzanillo | 70 | Vereda San José Manzanillo |
| 10 | La Isla | 2 | La Isla - Corporación Progreso |
| 11 | Moravia Oasis | 4 | Jac Moravia Oasis Tropical |
| 12 | Moravia El Bosque | 4 | Jac Moravia El Bosque |
| 13 | Palermo | 4 | Jac Palermo |
| 14 | San Cayetano | 4 | Jac San Cayetano |
| 15 | Álamos | 4 | Jac Álamos |
| 16 | San Nicolas | 4 | Jac San Nicolas |
| 17 | Campo Valdés El Calvario | 4 | Jac Campo Valdés |
| 18 | Sevilla | 4 | Jac Sevilla |
| 19 | Miranda | 4 | Jac Miranda |
| 20 | Emisora La Cuarta Estación | 4 | San Pedro - Emisora |

---

## 🎯 MEDIDAS DAX LISTOS

### Semilleros (NUEVA)
```dax
Total_Semilleros = DISTINCTCOUNT(Dim_Semilleros[Semillero]) → 20

Semilleros_por_Comuna = DISTINCTCOUNT(Dim_Semilleros[Comuna]) → 9

Semilleros_Activos = CALCULATE(DISTINCTCOUNT(...), bloque="Semilleros")

Comuna_Seleccionada = VALUES(Dim_Semilleros[Comuna_Nombre])
```

### SAT-C (Existente)
```dax
Total_SATC_Unicos = 37
SATC_Principales = Activos en datos
Actividades_por_SATC = Conteo
Participantes_por_SATC = Suma
Cobertura_SATC_Porcentaje = Ratio
```

---

## 📂 ESTRUCTURA FINAL

```
Dashboard/
├── data/
│   └── model/ ← DATOS MAESTRO
├── scripts/
│   ├── etl/ ← CREAR/ACTUALIZAR DATOS
│   ├── qa/ ← VALIDAR DATOS
│   ├── powerbi/ ← GENERAR MEDIDAS
│   └── dax/ ← MEDIDAS DAX
├── docs/ ← DOCUMENTACIÓN
├── powerbi/ ← CONFIG POWER BI
├── README.md ← ESTE DOCUMENTO
└── CHANGELOG.md ← CAMBIOS
```

---

## ⚡ COMANDO DE INICIO (COPIA Y PEGA)

```powershell
# Activar entorno y crear tabla Semilleros
.\.venv\Scripts\Activate.ps1
python scripts/etl/crear_tabla_semilleros.py
python scripts/qa/analizar_kpis_comunidad.py
```

---

## 📞 REFERENCIA RÁPIDA

| Necesito... | Archivo | Comando |
|-----------|---------|---------|
| Agregar semilleros | `scripts/etl/crear_tabla_semilleros.py` | `python scripts/etl/crear_tabla_semilleros.py` |
| Validar datos | `scripts/qa/analizar_kpis_comunidad.py` | `python scripts/qa/analizar_kpis_comunidad.py` |
| Medidas Semilleros | `scripts/dax/medidas_semilleros.dax` | Copiar al Power BI |
| Estructurar Power BI | `scripts/powerbi/crear_medidas_semilleros.py` | `python scripts/powerbi/crear_medidas_semilleros.py` |
| Guía Power BI | `docs/guides/GUIA_PASO_A_PASO_POWERBI_DAGRD.md` | Leer archivo |

---

**Última actualización:** 2026-03-18  
**Autor:** DAGRD Automation  
**Estado:** ✅ Listo
