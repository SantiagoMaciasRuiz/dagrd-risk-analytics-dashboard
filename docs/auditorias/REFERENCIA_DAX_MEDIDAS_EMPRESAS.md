# 📌 REFERENCIA DAX - MEDIDAS "EMPRESAS" COMPLETO

**Archivo de Referencia para Actualizaciones**  
**Conexión**: localhost:54211 | **Fecha**: 27-05-2026

---

## 🔴 MEDIDAS CRÍTICAS - IMPLEMENTACIONES RECOMENDADAS

### 1. EMPRESAS_DETALLE (ACTUAL vs PROPUESTO)

#### ❌ ACTUAL (PROBLÉMÁTICO)
```dax
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _MapaZonaComuna =
    DATATABLE(
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
            {"Robledo IPS", 60}
        }
    )
VAR _ZonasPermitidas =
    SELECTCOLUMNS(
        FILTER(_MapaZonaComuna, [comuna_cod] IN _ComunasSeleccionadas),
        "zona_cam", [zona_cam]
    )
VAR _EmpresasFiltradas =
    CALCULATETABLE(
        VALUES(CAM_Detalle[empresa_normalizada]),
        KEEPFILTERS(TREATAS(_ZonasPermitidas, CAM_Detalle[zona_cam]))
    )
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
RETURN
    IF(
        HASONEVALUE(CAM_Detalle[empresa_normalizada]),
        IF([Empresas_Detalle_Filtro_Comuna] = 1, _EmpresaActual, BLANK()),
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
```

#### ✅ OPCIÓN A: USAR TABLA DE RELACIONES DINÁMICA
```dax
-- Supone tabla CAM_Zonas_Comunas existe
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _ZonasPermitidas =
    CALCULATETABLE(
        VALUES(CAM_Zonas_Comunas[zona_cam]),
        CAM_Zonas_Comunas[comuna_cod] IN _ComunasSeleccionadas,
        CAM_Zonas_Comunas[activo] = TRUE
    )
VAR _EmpresasFiltradas =
    CALCULATETABLE(
        VALUES(CAM_Detalle[empresa_normalizada]),
        CAM_Detalle[zona_cam] IN _ZonasPermitidas,
        CAM_Detalle[activo] = TRUE
    )
RETURN
    IF(
        HASONEVALUE(CAM_Detalle[empresa_normalizada]),
        IF([Empresas_Detalle_Filtro_Comuna] = 1, _EmpresaActual, BLANK()),
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
```

#### ✅ OPCIÓN B: REMOVER FILTRO POR ZONA (SIN MAPA)
```dax
-- Si la zona no es necesaria, simplificar
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _EmpresasFiltradas =
    CALCULATETABLE(
        VALUES(CAM_Detalle[empresa_normalizada]),
        CAM_Detalle[activo] = TRUE
    )
RETURN
    IF(
        HASONEVALUE(CAM_Detalle[empresa_normalizada]),
        IF(NOT(ISBLANK(_EmpresaActual)), _EmpresaActual, BLANK()),
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
```

---

### 2. EMPRESAS_DETALLE_FILTRO_COMUNA (ACTUAL vs PROPUESTO)

#### ❌ ACTUAL
```dax
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _MapaZonaComuna =
    DATATABLE(
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
            {"Robledo IPS", 60}
        }
    )
VAR _ZonasPermitidas =
    SELECTCOLUMNS(
        FILTER(_MapaZonaComuna, [comuna_cod] IN _ComunasSeleccionadas),
        "zona_cam", [zona_cam]
    )
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _Visible =
    CALCULATE(
        COUNTROWS(CAM_Detalle),
        KEEPFILTERS(CAM_Detalle[empresa_normalizada] = _EmpresaActual),
        KEEPFILTERS(TREATAS(_ZonasPermitidas, CAM_Detalle[zona_cam]))
    )
RETURN
    IF(
        NOT(HASONEVALUE(CAM_Detalle[empresa_normalizada])),
        1,
        IF(NOT(ISBLANK(_EmpresaActual)) && _Visible > 0, 1, BLANK())
    )
```

#### ✅ OPCIÓN A: CON TABLA DINÁMICA
```dax
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
VAR _ZonasPermitidas =
    CALCULATETABLE(
        VALUES(CAM_Zonas_Comunas[zona_cam]),
        CAM_Zonas_Comunas[comuna_cod] IN _ComunasSeleccionadas,
        CAM_Zonas_Comunas[activo] = TRUE
    )
VAR _Visible =
    CALCULATE(
        COUNTROWS(CAM_Detalle),
        CAM_Detalle[empresa_normalizada] = _EmpresaActual,
        CAM_Detalle[zona_cam] IN _ZonasPermitidas,
        CAM_Detalle[activo] = TRUE
    )
RETURN
    IF(
        NOT(HASONEVALUE(CAM_Detalle[empresa_normalizada])),
        1,
        IF(NOT(ISBLANK(_EmpresaActual)) && _Visible > 0, 1, BLANK())
    )
```

#### ✅ OPCIÓN B: SIN FILTRO POR ZONA
```dax
VAR _EmpresaActual = SELECTEDVALUE(CAM_Detalle[empresa_normalizada])
VAR _Visible =
    CALCULATE(
        COUNTROWS(CAM_Detalle),
        CAM_Detalle[empresa_normalizada] = _EmpresaActual,
        CAM_Detalle[activo] = TRUE
    )
RETURN
    IF(
        NOT(HASONEVALUE(CAM_Detalle[empresa_normalizada])),
        1,
        IF(NOT(ISBLANK(_EmpresaActual)) && _Visible > 0, 1, BLANK())
    )
```

---

### 3. PARTICIPANTES_CAM (DUMMY → FUNCIONAL)

#### ❌ ACTUAL (DUMMY)
```dax
"N/A"
```

#### ✅ PROPUESTO
```dax
VAR _v = CALCULATE(
    SUM(Hecho_Participacion_General[participantes]),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "CAM"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

---

### 4. ACTIVIDADES_PLANESAYUDAMUTUA (DUMMY → FUNCIONAL)

#### ❌ ACTUAL (DUMMY)
```dax
1
```

#### ✅ PROPUESTO
```dax
VAR _v = CALCULATE(
    COUNTROWS(Hecho_Participacion_General),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Planes de ayuda mutua/Acuerdo de voluntades"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

---

## ⚠️ MEDIDAS RECOMENDADAS PARA VALIDACIÓN/ACTUALIZACIÓN

### 5. ACTIVIDADES_EMPRESA (VERIFICAR)

#### ✅ ACTUAL
```dax
VAR _v = MAX(CAM_Control[empresas_unicas_global])
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### 🔍 VALIDACIÓN REQUERIDA
- Confirmar que `CAM_Control[empresas_unicas_global]` refleja 92 (no 73)
- Si está desactualizado, usar:

#### ✅ ALTERNATIVA (SI ES NECESARIO)
```dax
VAR _v = CALCULATE(
    DISTINCTCOUNT(CAM_Detalle[empresa_normalizada]),
    CAM_Detalle[activo] = TRUE
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

---

### 6. LISTA_NOMBRES_EMPRESAS_FILTRADAS (VALIDAR + MEJORAR)

#### ✅ ACTUAL
```dax
VAR _Nombres =
    CALCULATETABLE(
        VALUES(Hecho_Participacion_General[publico_empresarial]),
        KEEPFILTERS(Hecho_Participacion_General[seccion_tablero] = "Empresarial"),
        KEEPFILTERS(Hecho_Participacion_General[bloque_empresarial] = "Empresas")
    )
VAR _Lista =
    CONCATENATEX(
        FILTER(
            _Nombres,
            NOT(ISBLANK(Hecho_Participacion_General[publico_empresarial]))
                && TRIM(Hecho_Participacion_General[publico_empresarial]) <> ""
        ),
        Hecho_Participacion_General[publico_empresarial],
        UNICHAR(10),
        Hecho_Participacion_General[publico_empresarial],
        ASC
    )
RETURN
    IF(_Lista = "", "N/A", _Lista)
```

#### 🔍 VERIFICACIÓN REQUERIDA
1. Confirmar que Hecho_Participacion_General incluye todas 92 empresas
2. Si falta alguna empresa de CAM_Detalle, usar esta alternativa:

#### ✅ ALTERNATIVA (CON FALLBACK A CAM_DETALLE)
```dax
VAR _Nombres_HPG =
    CALCULATETABLE(
        DISTINCT(Hecho_Participacion_General[publico_empresarial]),
        Hecho_Participacion_General[seccion_tablero] = "Empresarial",
        Hecho_Participacion_General[bloque_empresarial] = "Empresas",
        NOT(ISBLANK(Hecho_Participacion_General[publico_empresarial]))
    )
VAR _Nombres_CAM =
    CALCULATETABLE(
        VALUES(CAM_Detalle[empresa_normalizada]),
        CAM_Detalle[activo] = TRUE
    )
VAR _NombresFinal =
    UNION(_Nombres_HPG, _Nombres_CAM)
VAR _Lista =
    CONCATENATEX(
        FILTER(_NombresFinal, TRIM([Value]) <> ""),
        [Value],
        UNICHAR(10),
        [Value],
        ASC
    )
RETURN IF(_Lista = "", "N/A", _Lista)
```

---

## ✅ MEDIDAS OK (SIN CAMBIOS)

### Medidas que funcionan correctamente:

#### Participantes_Empresa ✅
```dax
VAR _v = CALCULATE(
    SUM(Hecho_Participacion_General[participantes]),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Empresas"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### Actividades_PropiedadHorizontal ✅
```dax
VAR _v = CALCULATE(
    COUNTROWS(Hecho_Participacion_General),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Propiedades Horizontales"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### Participantes_PropiedadHorizontal ✅
```dax
VAR _v = CALCULATE(
    SUM(Hecho_Participacion_General[participantes]),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Propiedades Horizontales"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### Actividades_CAM ✅
```dax
VAR _v = MAX(CAM_Control[cam_activos_total])
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### Participantes_PlanesAyudaMutua ✅
```dax
VAR _v = CALCULATE(
    SUM(Hecho_Participacion_General[participantes]),
    Dim_Seccion[seccion_tablero] = "Empresarial",
    Hecho_Participacion_General[bloque_empresarial] = "Planes de ayuda mutua/Acuerdo de voluntades"
)
RETURN IF(ISBLANK(_v), "N/A", FORMAT(_v, "#,##0"))
```

#### GenF_Empresarial_Actividades ✅
```dax
CALCULATE([GenF_Total_Actividades], Dim_Seccion[seccion_tablero] = "Empresarial")
```

#### GenF_Empresarial_Participaciones ✅
```dax
CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Empresarial")
```

#### GenF_Empresarial_Impacto ✅
```dax
CALCULATE([Base_Impacto_Indirecto], Dim_Seccion[seccion_tablero] = "Empresarial")
```

#### Sim_Empresarial_Registros ✅
```dax
CALCULATE([Base_Simulacros], Hecho_Simulacros[sector_tablero] = "Empresarial")
```

#### Sim_Empresarial_Personas ✅
```dax
CALCULATE([Base_Simulacros_Personas], Hecho_Simulacros[sector_tablero] = "Empresarial")
```

---

## 🔄 ORDEN DE ACTUALIZACIÓN RECOMENDADO

1. **Empresas_Detalle** (Elimina problema de 37 empresas)
2. **Empresas_Detalle_Filtro_Comuna** (Ajusta lógica de filtro)
3. **Participantes_CAM** (Implementar funcionalidad real)
4. **Actividades_PlanesAyudaMutua** (Implementar funcionalidad real)
5. **Validar Actividades_Empresa** (Verificar CAM_Control actualizado)
6. **Validar Lista_Nombres_Empresas_Filtradas** (Verificar cobertura)

---

**Referencia creada**: 27-05-2026 | Power BI localhost:54211  
**Listo para**: Implementación inmediata en Power BI Desktop
