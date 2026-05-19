# Paquete de Publicacion - Dashboard DAGRD

## Archivo PBIX recomendado para publicar
- tableroDAGRD.pbix

## Checklist de publicacion en nube
1. Abrir el PBIX recomendado.
2. Verificar origen de datos apunte a los archivos de 02_datos_modelo en la ruta local de quien publica.
3. Actualizar modelo (Refresh).
4. Publicar al workspace/carpeta del equipo (OneDrive/Drive segun flujo).
5. Seguir la guia completa en 05_documentacion/GUIA_PUBLICACION_NUBE_PASO_A_PASO.md.

## Contenido incluido
- 01_pbix/tableroDAGRD.pbix
- 02_datos_modelo/Modelo_Reporte_Paginas_2026.xlsx
- 02_datos_modelo/Dim_Comites_Comisiones_2026.csv
- 03_fuente_original/Reporte de actividades equipo social 2026 (1).xlsx
- 05_documentacion/GUIA_PUBLICACION_NUBE_PASO_A_PASO.md

## Notas
- La medida Num_Comites_Comisiones ya quedo ajustada para excluir el valor generico "TODOS LOS COMITES Y COMISIONES".
- Valor esperado de control para Num_Comites_Comisiones (sin filtros): 89.
- Actualizacion 2026-03-27: paquete sincronizado con el Excel base mas reciente `Reporte de actividades equipo social 2026 (1).xlsx` y ETL regenerado.
- Actualizacion 2026-04-14: paquete resincronizado con ETL completo; `Modelo_Reporte_Paginas_2026.xlsx` incluye hojas criticas (`Dim_SATC`, `Dim_SATC_Relaciones`, `Dim_Semilleros`, `Dim_Semilleros_Confiable`, `Dim_Comites_Comisiones_2026`) para evitar errores de clave al refrescar en Power BI.
- Actualizacion 2026-04-14 (PBIX): se reemplaza el tablero de entrega por `tableroDAGRD.pbix`, que es la version vigente en uso.
