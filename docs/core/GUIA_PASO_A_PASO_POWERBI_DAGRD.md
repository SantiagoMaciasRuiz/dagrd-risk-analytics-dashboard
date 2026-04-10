# Guia literal paso a paso: reset total del PBIX conservando diseno (fuente unica)

## Objetivo de esta guia
Esta guia reemplaza el flujo anterior para que trabajes solo con una fuente:
1. Borrar el modelo y los datos actuales del PBIX.
2. Conservar solo el diseno visual de tus paginas.
3. Reconectar un modelo limpio usando unicamente `Reporte de actividades equipo social 2026 (1).xlsx`.
4. Volver a enlazar medidas y visuales sin redisenar.

Regla central de trabajo:
- Si no es diseno visual (posicion, color, logos, encabezados, navegacion), se borra y se reconstruye.

Alcance de esta version:
- Fuente unica: `Reporte de actividades equipo social 2026 (1).xlsx`.
- Fuera de alcance: `Excel_Maestro_PowerBI.xlsx` y cualquier tabla derivada de ese archivo.

---

## Parte 0 - Preparacion rapida (obligatoria)

### 0.1 Cerrar archivos bloqueados
1. Cierra Excel.
2. Cierra Power BI Desktop.
3. Verifica que no exista abierto `~$Reporte de actividades equipo social 2026 (1).xlsx`.

### 0.2 Confirmar archivos fuente
Deben existir estos archivos en la carpeta del proyecto:
1. `Reporte de actividades equipo social 2026 (1).xlsx`
2. `extraer_consultas_paginas_reporte.py` (opcional para control y auditoria)

---

## Parte 1 - Respaldo y proteccion del diseno

### 1.1 Abrir y guardar copia del PBIX
1. Abre tu PBIX actual.
2. Click en `Archivo` > `Guardar como`.
3. Guarda una copia con nombre nuevo, por ejemplo:
4. `Tablero_DAGRD_RESET_FUENTE_UNICA_2026-03-16.pbix`

### 1.2 Congelar estructura visual (sin tocar estilos)
1. En cada pagina activa, click derecho en la pestana.
2. Click en `Duplicar pagina`.
3. Renombra cada copia con prefijo `DISENO_`.

Resultado esperado:
- Tienes una plantilla visual de respaldo por pagina.

---

## Parte 2 - PASO INICIAL REAL: borrar modelo y datos actuales

### 2.1 Desactivar fecha/hora automatica
1. Click en `Archivo` > `Opciones y configuracion` > `Opciones`.
2. En `Carga de datos`, desmarca `Fecha/Hora automatica` (archivo actual y nuevos archivos).
3. Click en `Aceptar`.

### 2.2 Borrar consultas viejas (Power Query)
1. Click en `Inicio` > `Transformar datos`.
2. En panel izquierdo, selecciona todas las consultas existentes.
3. Click derecho > `Eliminar`.
4. Click en `Cerrar y aplicar`.

### 2.3 Borrar origenes de datos del archivo actual
1. Click en `Archivo` > `Opciones y configuracion` > `Configuracion de origen de datos`.
2. En `Origenes de datos en el archivo actual`, selecciona todos los origenes viejos.
3. Click en `Borrar permisos` en cada origen.
4. Click en `Cerrar`.

### 2.4 Borrar objetos de modelo que queden sueltos
1. Ve a vista `Modelo`.
2. Elimina tablas calculadas viejas que hayan quedado (`_Medidas`, tablas auxiliares antiguas, etc.).
3. Elimina relaciones residuales.
4. Conserva solo paginas y diseno visual.

Resultado esperado:
- PBIX con diseno intacto y modelo vacio.

---

## Parte 3 - Control previo opcional con script (recomendado)

Esta parte NO es obligatoria para cargar el PBIX, pero si para validar calidad antes de modelar.

### 3.1 Ejecutar script de control
En terminal, ejecuta:

```powershell
c:/Users/santi/OneDrive/Escritorio/Chamba/Dashboard/.venv/Scripts/python.exe extraer_consultas_paginas_reporte.py
```

### 3.2 Archivo de control esperado
Debe crearse:
1. `Modelo_Reporte_Paginas_2026.xlsx`

Con hojas:
1. `Hecho_Participacion_General`
2. `General_Por_Seccion`
3. `General_Por_Comuna`
4. `General_Por_Fecha`
5. `Comunidad_Resumen`
6. `Educacion_Resumen`
7. `Empresarial_Resumen`
8. `Institucional_Resumen`
9. `Hecho_Demografia`
10. `Hecho_Simulacros`
11. `Simulacros_Por_Sector`
12. `Control_Extraccion`

### 3.3 Validacion minima de control
En `Control_Extraccion` valida:
1. `coinciden_actividades` = `SI`
2. `coinciden_participantes` = `SI`
3. Referencia historica (si no cambio el archivo fuente):
4. `total_actividades_hecho_general` cerca de `3202`
5. `total_participaciones_hecho_general` cerca de `111694`

---

## Parte 4 - Reconectar fuente unica desde cero

### 4.1 Conectar unicamente el Excel de reporte
1. En Power BI: `Inicio` > `Obtener datos` > `Excel`.
2. Selecciona `Reporte de actividades equipo social 2026 (1).xlsx`.
3. Click en `Transformar datos`.
4. En Navegador marca solo:
5. `Sheet1`
6. `Tablas dinamicas`
7. `Simulacros`

### 4.2 Renombrar consultas base (staging)
1. `Sheet1` -> `Stg_Sheet1`
2. `Tablas dinamicas` -> `Stg_TablasDinamicas`
3. `Simulacros` -> `Stg_Simulacros`

Regla de staging:
- Las consultas `Stg_*` no se cargan al modelo.

---

## Parte 5 - Construccion de consultas finales en Power Query

### 5.1 Hecho_Participacion_General (desde Stg_Sheet1)
Crear consulta referenciada de `Stg_Sheet1` y nombrarla `Hecho_Participacion_General`.

Columnas minimas obligatorias:
1. `id_actividad`
2. `fecha`
3. `anio`
4. `mes_num`
5. `mes_nombre`
6. `comuna_cod`
7. `instancia`
8. `seccion_tablero`
9. `participantes`
10. `impacto_indirecto`
11. `bloque_comunidad`
12. `bloque_educacion`
13. `bloque_empresarial`
14. `bloque_institucional`
15. Campos demograficos (`mujeres`, `hombres`, `ninos`, `pri_infanc`, `nino_adole`, `juventud`, `adulto`, `adulto_may`, `discapacid`, `afrodescen`, `campesino`, `pob_victim`, `pob_migran`, `pob_lgtbi`, `pob_indige`, `pob_rom`)

Tipos obligatorios:
1. `id_actividad` -> numero entero
2. `fecha` -> fecha
3. `anio` -> numero entero
4. `mes_num` -> numero entero
5. `comuna_cod` -> numero entero
6. `participantes` -> numero entero
7. `impacto_indirecto` -> numero entero
8. Columnas de bloque y seccion -> texto

Regla de fecha:
1. Si `fecha < 1900-01-01`, convertir a `null`.

### 5.2 Hecho_Demografia (desde Hecho_Participacion_General)
1. Referenciar `Hecho_Participacion_General`.
2. Anular dinamizacion de columnas demograficas.
3. Crear columnas:
4. `dimension`
5. `categoria`
6. `valor`
7. Filtrar `valor > 0`.

Columnas de contexto recomendadas:
1. `id_actividad`
2. `fecha`
3. `anio`
4. `mes_num`
5. `mes_nombre`
6. `comuna_cod`
7. `instancia`
8. `seccion_tablero`
9. `bloque_comunidad`
10. `bloque_educacion`
11. `bloque_empresarial`
12. `bloque_institucional`

### 5.3 Hecho_Simulacros (desde Stg_Simulacros)
Crear consulta referenciada de `Stg_Simulacros` y nombrarla `Hecho_Simulacros`.

Columnas minimas obligatorias:
1. `fecha`
2. `anio`
3. `mes_num`
4. `mes_nombre`
5. `comuna_texto`
6. `comuna_cod`
7. `sector_origen`
8. `sector_tablero`
9. `personas_participantes`
10. `nombre_entidad`

Tipos obligatorios:
1. `fecha` -> fecha
2. `anio` -> numero entero
3. `mes_num` -> numero entero
4. `comuna_cod` -> numero entero
5. `sector_tablero` -> texto
6. `personas_participantes` -> numero entero

Reglas clave:
1. Si `fecha < 1900-01-01`, convertir a `null`.
2. Si `comuna_cod` no se puede parsear, dejar `null` y registrar en control.

### 5.4 Dimensiones derivadas

#### 5.4.1 Dim_Fecha
1. Crear desde rango minimo/maximo de fechas de:
2. `Hecho_Participacion_General[fecha]`
3. `Hecho_Demografia[fecha]`
4. `Hecho_Simulacros[fecha]`
5. Incluir: `fecha`, `anio`, `mes_num`, `mes_nombre`, `trimestre`.

#### 5.4.2 Dim_Comuna
1. Unir distinct de `comuna_cod` desde los 3 hechos.
2. Excluir nulos para relaciones.

#### 5.4.3 Dim_Seccion
Crear tabla con 5 valores canonicos:
1. `Comunitaria`
2. `Educativa`
3. `Empresarial`
4. `Institucional`
5. `Otros`

#### 5.4.4 Dim_Instancia (recomendada)
1. Distinct de `instancia` y `seccion_tablero` desde `Hecho_Participacion_General`.

### 5.5 Control_Extraccion (solo QA, no para visual final)
1. Comparar totales de `Hecho_Participacion_General` vs pivote `Stg_TablasDinamicas`.
2. Crear campos:
3. `total_actividades_hecho_general`
4. `total_participaciones_hecho_general`
5. `total_actividades_pivot`
6. `total_participaciones_pivot`
7. `coinciden_actividades`
8. `coinciden_participantes`

### 5.6 Politica de carga final

Cargar al modelo:
1. `Hecho_Participacion_General`
2. `Hecho_Demografia`
3. `Hecho_Simulacros`
4. `Dim_Fecha`
5. `Dim_Comuna`
6. `Dim_Seccion`
7. `Dim_Instancia` (si se usa slicer de instancia)

No cargar al modelo:
1. `Stg_Sheet1`
2. `Stg_TablasDinamicas`
3. `Stg_Simulacros`
4. `Control_Extraccion`
5. Cualquier tabla `*_Resumen` o `General_Por_*` usada solo para auditoria

### 5.7 Aplicar cambios
1. `Inicio` > `Cerrar y aplicar`.

---

## Parte 6 - Relaciones finales (solo fuente unica)

Crear estas relaciones activas:
1. `Dim_Fecha[fecha]` -> `Hecho_Participacion_General[fecha]`
2. `Dim_Fecha[fecha]` -> `Hecho_Demografia[fecha]`
3. `Dim_Fecha[fecha]` -> `Hecho_Simulacros[fecha]`
4. `Dim_Comuna[comuna_cod]` -> `Hecho_Participacion_General[comuna_cod]`
5. `Dim_Comuna[comuna_cod]` -> `Hecho_Demografia[comuna_cod]`
6. `Dim_Comuna[comuna_cod]` -> `Hecho_Simulacros[comuna_cod]`
7. `Dim_Seccion[seccion_tablero]` -> `Hecho_Participacion_General[seccion_tablero]`
8. `Dim_Seccion[seccion_tablero]` -> `Hecho_Demografia[seccion_tablero]`
9. `Dim_Seccion[seccion_tablero]` -> `Hecho_Simulacros[sector_tablero]`
10. `Dim_Instancia[instancia]` -> `Hecho_Participacion_General[instancia]` (si aplica)
11. `Dim_Instancia[instancia]` -> `Hecho_Demografia[instancia]` (si aplica)

Parametros recomendados en todas:
1. Cardinalidad `Uno a varios (1:*)`.
2. Direccion de filtro `Unica`.
3. Relacion activa `Si`.

Reglas de oro:
1. No crear relaciones `Hecho` a `Hecho`.
2. No usar bidireccional en este modelo.
3. `Control_Extraccion` debe quedar desconectada.

---

## Parte 7 - Medidas DAX base (modelo fuente unica)

### 7.1 Crear tabla de medidas
1. `Modelado` > `Nueva tabla`.
2. Pega:

```dax
_Medidas = DATATABLE("Id", INTEGER, {{1}})
```

3. Oculta columna `Id`.

### 7.2 Medidas obligatorias

```dax
GenF_Total_Actividades =
COUNTROWS(Hecho_Participacion_General)
```

```dax
GenF_Total_Participaciones =
SUM(Hecho_Participacion_General[participantes])
```

```dax
Base_Impacto_Indirecto =
SUM(Hecho_Participacion_General[impacto_indirecto])
```

```dax
Base_Simulacros =
COUNTROWS(Hecho_Simulacros)
```

```dax
Base_Simulacros_Personas =
SUM(Hecho_Simulacros[personas_participantes])
```

```dax
GenF_Comunitaria_Participaciones =
CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Comunitaria")
```

```dax
GenF_Educativa_Participaciones =
CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Educativa")
```

```dax
GenF_Empresarial_Participaciones =
CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Empresarial")
```

```dax
GenF_Institucional_Participaciones =
CALCULATE([GenF_Total_Participaciones], Dim_Seccion[seccion_tablero] = "Institucional")
```

### 7.3 Medidas de control

```dax
Ctl_Referencia_Actividades_OK =
IF([GenF_Total_Actividades] = 3202, "SI", "NO")
```

```dax
Ctl_Referencia_Participaciones_OK =
IF([GenF_Total_Participaciones] = 111694, "SI", "NO")
```

Nota:
1. Estas dos medidas son de referencia historica.
2. Si cambia el archivo fuente, primero manda el control dinamico de `Control_Extraccion`.

### 7.4 Meta de participantes (opcional)
Si no tienes tabla de parametros oficial, evita una meta fija para no sesgar el KPI.

---

## Parte 8 - Reapuntar visuales conservando diseno

### 8.1 Regla de reemplazo
1. No mover visuales.
2. No cambiar formato.
3. Solo cambiar campos en `Valores`.

### 8.2 Mapeo principal por pagina

1. `Estrategia`:
2. KPIs y tendencias -> `Hecho_Participacion_General`
3. Simulacros -> `Hecho_Simulacros`

4. `Comunidad`:
5. Tarjetas por bloque -> `Hecho_Participacion_General` filtrando `bloque_comunidad`
6. Demografia -> `Hecho_Demografia`
7. Simulacros -> `Hecho_Simulacros` filtrando `sector_tablero = "Comunitaria"`

8. `Educacion`:
9. Tarjetas por bloque -> `Hecho_Participacion_General` filtrando `bloque_educacion`
10. Demografia -> `Hecho_Demografia`
11. Simulacros -> `Hecho_Simulacros` filtrando `sector_tablero = "Educativa"`

12. `Empresarial`:
13. Tarjetas por bloque -> `Hecho_Participacion_General` filtrando `bloque_empresarial`
14. Simulacros -> `Hecho_Simulacros` filtrando `sector_tablero = "Empresarial"`

15. `Institucional`:
16. Tarjetas por bloque -> `Hecho_Participacion_General` filtrando `bloque_institucional`
17. Demografia (si aplica) -> `Hecho_Demografia`

Regla critica:
1. No uses tablas `*_Resumen` ni `General_Por_*` como fuente de visual final.
2. Esas tablas solo sirven para auditoria/transicion.

---

## Parte 9 - Sincronizar slicers

1. Selecciona slicer `Anio`.
2. `Ver` > `Sincronizacion de segmentaciones`.
3. Marca sincronizar en todas las paginas.
4. Repite con `Mes`, `Comuna` y `Seccion`.

---

## Parte 10 - Validacion final obligatoria

### 10.1 Sin filtros
1. Verifica en control dinamico:
2. `coinciden_actividades = SI`
3. `coinciden_participantes = SI`
4. Referencia historica (si archivo fuente no cambio):
5. `GenF_Total_Actividades = 3202`
6. `GenF_Total_Participaciones = 111694`

### 10.2 Con filtros
1. Filtra por `Anio` y confirma cambios en `GenF_*`.
2. Filtra por `Comuna` y confirma cambios en `GenF_*`.
3. Filtra por `Seccion` y confirma coherencia entre Estrategia y pagina sectorial.

### 10.3 Si algo no cambia
1. Revisar relaciones activas en los 3 hechos.
2. Revisar tipos de `fecha` y `comuna_cod`.
3. Revisar que el visual no este conectado a tablas staging o resumen.

### 10.4 Validacion visual
1. Los visuales conservan diseno institucional.
2. Solo cambian numeros y logica.

---

## Parte 11 - Publicacion

1. `Archivo` > `Guardar`.
2. `Publicar`.
3. Selecciona area de trabajo.
4. Valida filtros y visuales en Power BI Service.

---

## Ruta de continuidad recomendada
Si ya estas en medio del proceso, retoma asi:
1. Si aun no borraste modelo: Parte 2.
2. Si ya borraste y falta modelado fuente unica: Parte 4 y Parte 5.
3. Si ya cargaste hechos/dimensiones: Parte 6.
4. Si ya creaste relaciones: Parte 7 y Parte 8.
5. Cierre final: Parte 9, Parte 10 y Parte 11.

## Checklist de cierre tecnico
1. Cero dependencias activas a `Excel_Maestro_PowerBI.xlsx`.
2. Cero relaciones ambiguas o bidireccionales.
3. Cero visuales finales montados sobre `Stg_*` o `*_Resumen`.
4. Slicers globales funcionando en todas las paginas.
