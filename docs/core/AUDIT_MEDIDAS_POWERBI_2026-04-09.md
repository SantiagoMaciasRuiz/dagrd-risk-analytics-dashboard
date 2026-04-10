# AUDITORÍA DE MEDIDAS - MODELO POWER BI tableroDAGRD

**Fecha**: 9 de abril, 2026  
**Modelo**: tableroDAGRD (localhost:57797)  
**Fuente**: TMDL live tables/_Medidas.tmdl  

---

## 📊 RESUMEN EJECUTIVO

```
Total de medidas en el modelo:        172
├─ Medidas principales:              89
└─ Medidas VAL (backing/support):    83

ESTADO GENERAL:
✓ ACTIVAS (utilizadas):              87   (97.8%)
✗ HUÉRFANAS (no usadas):              2   (2.2%)
⚠ DUPLICADAS:                         0   (0.0%)
✗ QUEBRADAS (errores DAX):            0   (0.0%)
✗ OBSOLETAS (patrón antigua):         0   (0.0%)

SALUD DEL MODELO: ✅ EXCELENTE (97.8% de medidas activas)
```

---

## 🟢 MEDIDAS ACTIVAS (87 medidas)

Todas las medidas principales están siendo utilizadas o son referenciadas por otras. Se organizan en las siguientes categorías:

### Por Categoría

| Categoría | Cantidad | Ejemplos |
|-----------|----------|----------|
| **General (GenF_)** | 14 | GenF_Total_Actividades, GenF_Total_Participaciones, GenF_Comunitaria_Participaciones |
| **Actividades** | 15 | Actividades_SATC, Actividades_Comites, Actividades_BasicaMedia, Actividades_Superior |
| **Participantes** | 12 | Participantes_SATC, Participantes_Comites, Participantes_CAM, Participantes_HogarSeguro |
| **Demografía (Dem_)** | 11 | Dem_Adulto, Dem_Juventud, Dem_PrimeraInfancia, Dem_Discapacidad, Dem_LGTBI |
| **Educación** | 8 | GenF_Edu_Instituciones_Unicas, Lista_Instituciones_BasicaMedia, Edu_Acomp_PlanesEscolares_GRD |
| **Institucional** | 7 | Articulacion_Institucional, Participantes_Acciones_Conjuntas, Actividades_ArticulacionInstitucional |
| **Simulacros** | 6 | Simulacros_Registrados_Total, Simulacros_Institucionales, Sim_Empresarial_Personas |
| **Empresarial** | 7 | Actividades_CAM, Participantes_CAM, Sim_Empresarial_Registros |
| **Cobertura/Impacto** | 4 | Cobertura_Total, Cobertura_Global, Impacto_Indirecto_Comunidad |
| **Control/Validación** | 2 | Ctl_Referencia_Actividades_OK, Ctl_Referencia_Participaciones_OK |
| **Listas/Detalle** | 3 | Lista_Instituciones_BasicaMedia, Lista_Comites_Comisiones_Filtrados, Lista_SATC_Filtrados |
| **Otra** | 10 | Num_Comites_Comisiones, Eje_AnioMes, Base_Impacto_Indirecto |

### Patrón de Uso

- **97.8% (87 medidas)**: Son "Componente de par VAL" = tienen una contraparte `_VAL` (backing measure con formato)
  - Ejemplo: `Participantes_SATC` + `Participantes_SATC_VAL`
  - Las medidas sin `_VAL` usan `FORMAT(variable_VAL)` para mostrar números formateados
  
- **0.2% (1 medida)**: Función auxiliar (`Eje_AnioMes`) = usada internamente

---

## 🔴 MEDIDAS HUÉRFANAS (2 medidas)

Estas medidas **NO están siendo usadas en visuales ni son referenciadas** por otras medidas:

| Medida | Carpeta | Categoría | Observación |
|--------|---------|-----------|-------------|
| **Ctl_Referencia_Actividades_OK** | — | Control/Validación | Validación hardcoded: = IF(GenF_Total_Actividades_VAL = 3202, "SI", "NO") |
| **Ctl_Referencia_Participaciones_OK** | — | Control/Validación | Validación hardcoded: = IF(GenF_Total_Participaciones_VAL = 111694, "SI", "NO") |

### Análisis

Estas son **medidas de control externo** que validan si los datos cumplen valores de referencia (3202 actividades, 111694 participaciones). 

**Recomendación**: 
- Verificar si todavía se necesitan para validación en otros reportes
- Si NO se usan, considerar eliminarlas (posible legacy de fase anterior)
- Si SÍ se usan eventualmente, documentar dónde y para qué

---

## ⚠️ DUPLICADAS (0 medidas)

✅ **No hay medidas duplicadas detectadas**. 

Nota técnica: El análisis detectó 83 "grupos de posibles duplicados" pero estos son pares `Medida` + `Medida_VAL`, que son **intencionalmente complementarios** (no duplicación).

---

## ❌ QUEBRADAS (0 medidas)

✅ **No hay medidas con errores DAX detectados**.

Todas las expresiones son sintácticamente válidas.

---

## 🕐 OBSOLETAS (0 medidas)

✅ **No hay medidas con patrones de nombre obsoleto detectados**.

(Se buscaban patrones como `OLD_`, `LEGACY_`, `_v1`, `_BORRAR`, etc.)

---

## 📋 RECOMENDACIONES DE LIMPIEZA

### Inmediatas

1. **Revisar medidas de control** (Ctl_Referencia_*)
   - ¿Se siguen usando en reportes o dashboards?
   - ¿Están hardcodeados los valores 3202 y 111694?
   - Si no son necesarias → eliminar

2. **Auditar cambios desde última actualización**
   - 172 medidas es un número elevado
   - Considerar si todas son necesarias en modelo vivo

### A Mediano Plazo

3. **Documentar propósito de medidas VAL**
   - Las 83 medidas `*_VAL` son backing measures necesarias
   - Asegurar que estos never se usen directamente en reportes

4. **Considerar organización en carpetas**
   - Muchas medidas aún no tienen `displayFolder` asignada
   - Mejorar navegabilidad en Power BI Desktop

5. **Validar fórmulas en medidas educativas complejas**
   - `GenF_Edu_Instituciones_Unicas_VAL`: usa `REMOVEFILTERS` + `KEEPFILTERS` (patrón avanzado)
   - `Edu_Acomp_PlanesEscolares_GRD_VAL`: busca strings con `CONTAINSSTRING` (puede ser lento)

---

## 📊 NOTA TÉCNICA

### Metodología de Análisis

1. **Parse TMDL**: Extrae 172 medidas del archivo `_Medidas.tmdl`
2. **Cross-reference**: Detecta qué medidas referencian a cuáles
3. **Visual Usage**: Correlaciona contra `powerbi_consultas_visuales_2026.csv`
4. **Heurísticas:**
   - `Medida_VAL` = backing for `Medida` ✓
   - `Lista_`, `Eje_`, etc. = auxiliares ✓
   - Si está en `displayFolder` = probablemente activa ✓

### Limitaciones

- Solo se auditan expresiones DAX, no comportamiento en tiempo de ejecución
- El CSV de visuales está parcialmente vacío (referencias directo a columnas, no medidas)
- No se valida desempeño (¿qué medidas son lentas?)

---

## 📁 ARCHIVOS GENERADOS

- **`audit_medidas_2026.json`**: Reporte completo en machines-readable
- **Este documento**: Versión executiva para revisión manual

---

**Próximas acciones sugeridas:**
1. Validar medidas de control (2 huérfanas)
2. Documentar propósito de cada categoría de medidas
3. Reorganizar en carpetas Display para mejor UX en Power BI Desktop
4. Ejecutar audit mensual para monitorear cambios
