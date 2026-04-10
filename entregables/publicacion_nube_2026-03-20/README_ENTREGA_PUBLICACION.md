# Paquete de Publicacion - Dashboard DAGRD

## Archivo PBIX recomendado para publicar
- Tablero Equipo Social DAGRD.pbix

## Checklist de publicacion en nube
1. Abrir el PBIX recomendado.
2. Verificar origen de datos apunte a los archivos de 02_datos_modelo en la ruta local de quien publica.
3. Actualizar modelo (Refresh).
4. Publicar al workspace/carpeta del equipo (OneDrive/Drive segun flujo).
5. Seguir la guia completa en 05_documentacion/GUIA_PUBLICACION_NUBE_PASO_A_PASO.md.

## Contenido incluido
- 01_pbix/Tablero Equipo Social DAGRD.pbix
- 02_datos_modelo/Modelo_Reporte_Paginas_2026.xlsx
- 02_datos_modelo/Dim_Comites_Comisiones_2026.csv
- 03_fuente_original/Reporte de actividades equipo social 2026 (1).xlsx
- 05_documentacion/GUIA_PUBLICACION_NUBE_PASO_A_PASO.md

## Notas
- La medida Num_Comites_Comisiones ya quedo ajustada para excluir el valor generico "TODOS LOS COMITES Y COMISIONES".
- Valor esperado de control para Num_Comites_Comisiones (sin filtros): 89.
- Actualizacion 2026-03-27: paquete sincronizado con el Excel base mas reciente `Reporte de actividades equipo social 2026 (1).xlsx` y ETL regenerado.
