# 🔍 AUDITORÍA DE MEDIDAS "EMPRESAS" - VALIDACIÓN PARA UPDATE

**Fecha**: 27 de mayo de 2026  
**Conexión**: Power BI Desktop localhost:54211  
**Total Medidas Analizadas**: 16  
**Estado Crítico**: 🔴 4 MEDIDAS CON PROBLEMAS CRÍTICOS  

---

## 📋 TABLA RESUMEN - MEDIDAS RELACIONADAS A "EMPRESAS"

| # | **Medida** | **DAX** | **Tablas/Columnas** | **Usa CAM_Detalle?** | **Usa Hecho_Part.General?** | **Status** | **Recomendación** |
|---|-----------|---------|-------------------|:--:|:--:|:--:|-------------|
| 1 | **Empresas_Detalle** ⭐⭐⭐ | `VAR _MapaZonaComuna = DATATABLE(...) VAR _ZonasPermitidas = SELECTCOLUMNS(FILTER(_MapaZonaComuna, [comuna_cod] IN _ComunasSeleccionadas), "zona_cam", [zona_cam])` | `CAM_Detalle[empresa_normalizada]`, `CAM_Detalle[zona_cam]`, `Dim_Comuna[comuna_cod]` | ✅ SÍ | ❌ NO | 🔴 **CRÍTICO** | **URGENTE**: Reemplazar DATATABLE hardcodeado con consulta dinámica a tabla de control. Mapeo zona-comuna es frágil y excluye empresas sin zona asignada. |
| 2 | **Actividades_Empresa** ⭐⭐⭐ | `VAR _v = MAX(CAM_Control[empresas_unicas_global]) RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))` | `CAM_Control[empresas_unicas_global]` | ✅ INDIRECTO | ❌ NO | ⚠️ **ACTUALIZAR** | Valida post-fix de 37 empresas. Verificar que CAM_Control refleje 92 empresas únicas (no 73 filtradas). Agregar validación de período (Año/Mes). |
| 3 | **Participantes_Empresa** ⭐⭐⭐ | `VAR _v = CALCULATE(SUM(Hecho_Participacion_General[participantes]), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "Empresas") RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))` | `Hecho_Participacion_General[participantes]`, `Hecho_Participacion_General[bloque_empresarial]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ✅ SÍ | ✅ **OK** | **Validar**: Confirmar que Hecho_Participacion_General incluye registros con `bloque_empresarial = "Empresas"` para las 37 empresas. Agregar integración Año/Mes si está disponible. |
| 4 | **Lista_Nombres_Empresas_Filtradas** ⭐ | `VAR _Nombres = CALCULATETABLE(VALUES(Hecho_Participacion_General[publico_empresarial]),...) VAR _Lista = CONCATENATEX(FILTER(_Nombres, NOT(ISBLANK(...)) && TRIM(...) <> ""),...)` | `Hecho_Participacion_General[publico_empresarial]`, `Hecho_Participacion_General[bloque_empresarial]`, `Hecho_Participacion_General[seccion_tablero]` | ❌ NO | ✅ SÍ | ⚠️ **ACTUALIZAR** | Depende de datos en Hecho_Participacion_General. Si 37 empresas no tienen registros en esa tabla, no aparecerán en lista. Usar `CONCATENATEX` con `DISTINCT` si hay duplicados. |
| 5 | **Empresas_Detalle_Filtro_Comuna** | `VAR _Visible = CALCULATE(COUNTROWS(CAM_Detalle), KEEPFILTERS(CAM_Detalle[empresa_normalizada] = _EmpresaActual), KEEPFILTERS(TREATAS(_ZonasPermitidas, CAM_Detalle[zona_cam])))` | `CAM_Detalle[empresa_normalizada]`, `CAM_Detalle[zona_cam]`, `Dim_Comuna[comuna_cod]` | ✅ SÍ | ❌ NO | 🔴 **CRÍTICO** | **URGENTE**: Lógica de filtro basada en mapa frágil de zona-comuna. Usar tabla de control dinámica. Validar que todas las 92 empresas estén mapeadas. |
| 6 | **Actividades_CAM** | `VAR _v = MAX(CAM_Control[cam_activos_total]) RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))` | `CAM_Control[cam_activos_total]` | ✅ INDIRECTO | ❌ NO | ✅ **OK** | Verificar que CAM_Control esté actualizado con nuevos datos. Sincronizar con nueva estructura Año/Mes si aplica. |
| 7 | **Participantes_CAM** | `"N/A"` | NINGUNA (Hardcoded) | ❌ NO | ❌ NO | 🔴 **CRÍTICO** | **DUMMY MEDIDA**: Retorna "N/A" siempre. Implementar lógica real: `CALCULATE(SUM(Hecho_Participacion_General[participantes]), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "CAM")` |
| 8 | **Actividades_PropiedadHorizontal** | `VAR _v = CALCULATE(COUNTROWS(Hecho_Participacion_General), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "Propiedades Horizontales")` | `Hecho_Participacion_General[bloque_empresarial]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ✅ SÍ | ✅ **OK** | Lógica correcta. Integrar con filtro Año/Mes si está disponible. |
| 9 | **Participantes_PropiedadHorizontal** | `VAR _v = CALCULATE(SUM(Hecho_Participacion_General[participantes]), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "Propiedades Horizontales")` | `Hecho_Participacion_General[participantes]`, `Hecho_Participacion_General[bloque_empresarial]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ✅ SÍ | ✅ **OK** | Lógica correcta. Integrar con filtro Año/Mes si está disponible. |
| 10 | **Actividades_PlanesAyudaMutua** | `1` | NINGUNA (Hardcoded) | ❌ NO | ❌ NO | 🔴 **CRÍTICO** | **DUMMY MEDIDA**: Retorna "1" siempre. Implementar: `CALCULATE(COUNTROWS(Hecho_Participacion_General), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "Planes de ayuda mutua/Acuerdo de voluntades")` |
| 11 | **Participantes_PlanesAyudaMutua** | `VAR _v = CALCULATE(SUM(Hecho_Participacion_General[participantes]), Dim_Seccion[seccion_tablero] = "Empresarial", Hecho_Participacion_General[bloque_empresarial] = "Planes de ayuda mutua/Acuerdo de voluntades")` | `Hecho_Participacion_General[participantes]`, `Hecho_Participacion_General[bloque_empresarial]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ✅ SÍ | ✅ **OK** | Lógica correcta. Integrar con filtro Año/Mes si está disponible. |
| 12 | **GenF_Empresarial_Actividades** | `CALCULATE([GenF_Total_Actividades], Dim_Seccion[seccion_tablero] = "Empresarial")` | `[GenF_Total_Actividades]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ❌ NO | ✅ **OK** | Medida derivada. Valida correctamente la vista Empresarial. |
| 13 | **GenF_Empresarial_Participaciones** | `CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Empresarial")` | `[GenF_Total_Participaciones]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ❌ NO | ✅ **OK** | Medida derivada. Valida correctamente la vista Empresarial. |
| 14 | **GenF_Empresarial_Impacto** | `CALCULATE([Base_Impacto_Indirecto], Dim_Seccion[seccion_tablero] = "Empresarial")` | `[Base_Impacto_Indirecto]`, `Dim_Seccion[seccion_tablero]` | ❌ NO | ❌ NO | ✅ **OK** | Medida derivada. Valida correctamente la vista Empresarial. |
| 15 | **Sim_Empresarial_Registros** | `CALCULATE([Base_Simulacros], Hecho_Simulacros[sector_tablero] = "Empresarial")` | `[Base_Simulacros]`, `Hecho_Simulacros[sector_tablero]` | ❌ NO | ❌ NO | ✅ **OK** | Medida derivada. Valida correctamente sector empresarial en simulacros. |
| 16 | **Sim_Empresarial_Personas** | `CALCULATE([Base_Simulacros_Personas], Hecho_Simulacros[sector_tablero] = "Empresarial")` | `[Base_Simulacros_Personas]`, `Hecho_Simulacros[sector_tablero]` | ❌ NO | ❌ NO | ✅ **OK** | Medida derivada. Valida correctamente sector empresarial en simulacros. |

---

## 🔴 MEDIDAS CON PROBLEMAS CRÍTICOS

### 1️⃣ **EMPRESAS_DETALLE** (Prioridad: ⭐⭐⭐)
**Estado**: 🔴 CRÍTICO - Causa principal de exclusión de 37 empresas

**Problema Técnico**:
```dax
VAR _MapaZonaComuna = DATATABLE(
    "zona_cam", STRING, "comuna_cod", INTEGER,
    {
        {"Carabobo Norte", 4}, {"Carabobo Norte", 10},
        {"Centro Oriental", 10}, {"Alpujarra", 10},
        {"Belen Olaya", 15}, {"Belen Olaya", 16},
        {"Guayabal Sur", 15}, {"Guayabal Norte", 15},
        {"Robledo IES", 7}, {"Robledo IPS", 5},
        {"Robledo IPS", 7}, {"Robledo IPS", 60}
    }
)
```
- Mapa **hardcodeado** solo tiene 8 zonas CAM
- Las 37 empresas NO están en CAM_Detalle[zona_cam]
- Se excluyen todas las empresas que no coinciden con estas 8 zonas

**Impacto**: 
- Mostraba 19 empresas visibles de 92 totales
- 73 empresas están en CAM_Detalle pero NO en el mapa

**Solución**:
```dax
-- OPCIÓN A: Usar tabla de control dinámmica
VAR _MapaZonaComuna = 
    CALCULATETABLE(
        VALUES(CAM_Zonas[zona_cam]),  -- Nueva tabla con mapeo actual
        KEEPFILTERS(CAM_Zonas[activo] = TRUE)
    )

-- OPCIÓN B: Remover filtro por zona si no es necesario
VAR _EmpresasFiltradas =
    CALCULATETABLE(
        VALUES(CAM_Detalle[empresa_normalizada])
    )
```

---

### 2️⃣ **EMPRESAS_DETALLE_FILTRO_COMUNA** (Prioridad: ⭐⭐⭐)
**Estado**: 🔴 CRÍTICO - Lógica de filtro frágil

**Problema**:
- Depende del mismo DATATABLE frágil
- Usa TREATAS para mapear zonas a comunas (método frágil)
- Excluye empresas por mapeo incorrecto

**Solución**:
```dax
-- Usar tabla de relaciones dinámmica
VAR _Visible =
    CALCULATE(
        COUNTROWS(CAM_Detalle),
        KEEPFILTERS(CAM_Detalle[empresa_normalizada] = _EmpresaActual),
        KEEPFILTERS(CAM_Detalle[activo] = TRUE)
    )
```

---

### 3️⃣ **PARTICIPANTES_CAM** (Prioridad: ⭐)
**Estado**: 🔴 CRÍTICO - Medida DUMMY

**Problema**:
```dax
"N/A"  -- Solo retorna texto
```

**Solución**:
```dax
VAR _v = CALCULATE(
    SUM(Hecho_Participacion_General[participantes]), 
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "CAM"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

---

### 4️⃣ **ACTIVIDADES_PLANESAYUDAMUTUA** (Prioridad: ⭐)
**Estado**: 🔴 CRÍTICO - Medida DUMMY

**Problema**:
```dax
1  -- Solo retorna número 1
```

**Solución**:
```dax
VAR _v = CALCULATE(
    COUNTROWS(Hecho_Participacion_General), 
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Planes de ayuda mutua/Acuerdo de voluntades"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

---

## ⚠️ MEDIDAS CON CAMBIOS RECOMENDADOS

### **ACTIVIDADES_EMPRESA** (Prioridad: ⭐⭐⭐)
**Estado**: ⚠️ ACTUALIZAR

**Verificación Requerida**:
- Confirmar que `CAM_Control[empresas_unicas_global]` = 92 (no 73)
- Validar post-fix de las 37 empresas faltantes

**Si es necesario actualizar**:
```dax
-- Contar directamente desde CAM_Detalle
VAR _v = CALCULATE(
    DISTINCTCOUNT(CAM_Detalle[empresa_normalizada]),
    CAM_Detalle[activo] = TRUE
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

### **LISTA_NOMBRES_EMPRESAS_FILTRADAS**
**Estado**: ⚠️ ACTUALIZAR

**Verificación Requerida**:
- Confirmar que Hecho_Participacion_General tiene registros para todas 92 empresas
- Si falta empresas, usar fuente alternativa (CAM_Detalle)

**Mejora**:
```dax
-- Si no hay datos en Hecho_Participacion_General, usar CAM_Detalle
VAR _Nombres_HPG =
    CALCULATETABLE(
        VALUES(Hecho_Participacion_General[publico_empresarial]),
        Hecho_Participacion_General[bloque_empresarial] = "Empresas"
    )
VAR _Nombres_CAM =
    IF(ISEMPTY(_Nombres_HPG),
        VALUES(CAM_Detalle[empresa_normalizada]),
        _Nombres_HPG
    )
```

---

## ✅ MEDIDAS OK (Sin cambios requeridos)

| Medida | Justificación |
|--------|---------------|
| **Participantes_Empresa** | ✅ Lógica correcta usando Hecho_Participacion_General |
| **Actividades_PropiedadHorizontal** | ✅ Lógica correcta |
| **Participantes_PropiedadHorizontal** | ✅ Lógica correcta |
| **Actividades_CAM** | ✅ Depende de CAM_Control (verificar actualización) |
| **GenF_Empresarial_Actividades** | ✅ Derivada de medida base válida |
| **GenF_Empresarial_Participaciones** | ✅ Derivada de medida base válida |
| **GenF_Empresarial_Impacto** | ✅ Derivada de medida base válida |
| **Sim_Empresarial_Registros** | ✅ Derivada de medida base válida |
| **Sim_Empresarial_Personas** | ✅ Derivada de medida base válida |
| **Participantes_PlanesAyudaMutua** | ✅ Lógica correcta |

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### **FASE 1: CRÍTICA (TODAY)**
1. ✅ **Empresas_Detalle** → Reemplazar DATATABLE hardcodeado
2. ✅ **Empresas_Detalle_Filtro_Comuna** → Usar relaciones dinámicas
3. ✅ **Participantes_CAM** → Implementar lógica real
4. ✅ **Actividades_PlanesAyudaMutua** → Implementar lógica real

### **FASE 2: VALIDACIÓN (TODAY)**
5. ✅ Verificar CAM_Control[empresas_unicas_global] = 92
6. ✅ Validar Hecho_Participacion_General tiene 37 empresas nuevas
7. ✅ Confirmar filtros Año/Mes funcionan correctamente

### **FASE 3: OPTIMIZACIÓN (MAÑANA)**
8. ✅ Integrar medidas con nuevo modelo Año/Mes
9. ✅ Crear tabla de control dinámico zona-comuna
10. ✅ Testing exhaustivo con 92 empresas

---

## 📊 DEPENDENCIAS DE TABLAS

| Tabla | Medidas que la usan | Estado de Actualización |
|-------|-------------------|------------------------|
| **CAM_Detalle** | Empresas_Detalle, Empresas_Detalle_Filtro_Comuna, Actividades_CAM | ⚠️ Verificar 92 empresas |
| **CAM_Control** | Actividades_Empresa, Actividades_CAM | ⚠️ Verificar valores post-fix |
| **Hecho_Participacion_General** | Participantes_Empresa, Lista_Nombres_Empresas_Filtradas, (todos los "Participantes_*") | ⚠️ Verificar 37 empresas incluidas |
| **Dim_Seccion** | (Todos con "Empresarial") | ✅ OK |
| **Dim_Comuna** | Empresas_Detalle, Empresas_Detalle_Filtro_Comuna | ✅ OK |
| **Hecho_Simulacros** | Sim_Empresarial_* | ✅ OK |

---

## 🔗 REFERENCIAS

- **Investigación Previa**: [INVESTIGACION_CRITICA_37_EMPRESAS_FALTANTES.md](INVESTIGACION_CRITICA_37_EMPRESAS_FALTANTES.md)
- **Resolución de 37 Empresas**: [RESUMEN_EJECUTIVO_37_EMPRESAS_FIX.md](RESUMEN_EJECUTIVO_37_EMPRESAS_FIX.md)
- **Validación Completa**: [VALIDACION_COMPLETA_CAM_EMPRESAS.md](VALIDACION_COMPLETA_CAM_EMPRESAS.md)

---

**Generado por**: Auditoría Automática de Medidas | Power BI  
**Fecha**: 27-05-2026 | 10:15 AM  
**Estado**: LISTO PARA IMPLEMENTACIÓN
