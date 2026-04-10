# Guia paso a paso para publicar en nube (Power BI Service)

## 0) Archivos necesarios del paquete
Usa estos archivos del entregable:
- 01_pbix/Tablero Equipo Social DAGRD.pbix
- 02_datos_modelo/Modelo_Reporte_Paginas_2026.xlsx
- 02_datos_modelo/Dim_Comites_Comisiones_2026.csv
- 03_fuente_original/Reporte de actividades equipo social 2026 (1).xlsx (soporte)

## 1) Preparar carpeta local antes de publicar
1. Crea una carpeta local, por ejemplo: C:/DAGRD/Publicacion_Dashboard/
2. Copia dentro de esa carpeta las subcarpetas 01_pbix y 02_datos_modelo.
3. Verifica que existan estos archivos:
   - C:/DAGRD/Publicacion_Dashboard/01_pbix/Tablero Equipo Social DAGRD.pbix
   - C:/DAGRD/Publicacion_Dashboard/02_datos_modelo/Modelo_Reporte_Paginas_2026.xlsx
   - C:/DAGRD/Publicacion_Dashboard/02_datos_modelo/Dim_Comites_Comisiones_2026.csv

## 2) Abrir y validar en Power BI Desktop
1. Abre Power BI Desktop.
2. Abre el archivo 01_pbix/Tablero Equipo Social DAGRD.pbix.
3. Ve a Transformar datos > Configuracion de origen de datos.
4. Si alguna ruta esta rota, edita la ruta para apuntar a 02_datos_modelo de tu carpeta local.
5. Ejecuta Actualizar (Refresh).
6. Validacion minima recomendada:
   - Tarjeta Num_Comites_Comisiones debe mostrar 101 sin filtros.

## 3) Publicar al servicio de Power BI (nube)
1. En Power BI Desktop, clic en Publicar.
2. Selecciona el workspace destino del equipo.
3. Confirma que se publique el dataset/modelo semantico y el reporte.

## 4) Configurar credenciales y actualizacion en Power BI Service
1. En Power BI Service (app.powerbi.com), abre el workspace.
2. Entra al modelo semantico publicado (dataset).
3. Ve a Configuracion > Credenciales de origen de datos.
4. Configura autenticacion para los origenes de archivo usados.
5. Ve a Configuracion > Actualizacion programada.
6. Activa actualizacion programada (si aplica) y define horario.

## 5) Si usaran OneDrive/SharePoint para los archivos de datos
1. Suban Modelo_Reporte_Paginas_2026.xlsx y Dim_Comites_Comisiones_2026.csv a una carpeta de OneDrive/SharePoint del equipo.
2. En Desktop, cambia origenes para apuntar a la ruta web o conector SharePoint Folder/OneDrive segun politica del equipo.
3. Actualiza y valida.
4. Publica nuevamente para que el dataset en nube quede enlazado al origen colaborativo.

## 6) Checklist final de entrega
1. Reporte abre correctamente en Power BI Service.
2. Visuales cargan sin error.
3. Num_Comites_Comisiones = 101 (sin filtros).
4. Refresh manual exitoso en el servicio.
5. Refresh programado habilitado (si aplica).

## 7) Solucion de problemas rapida
1. Error de credenciales: reconfigura Credenciales de origen de datos en el dataset.
2. Error de ruta: en Desktop corrige rutas y republica.
3. Visual en blanco: confirma que el refresh termine sin errores.
4. Valor distinto a 101 en comites/comisiones: revisa filtros del visual/pagina/reporte.
