# 📊 Dashboard DAGRD - Organización y Documentación

**Última actualización:** 18 de junio de 2026  
**Estado:** ✅ Reorganizado, optimizado y totalmente portátil

Este repositorio contiene el pipeline ETL y el modelo analítico para el tablero de control de gestión de riesgo del **DAGRD**. Ha sido optimizado para ser completamente independiente del entorno local, con configuraciones centralizadas en JSON y un flujo de ejecución sumamente simplificado.

---

## 🚀 Flujo de Trabajo Operativo (Actualización del Tablero)

Para actualizar el tablero con datos nuevos del equipo social, sigue estos 3 simples pasos:

### 1️⃣ Guardar el archivo fuente
Copia el nuevo reporte de Excel en la carpeta:
* `data/source/`
* *Nota: El pipeline busca archivos bajo el patrón `Reporte de actividades equipo social*.xlsx` y procesa el más reciente por fecha de modificación.*

### 2️⃣ Ejecutar el ETL
Abre una terminal PowerShell en la raíz del proyecto y ejecuta:
```powershell
.\scripts\etl\run_etl_simple.ps1
```
* **¿Qué hace este script?**
  1. Lee la configuración de [etl_config.json](scripts/etl/etl_config.json).
  2. Extrae las actividades y simulacros unificándolos.
  3. Ejecuta el script de reparación de Power BI para crear/actualizar catálogos y formatear hojas críticas en Excel de forma que el refresco en Power BI no falle.

### 3️⃣ Refrescar Power BI
Abre el archivo de Power BI Desktop (`.pbix` o `.pbip`) y haz clic en **Refresh** (Actualizar) en la pestaña de inicio o presiona `Ctrl+Shift+R`.

---

## ⚙️ Configuración Centralizada
Toda la lógica de carpetas de origen/destino y nombres de hojas de Excel se controla desde el archivo:
* **[scripts/etl/etl_config.json](scripts/etl/etl_config.json)**

Si en el futuro cambian los nombres de las hojas base (ej. `"Sheet1"`, `"Simulacros"`, `"CAM"`, `"SAT-C"`), **no edites los scripts**, solo actualiza las etiquetas correspondientes en este archivo JSON.

---

## 📁 Estructura de Carpetas Limpia y Organizada

```
Dashboard/
│
├── 📂 data/                    # Datos y modelos
│   ├── source/                 # 📥 Archivos Excel de entrada del Equipo Social
│   ├── model/                  # 📤 Archivos procesados de salida para Power BI
│   │   ├── Modelo_Reporte_Paginas_2026.xlsx      # ⭐ BASE DE DATOS PRINCIPAL DE POWER BI
│   │   ├── Excel_Maestro_PowerBI.xlsx            # Catálogo maestro de comunas/comités
│   │   └── legacy/                               # Archivos antiguos de depuración
│   └── reference/              # Datos de referencia
│
├── 📂 scripts/                 # Automatización y procesamiento
│   ├── etl/                    # 🔄 Pipeline ETL Activo
│   │   ├── etl_config.json                       # ⚙️ Archivo de configuración central
│   │   ├── run_etl_simple.ps1                    # Runner simplificado
│   │   ├── run_etl_full.ps1                      # Runner completo (cierre/apertura de PBI)
│   │   ├── extraer_consultas_paginas_reporte.py  # Script de extracción
│   │   ├── reparar_hojas_modelo_para_powerbi.py  # Script de formateo y reparación
│   │   ├── crear_tabla_semilleros.py              # Semilla oficial de Semilleros
│   │   └── legacy/                               # Scripts antiguos de debug
│   │
│   ├── qa/                     # Control de calidad y validación
│   └── powerbi/                # Scripts para Power BI (medidas, visuales y automatización)
│       └── legacy/             # Scripts antiguos de debug / medidas
│
├── 📂 docs/                    # Documentación
│   ├── core/                   # Documentación principal de análisis
│   ├── guides/                 # Guías de usuario paso a paso
│   │   └── GUIA_PASO_A_PASO_POWERBI_DAGRD.md     # Guía operativa completa
│   └── auditorias/             # 📑 Resultados de auditorías, validaciones e investigaciones previas
│
├── 📂 Tableros/                # Informes y archivos de Power BI (.pbix)
├── 📂 powerbi/                 # Estructura TMDL y metadatos de Power BI Desktop
├── 🔵 run_pipeline.py          # Script de integración con backend local (LLM y AutoVis)
├── 📋 .gitignore               # Configuración de exclusiones de Git
└── 📦 requirements.txt         # Dependencias Python
```

---

## 🛠️ Instalación y Requisitos

### Requisitos Previos
* Python 3.8+ (64-bit recomendado)
* Power BI Desktop

### Instalación Rápida
1. Abre tu terminal en la raíz del proyecto.
2. Crea el entorno virtual si no existe:
   ```bash
   python -m venv .venv
   ```
3. Activa el entorno virtual:
   * **PowerShell:** `.\.venv\Scripts\Activate.ps1`
   * **CMD:** `.\.venv\Scripts\activate.bat`
4. Instalar dependencias requeridas:
   ```bash
   pip install -r requirements.txt
   ```

---

## ❓ Preguntas Frecuentes y Soporte

### P: Se agregaron nuevos comités en el consolidado y no aparecen en Power BI.
* **R:** Asegúrate de que el archivo del consolidado esté en `data/model/CONSOLIDADO COMITES COMISIONES 03-2026.xlsx`. Al correr `run_etl_simple.ps1`, el script regenera el CSV `Dim_Comites_Comisiones_2026.csv` que lee Power BI automáticamente.

### P: El pipeline falla con error de permisos o archivos bloqueados.
* **R:** Esto ocurre si tienes el archivo de salida `Modelo_Reporte_Paginas_2026.xlsx` abierto en Excel. Ciérralo y vuelve a ejecutar el script. Para evitar bloqueos con Power BI, puedes usar `run_etl_full.ps1 -ClosePowerBI` el cual cierra Power BI Desktop antes de iniciar y lo vuelve a abrir al terminar.

### P: Modifiqué o agregué zonas en el reporte CAM y no se muestran con su comuna en Power BI.
* **R:** La relación entre las zonas CAM y las comunas de Medellín se maneja a través de relaciones virtuales en las medidas de Power BI. Si agregas zonas nuevas en el archivo fuente, deberás mapearlas en la medida `Empresas_Detalle` y afines dentro del archivo local `_Medidas.tmdl` o en la vista de modelado de Power BI.

---

**Mantenido por:** Equipo Técnico DAGRD  
**Versión del Proyecto:** 3.0.0 (Portátil y Configurable)
