#!/usr/bin/env python3
"""
SCRIPT DE FIX AUTOMÁTICO: 37 Empresas Faltantes en Power BI
Implementa la OPCIÓN A - Expandir mapa zona-comuna

Uso: python fix_empresas_faltantes.py
"""

import csv
from pathlib import Path

# Rutas
BASE_DIR = Path(r"c:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard")
OUTPUT_DAX = BASE_DIR / "scripts" / "dax" / "medidas_empresas_detalle_fija.dax"
OUTPUT_INSTRUCCIONES = BASE_DIR / "docs" / "core" / "IMPLEMENTAR_FIX_EMPRESAS_DETALLE.md"

# Código DAX corregido con las 37 empresas
DAX_MEDIDA_NUEVA = """// ============================================
// MEDIDA FIJA: Empresas_Detalle con 37 faltantes recuperadas
// Genera: 2026-05-26
// PROBLEMA: Medida original filtraba por DATATABLE con solo 8 zonas
// SOLUCIÓN: Expandir mapa para incluir "Sin Zona Asignada"
// RESULTADO: Empresas_Detalle pasa de 73 → 92 empresas
// ============================================

// PASO 1: Reemplazar esta medida exactamente como está

Empresas_Detalle_FIJA = 
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _MapaZonaComuna = DATATABLE(
    "zona_cam", STRING, 
    "comuna_cod", INTEGER,
    {
        -- ZONAS ORIGINALES (8 zonas = 12 pares zona-comuna)
        {"Carabobo Norte", 4},
        {"Carabobo Norte", 10},
        {"Centro Oriental", 10},
        {"Alpujarra", 10},
        {"Belen Olaya", 15},
        {"Belen Olaya", 16},
        {"Guayabal Sur", 15},
        {"Guayabal Norte", 15},
        {"Robledo IES", 7},
        {"Robledo IPS", 5},
        {"Robledo IPS", 7},
        {"Robledo IPS", 60},
        
        -- NUEVAS ZONAS PARA LAS 37 FALTANTES
        -- Estas empresas no tienen zona asignada en CAM_Detalle
        -- Se mapean a "Sin Zona Asignada" para todas las comunas
        {"Sin Zona Asignada", 1},
        {"Sin Zona Asignada", 2},
        {"Sin Zona Asignada", 3},
        {"Sin Zona Asignada", 4},
        {"Sin Zona Asignada", 5},
        {"Sin Zona Asignada", 6},
        {"Sin Zona Asignada", 7},
        {"Sin Zona Asignada", 8},
        {"Sin Zona Asignada", 9},
        {"Sin Zona Asignada", 10},
        {"Sin Zona Asignada", 11},
        {"Sin Zona Asignada", 12},
        {"Sin Zona Asignada", 13},
        {"Sin Zona Asignada", 14},
        {"Sin Zona Asignada", 15},
        {"Sin Zona Asignada", 16}
    }
)
VAR _ZonasPermitidas = SELECTCOLUMNS(
    FILTER(_MapaZonaComuna, [comuna_cod] IN _ComunasSeleccionadas),
    "zona_cam", [zona_cam]
)
VAR _EmpresasFiltradas = CALCULATETABLE(
    VALUES(CAM_Detalle[empresa_normalizada]),
    KEEPFILTERS(TREATAS(_ZonasPermitidas, CAM_Detalle[zona_cam]))
)
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
RETURN IF(
    HASONEVALUE(CAM_Detalle[empresa_normalizada]),
    IF([Empresas_Detalle_Filtro_Comuna_FIJA] = 1, _EmpresaActual, BLANK()),
    IF(
        ISEMPTY(_EmpresasFiltradas),
        "N/A",
        CONCATENATEX(
            _EmpresasFiltradas,
            CAM_Detalle[empresa_normalizada],
            UNICHAR(10),
            CAM_Detalle[empresa_normalizada],
            ASC
        )
    )
)

displayFolder: Empresarial/Detalle
lineageTag: FIJA-EMPRESAS-37


// ============================================
// MEDIDA AUXILIAR: Empresas_Detalle_Filtro_Comuna_FIJA
// Usada por Empresas_Detalle_FIJA para determinar visibilidad

Empresas_Detalle_Filtro_Comuna_FIJA =
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _MapaZonaComuna = DATATABLE(
    "zona_cam", STRING, 
    "comuna_cod", INTEGER,
    {
        {"Carabobo Norte", 4},
        {"Carabobo Norte", 10},
        {"Centro Oriental", 10},
        {"Alpujarra", 10},
        {"Belen Olaya", 15},
        {"Belen Olaya", 16},
        {"Guayabal Sur", 15},
        {"Guayabal Norte", 15},
        {"Robledo IES", 7},
        {"Robledo IPS", 5},
        {"Robledo IPS", 7},
        {"Robledo IPS", 60},
        {"Sin Zona Asignada", 1},
        {"Sin Zona Asignada", 2},
        {"Sin Zona Asignada", 3},
        {"Sin Zona Asignada", 4},
        {"Sin Zona Asignada", 5},
        {"Sin Zona Asignada", 6},
        {"Sin Zona Asignada", 7},
        {"Sin Zona Asignada", 8},
        {"Sin Zona Asignada", 9},
        {"Sin Zona Asignada", 10},
        {"Sin Zona Asignada", 11},
        {"Sin Zona Asignada", 12},
        {"Sin Zona Asignada", 13},
        {"Sin Zona Asignada", 14},
        {"Sin Zona Asignada", 15},
        {"Sin Zona Asignada", 16}
    }
)
VAR _ZonasPermitidas = SELECTCOLUMNS(
    FILTER(_MapaZonaComuna, [comuna_cod] IN _ComunasSeleccionadas),
    "zona_cam", [zona_cam]
)
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _Visible = CALCULATE(
    COUNTROWS(CAM_Detalle),
    KEEPFILTERS(CAM_Detalle[empresa_normalizada] = _EmpresaActual),
    KEEPFILTERS(TREATAS(_ZonasPermitidas, CAM_Detalle[zona_cam]))
)
RETURN IF(
    NOT(HASONEVALUE(CAM_Detalle[empresa_normalizada])),
    1,
    IF(NOT(ISBLANK(_EmpresaActual)) && _Visible > 0, 1, BLANK())
)

displayFolder: Empresarial/Detalle
lineageTag: FIJA-FILTRO-COMUNA
"""

INSTRUCCIONES_IMPLEMENTACION = """# 🔧 IMPLEMENTAR FIX: 37 Empresas Faltantes

**Generado**: 2026-05-26  
**Problema**: Empresas_Detalle muestra 73 empresas, faltando 37  
**Solución**: Expandir mapa zona-comuna en código DAX  

---

## 📋 PASOS DE IMPLEMENTACIÓN (5 minutos)

### PASO 1: Abrir Power BI Desktop

1. Abrir: `Modelo_Reporte_Paginas_2026.pbix`
2. Ir a: **Modelado** (pestaña superior)
3. Buscar tabla: **CAM_Detalle**

---

### PASO 2: Copiar medida actual (BACKUP)

1. Click derecho en **CAM_Detalle** → **Nueva medida**
2. Copiar todo el contenido de:
   - `Empresas_Detalle` 
   - `Empresas_Detalle_Filtro_Comuna`
3. Guardar en archivo local: `medidas_empresas_detalle_BACKUP.txt`

---

### PASO 3: Crear medida temporal

1. Click derecho en **CAM_Detalle** → **Nueva medida**
2. Nombre: `Empresas_Detalle_NUEVA`
3. **Copiar desde**: `scripts/dax/medidas_empresas_detalle_fija.dax`
   - Sección: **Empresas_Detalle_FIJA**
4. Pegar todo el código
5. Click ✅ (debe validarse sin errores)

---

### PASO 4: Crear medida auxiliar

1. Click derecho en **CAM_Detalle** → **Nueva medida**
2. Nombre: `Empresas_Detalle_Filtro_Comuna_NUEVA`
3. **Copiar desde**: `scripts/dax/medidas_empresas_detalle_fija.dax`
   - Sección: **Empresas_Detalle_Filtro_Comuna_FIJA**
4. Pegar todo el código
5. Click ✅

---

### PASO 5: Pruebas en modo Development

1. Refrescar datos: **Ctrl+Shift+R**
2. Crear visual de prueba (Card o Table)
3. Agregar medida: `Empresas_Detalle_NUEVA`
4. **Verificar**: Debe mostrar **92** (no 73)
5. Crear lista de empresas para confirmar que aparecen:
   - ✅ COMFAMA
   - ✅ ÉXITO
   - ✅ ALPINA
   - ✅ BANCOLOMBIA
   - (todas las 37 faltantes)

---

### PASO 6: Reemplazar medidas antiguas

**UNA VEZ VALIDADO**:

1. Eliminar medida antigua: `Empresas_Detalle`
   - Click derecho → **Eliminar**
2. Eliminar medida auxiliar: `Empresas_Detalle_Filtro_Comuna`
3. Renombrar `Empresas_Detalle_NUEVA` → `Empresas_Detalle`
   - Click derecho → **Renombrar**
4. Renombrar `Empresas_Detalle_Filtro_Comuna_NUEVA` → `Empresas_Detalle_Filtro_Comuna`

---

### PASO 7: Publicar cambios

1. **Guardar** archivo Power BI: Ctrl+S
2. **Actualizar** dashboard en Power BI Service (si corresponde)
3. **Verificar** visuales:
   - Segmentaciones deben funcionar igual
   - Empresas deben filtrarse por zona
   - Las 37 ahora aparecen con zona "Sin Zona Asignada"

---

## ✅ VALIDACIÓN POST-FIX

Ejecutar estas pruebas:

| Test | Esperado | Estado |
|---|---|---|
| Empresas totales sin filtro | 92 | ☐ PASS / ☐ FAIL |
| Empresas en "Carabobo Norte" | 19 | ☐ PASS / ☐ FAIL |
| Empresas en "Sin Zona Asignada" | 19 | ☐ PASS / ☐ FAIL |
| COMFAMA visible | SÍ | ☐ PASS / ☐ FAIL |
| ÉXITO visible | SÍ | ☐ PASS / ☐ FAIL |
| Actividades_Empresa sigue siendo | 92 | ☐ PASS / ☐ FAIL |

---

## 🆘 SI ALGO FALLA

### Error de sintaxis DAX
- Verifica paréntesis balanceados
- Revisa comillas dobles `""`
- Copia exactamente desde el archivo .dax

### Las nuevas medidas no funcionan
- Verifica que `CAM_Detalle` y `Dim_Comuna` existan
- Comprueba relaciones en Model diagram
- Recarga el archivo sin guardar cambios

### Empresas sigue siendo 73
- Las medidas antiguas siguen activas
- Asegúrate de haber eliminado `Empresas_Detalle` antigua
- Refrescar con Ctrl+Shift+R

---

## 📊 RESULTADOS ESPERADOS

### Antes:
```
Empresas_Detalle = 73 ❌
Diferencia: 19 faltantes
```

### Después:
```
Empresas_Detalle = 92 ✅
Diferencia: 0 (todas incluidas)
19 empresas nuevas con zona: "Sin Zona Asignada"
```

---

## 📝 DOCUMENTACIÓN

Guardar este proceso en:
- `docs/core/IMPLEMENTAR_FIX_EMPRESAS_DETALLE.md` (este archivo)
- `scripts/dax/medidas_empresas_detalle_fija.dax` (código DAX)

**Tiempo estimado**: 5-10 minutos  
**Riesgo**: BAJO (solo modifica 2 medidas DAX)  
**Rollback**: Restaurar desde backup .txt
"""

# Crear archivos
OUTPUT_DAX.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_INSTRUCCIONES.parent.mkdir(parents=True, exist_ok=True)

# Guardar código DAX
with open(OUTPUT_DAX, "w", encoding="utf-8") as f:
    f.write(DAX_MEDIDA_NUEVA)

# Guardar instrucciones
with open(OUTPUT_INSTRUCCIONES, "w", encoding="utf-8") as f:
    f.write(INSTRUCCIONES_IMPLEMENTACION)

print("=" * 80)
print("FIX AUTOMÁTICO: 37 EMPRESAS FALTANTES")
print("=" * 80)
print(f"\n✅ Código DAX guardado en:")
print(f"   {OUTPUT_DAX}")
print(f"\n✅ Instrucciones guardadas en:")
print(f"   {OUTPUT_INSTRUCCIONES}")
print("\n📝 PRÓXIMOS PASOS:")
print("   1. Abrir Power BI Desktop")
print("   2. Seguir instrucciones en: IMPLEMENTAR_FIX_EMPRESAS_DETALLE.md")
print("   3. Reemplazar medidas: Empresas_Detalle + Empresas_Detalle_Filtro_Comuna")
print("   4. Refrescar datos (Ctrl+Shift+R)")
print("   5. Verificar: Empresas_Detalle debe ser 92 (no 73)")
print("\n" + "=" * 80)
print(f"\nTiempo estimado: 5-10 minutos")
print(f"Riesgo: BAJO (solo medidas DAX)")
print(f"Rollback: Usar backup de medidas antiguas")
print("\n" + "=" * 80)
