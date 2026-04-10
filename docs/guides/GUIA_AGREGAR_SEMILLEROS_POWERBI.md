# 📊 GUÍA: Agregar Tabla Semilleros a Power BI

**Objetivo:** Integrar los 20 semilleros confiables en tu dashboard Power BI  
**Tiempo estimado:** 10-15 minutos  
**Requiere:** Power BI Desktop + Excel actualizado

---

## ✅ Paso 1: Verificar Datos en Excel

### 1.1 Abrir el archivo Excel
- Ruta: `data/model/Modelo_Reporte_Paginas_2026.xlsx`
- Búscar la hoja **`Dim_Semilleros`** (debe ser la hoja 2)

### 1.2 Verificar contenido
```
Dim_Semilleros debe tener:
  
  Columnas:  N° | Semillero | Comuna | Comuna_Nombre | Barrio_Organización
  
  Filas:     20 semilleros (del #1 al #20)
  
  Formato:   Encabezado azul (#4472C4) y formato de tabla
```

✅ Si todo se ve bien → **Continua al Paso 2**  
❌ Si NO existe o está vacía → Ejecuta:
```bash
python scripts/etl/crear_tabla_semilleros.py
```

---

## ✅ Paso 2: Refrescar Datos en Power BI

### 2.1 Abre Power BI Desktop
- Abre el archivo `.pbix` que tengas en uso
- O crea uno nuevo y conecta a `Modelo_Reporte_Paginas_2026.xlsx`

### 2.2 Refrescar datos
- **Opción A (Atajo):** `Ctrl + Shift + R`
- **Opción B (Menú):** `Inicio` → botón `Refrescar` → `Refrescar`

### 2.3 Esperar a que se complete
- Power BI descargará la nueva tabla `Dim_Semilleros`
- Espere 10-30 segundos según tamaño del modelo

✅ Una vez completado → **Continua al Paso 3**

---

## ✅ Paso 3: Crear Relación entre Tablas

### 3.1 Ir a Vista de Modelado
- `Inicio` → `Cambiar vista` → `Modelado` (o botón en barra izquierda)

### 3.2 Crear nueva relación
- Haz clic botón `Nueva relación`
- O arrastra manualmente columna von columna

### 3.3 Configurar relación
| Parámetro | Valor |
|-----------|-------|
| **Tabla 1** | Dim_Semilleros |
| **Columna 1** | Comuna |
| **Tabla 2** | Hecho_Participacion_General |
| **Columna 2** | comuna_cod |
| **Cardinalidad** | Muchos a 1 (M:1) |
| **Dirección cruzada** | Simple |
| **Activa** | ✓ Sí |

### 3.4 Guardar
- Clic `OK`
- Power BI creará la relación automáticamente

✅ Relación creada → **Continua al Paso 4**

---

## ✅ Paso 4: Agregar Medidas DAX

### 4.1 Abrir archivo de medidas
- Abre: `scripts/dax/medidas_semilleros.dax`
- Copia el contenido (Ctrl + A, Ctrl + C)

### 4.2 En Power BI: Ir a Modelado
- `Inicio` → `Modelado` (si no está activo)
- Verás todas las tablas en el esquema

### 4.3 Crear medida 1: Total_Semilleros
1. Haz clic en tabla **Dim_Semilleros** (esquema visual)
2. `Herramientas de tabla` → `Nueva medida`
3. Copia esta fórmula:
```dax
Total_Semilleros = DISTINCTCOUNT(Dim_Semilleros[Semillero])
```
4. `Intro` para guardar

### 4.4 Crear medida 2: Semilleros_por_Comuna
1. Nuevamente en **Dim_Semilleros** → `Nueva medida`
2. Copia:
```dax
Semilleros_por_Comuna = DISTINCTCOUNT(Dim_Semilleros[Comuna])
```
3. `Intro`

### 4.5 Crear medida 3: Semilleros_Activos
1. **Dim_Semilleros** → `Nueva medida`
2. Copia:
```dax
Semilleros_Activos = CALCULATE(
    DISTINCTCOUNT(Dim_Semilleros[Semillero]),
    FILTER(Hecho_Participacion_General, 
           Hecho_Participacion_General[bloque_comunidad] = "Semilleros")
)
```
3. `Intro`

### 4.6 Crear medida 4: Comuna_Seleccionada_Semilleros
1. **Dim_Semilleros** → `Nueva medida`
2. Copia:
```dax
Comuna_Seleccionada_Semilleros = IFERROR(
    VALUES(Dim_Semilleros[Comuna_Nombre]),
    "Seleccionar"
)
```
3. `Intro`

✅ Todas las medidas creadas → **Continua al Paso 5**

---

## ✅ Paso 5: Crear Visuales

### 5.1 Ir a Vista de Informe
- `Inicio` → `Cambiar vista` → `Informe`

### 5.2 Crear Tarjeta: Total de Semilleros
1. `Insertar` → `Tarjeta` (o `Tarjeta de número grande`)
2. En **Campos:** arrastra:
   - **Medida:** `Total_Semilleros`
3. Resultado esperado: **20**

### 5.3 Crear Tarjeta: Comunas con Semilleros
1. Insertar nueva `Tarjeta`
2. Arrastra:
   - **Medida:** `Semilleros_por_Comuna`
3. Resultado esperado: **9**

### 5.4 Crear Tabla: Semilleros por Comuna
1. `Insertar` → `Tabla` (o `Matriz`)
2. Entrados:
   - **Filas:** `Dim_Semilleros[Comuna_Nombre]`
   - **Valores:** `Dim_Semilleros[Semillero]` (Contar)
3. Ordena por Comuna

### 5.5 Crear Slicer: Filtrar por Comuna
1. `Insertar` → `Slicer`
2. Selecciona:
   - **Campo:** `Dim_Semilleros[Comuna_Nombre]`
3. Ahora puedes filtrar otros visuales por comuna

### 5.6 Crear Tabla Detallada: Todos los Semilleros
1. `Insertar` → `Tabla`
2. Arrastra columnas:
   - `Dim_Semilleros[N°]`
   - `Dim_Semilleros[Semillero]`
   - `Dim_Semilleros[Comuna_Nombre]`
   - `Dim_Semilleros[Barrio_Organización]`

✅ Visuales creados → **Continua al Paso 6**

---

## ✅ Paso 6: Validación Final

### 6.1 Verificar números
Asegúrate que:
- ✓ `Total_Semilleros` = **20**
- ✓ `Semilleros_por_Comuna` = **9**
- ✓ Tabla muestra todos los semilleros
- ✓ Slicer filtra correctamente

### 6.2 Revisar datos mostrados
Busca en tabla:
- [ ] "Semillero IE Fe y Alegría" - Comuna 1
- [ ] "Semillero Comunidad Embera Dobida" - Comuna 80
- [ ] "Semillero Miranda" - Comuna 4
- [ ] etc.

### 6.3 Verificar relaciones
- En `Modelado`, verifica que existe línea entre:
  - `Dim_Semilleros[Comuna]` ↔ `Hecho_Participacion_General[comuna_cod]`

✅ Todo validado → **¡Completado!**

---

## 🔄 Solución de Problemas

### ❌ Problema: "Dim_Semilleros no aparece en Power BI"
**Solución:**
1. Ejecuta script: `python scripts/etl/crear_tabla_semilleros.py`
2. En Power BI: Refrescar (`Ctrl+Shift+R`)
3. Espera 30 segundos
4. Aparecerá en lista de tablas

### ❌ Problema: Medidas muestran error "#ERROR"
**Solución:**
1. Verifica nombre de tabla: debe ser exactamente `Dim_Semilleros`
2. Verifica nombre de columnas: `Semillero`, `Comuna`, `Comuna_Nombre`
3. Elimina medida errónea y re-crea

### ❌ Problema: Slicer no filtra otros visuales
**Solución:**
1. Verifica que exista relación (Paso 3)
2. Si no existe, crea manualmente en `Modelado`
3. Dirección cruzada debe ser "Ambas" o "Simple"

### ❌ Problema: Total muestra número erróneo
**Solución:**
1. Verifica que Excel tenga exactamente 20 Semilleros
2. Ejecuta: `python scripts/qa/analizar_kpis_comunidad.py`
3. Busca línea `Semilleros distinct publico_comunidad:` (debe ser 4)

---

## 📋 Checklist Final

- [ ] Excel tiene hoja `Dim_Semilleros` con 20 registros
- [ ] Power BI refrescó datos correctamente
- [ ] Relación Dim_Semilleros-Hecho creada
- [ ] 4 medidas DAX creadas sin errores
- [ ] Tarjeta muestra: Total_Semilleros = 20
- [ ] Tarjeta muestra: Semilleros_por_Comuna = 9
- [ ] Tabla detallada muestra 20 filas
- [ ] Slicer filtra por Comuna correctamente
- [ ] Todos los datos se ven en el informe
- [ ] Datos validados (tienen nombres correctos)

---

## ✅ LISTO PARA USAR

Una vez completados los 6 pasos y pasados todos los checklist:

✨ **Tu dashboard ya tiene los 20 Semilleros integrados correctamente**

- Puedes crear más visuales según necesites
- Los datos se actualizarán automáticamente si cambias Excel
- Las medidas funcionarán en todos tus slicers y filtros

---

**Documento creado:** 2026-03-18  
**Versión:** 1.0  
**Contacto:** DAGRD Team
