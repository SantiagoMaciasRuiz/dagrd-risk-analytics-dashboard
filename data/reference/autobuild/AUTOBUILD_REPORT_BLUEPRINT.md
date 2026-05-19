# AutoBuild Report Blueprint

## Estado
- Base seleccionada: f401fea8-e6ce-4415-be68-62143b06edad
- Tablas procesadas: 1
- Medidas generadas: 16
- Tema sugerido: data/reference/autobuild/autobuild_theme_moderno.json

## Buenas practicas aplicadas
- Medidas por tabla con carpeta AutoBuild/<Tabla>.
- KPI base por conteo de filas y métricas numéricas agregadas.
- Formato numérico estándar para consistencia visual.

## Pagina 1 - Resumen Ejecutivo
- 4 tarjetas KPI con medidas AB_*_Rows de tablas principales.
- 1 gráfico de columnas con la principal métrica SUM por categoría top.
- 1 segmentador de fecha (si existe columna DateTime).

## Pagina 2 - Tendencias
- 1 línea temporal usando fecha + medida SUM o Rows.
- 1 área apilada por categoría clave.

## Pagina 3 - Detalle Analítico
- Matriz con categorías (texto) y medidas SUM/AVG.
- Tabla detallada con drill-through recomendado.

## Campos recomendados detectados

### Numéricos
- customers-10000.Index -> AB_customers_10000_Index_Sum_2, AB_customers_10000_Index_Avg_2

### Fechas
- customers-10000.Subscription Date

### Categóricos
- customers-10000.Customer Id
- customers-10000.First Name
- customers-10000.Last Name
- customers-10000.Company
- customers-10000.City
- customers-10000.Country
- customers-10000.Phone 1
- customers-10000.Phone 2

## Paso final en Power BI (1 minuto)
1. Vista -> Temas -> Examinar temas -> selecciona autobuild_theme_moderno.json
2. Crea 3 páginas con los bloques sugeridos arriba
3. Usa medidas AB_* del panel Campos (carpetas AutoBuild)