# 🚀 Guía Rápida: Sistema Automático desde Frontend

## ¿Qué Cambió?

El sistema ahora es **100% automático desde el navegador**. No necesitas terminal ni cerrar Power BI manualmente.

---

## 📋 Flujo Simple

### Opción 1: Ejecutar TODO automáticamente (RECOMENDADO)

1. **Abre el frontend:** `http://127.0.0.1:8000`

2. **Escribe la ruta del PBIP:**
   ```
   C:\Users\santi\Downloads\documentos\pruebaHtml.pbip
   ```
   Click en "Guardar"

3. **Click gigante en:** `▶️ EJECUTAR TODO AUTOMÁTICO`

**¿Qué pasa?** El sistema:
- ✅ Cierra Power BI Desktop automáticamente
- ✅ Valida que tengas un PBIX abierto con datos
- ✅ Ejecuta AutoBuild (carga el modelo)
- ✅ Ejecuta AutoFull (crea estructura)
- ✅ Ejecuta AutoVis Smart (crea visualizaciones profesionales)

**Tiempo total:** ~2-3 minutos

---

### Opción 2: Solo cerrar Power BI (si necesitas hacerlo manual)

1. Click en **"❌ Cerrar Power BI"** (sección Acciones Rápidas)
2. Verás indicador de progreso y confirmación

---

## 📊 Indicadores Visuales

Mientras corre el pipeline, verás:
- ✓ Barra de progreso (0% → 100%)
- ✓ Paso actual destacado (Cerrar → Validar → AutoBuild → ...)
- ✓ Estado "En espera", "Ejecutando", "Completado", "Error"
- ✓ Historial de ejecuciones en panel derecho

---

## 🔧 Después del Pipeline

**Reabre Power BI Desktop:**
1. File → Open
2. Abre el mismo PBIX (`pruebaHtml.pbix`)
3. Navega a la página "AutoVis IA"
4. Verifica que las **6 tarjetas muestren datos sin errores** ✅

---

## ❌ Si Algo Falla

1. **Lee el mensaje de error** en el panel derecho (es muy descriptivo)

2. **Opciones:**
   - Click "Reintentar último fallo" (re-ejecuta solo el paso que falló)
   - Click "Cancelar" (detiene todo)
   - Cierra sesión y recarga el navegador

3. **Detalles técnicos:**
   - Abre DevTools (`F12`) → Pestaña "Console"
  - O revisa los logs del script o del backend local que ejecute el pipeline (si tienes acceso)

---

## 📱 Interfaz Nueva

```
PANEL DERECHO (Todo lo que necesitas):

⚡ ACCIONES RÁPIDAS
  [❌ Cerrar Power BI]

📁 CONTROL PBIP
  [Input: ruta PBIP] [Guardar]

🚀 PIPELINE AUTOMÁTICO
  [▶️ EJECUTAR TODO AUTOMÁTICO]  ← BOTÓN PRINCIPAL
  [Reintentar] [Cancelar]
  
  Progreso:
  ██████████░░░░░░░░ 50%
  
  Pasos:
  ✓ 0. Cerrar Power BI
  ⏳ 1. Validar Contexto
  ⌛ 2. AutoBuild
  ⌛ 3. AutoFull
  ⌛ 4. AutoVis PBIP

📜 ACCIONES EJECUTADAS
  (historial de lo que corrió)

📋 HISTORIAL
  (intentos anteriores)
```

---

## 🎯 Cambios Técnicos (Para reference)

- ✅ **Backend (`main.py`)**: Nuevo endpoint `/api/close-powerbi`
- ✅ **Frontend (`app.js`)**: Nueva función `closePowerBI()` + paso "close" en pipeline
- ✅ **HTML (`index.html`)**: Botón de cerrar + mejor layout
- ✅ **CSS (`styles.css`)**: Estilos para botón `.huge`

---

## ⚙️ Requisitos

- ✅ Automatización Power BI lista desde `scripts/powerbi`
- ✅ Power BI Desktop **abierto** cuando corresponda al flujo TOM/XMLA
- ✅ Python 3.9+
- ✅ PowerShell 5.1+

---

## 💡 Pro Tips

1. **Deja Power BI abierto o cerrado, da lo mismo** – el sistema lo maneja
2. **Los pasos del pipeline son independientes** – si uno falla, puedes reintentar solo ese
3. **El historial se guarda en localStorage** – tu navegador recuerda los últimos 20 intentos
4. **Ideal para testing repetitivo** – ejecuta, valida, modifica, ejecuta de nuevo

---

**¡Listo! Ya no necesitas terminal para automatizar Power BI.** 🎉
