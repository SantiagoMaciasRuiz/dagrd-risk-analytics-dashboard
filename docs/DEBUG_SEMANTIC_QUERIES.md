# 🔧 Diagnóstico y Validación: Semantic Queries Arregladas

## 📋 Resumen del Fix

El sistema identificó que las tarjetas visuales mostraban `"Hubo un problema con uno o más campos"` porque las consultas semánticas estaban **usando siempre `Measure`** incluso para columnas normales.

### Cambio Principal
En `scripts/powerbi/autovis_build_pbip_smart.py` → función `_build_card_visual()`:

**Antes (incorrecto):**
```python
# Siempre usaba Measure, incluso para columnas
"field": {
    "Measure": { ... "Property": field ... }
}
```

**Después (correcto):**
```python
# Ahora distingue entre Measure y Column
if is_measure:
    "field": { "Measure": { ... } }
else:
    "field": { "Column": { ... } }
```

---

## ✅ Pasos de Validación

### Paso 1: Inspeccionar estructura del modelo (RECOMENDADO)
```bash
# En terminal, desde la carpeta del Dashboard:
python scripts/powerbi/debug_model_structure.py "C:\Users\santi\Downloads\documentos\pruebaHtml.pbip"
```

**Qué esperar:**
- Lista de todas las tablas en el modelo
- Columnas de cada tabla
- Medidas disponibles
- Vista previa de que 4 visualizaciones se crearían

---

### Paso 2: Ejecutar pipeline renovado

**En el frontend `http://127.0.0.1:8000`:**

1. Escribe ruta del PBIP:
   ```
   C:\Users\santi\Downloads\documentos\pruebaHtml.pbip
   ```

2. Click en **"▶️ Ejecutar Workflow"** para correr:
   - ✓ Validar Contexto
   - ✓ AutoBuild (Smart)
   - ✓ AutoFull (Smart)
   - ✓ AutoVis Smart (con fix)

3. Espera a que se complete (la barra avanza paso a paso)

---

### Paso 3: Verificar en Power BI Desktop

**Abrir el PBIX local:**
- Espera que Power BI recargue los cambios
- Ve a la página "AutoVis IA"
- **Antes (roto):** 6 tarjetas con ⚠️ y mensaje de error
- **Después (esperado):** Las tarjetas deberían mostrar:
  - ✓ Datos numéricos (si tiene medidas)
  - ✓ O campos sin errores (si tiene columnas)
  - ✓ O tarjetas vacías profesionales (si no hay datos)

---

## 🔍 Si Aún Hay Problemas

### Problema: Las tarjetas siguen mostrando error

**Opción A: Modo Verbose (diagnóstico)**
```bash
# Ejecuta AutoVis con diagnóstico completo
python scripts/powerbi/autovis_build_pbip_smart.py -PbipPath "C:\..." -Verbose 1
```

Esto mostrará:
- Nombre exacto de las tablas
- Campos/medidas que se referenciaron
- Estructura JSON completa de cada visual

**Opción B: Inspeccionar JSON generado**
1. Abre `pruebaHtml.Report/definition/pages/AutoVis IA.json`
2. Busca las secciones `queryState` dentro de cada visual
3. Verifica que los nombres de tabla/campo coincidan exactamente con TMDL

---

## 📊 Explicación Técnica

El problema original fue que Power BI tiene **tipos de referencia diferentes**:

| Tipo | Campo | Estructura JSON |
|------|-------|-----------------|
| **Medida** | `Sales [Total Sales]` | `"Measure": {"Property": "Total Sales"}` |
| **Columna** | `Products [Name]` | `"Column": {"Property": "Name"}` |
| **Vacío** | (sin referencia) | (sin `query`) |

El código anterior **siempre usaba `Measure`**, lo que hacía que Power BI buscara una medida cuando en realidad era una columna, causando el error.

Ahora el sistema:
1. Parsea TMDL para saber qué es medida vs. columna
2. Usa la estructura correcta para cada tipo
3. Si no hay datos, crea tarjetas vacías en lugar de referencias rotas

---

## 🎯 Próximas Mejoras (Futuro)

- [ ] Agregar soporte para visualizaciones de tabla (Table)
- [ ] Crear gráficos inteligentes basados en tipos de datos
- [ ] Agregaciones automáticas para campos numéricos
- [ ] Validación de ciclos circulares en relaciones

---

**Estado:** ✅ Fix implementado | ⏳ Pendiente validación en Power BI
