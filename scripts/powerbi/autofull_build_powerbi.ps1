param(
    [int]$Port = 65106,
    [string]$DatabaseName = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

function Import-AnalysisAssembly {
    param(
        [string]$AssemblyName,
        [string[]]$CandidatePaths
    )

    try {
        Add-Type -AssemblyName $AssemblyName -ErrorAction Stop
        return
    }
    catch {
    }

    foreach ($path in $CandidatePaths) {
        if (Test-Path $path) {
            try {
                Add-Type -Path $path -ErrorAction Stop
                return
            }
            catch {
            }
        }
    }

    throw "No se pudo cargar el ensamblado $AssemblyName"
}

function Normalize-Name {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "Campo"
    }

    $clean = ($Value -replace "[^a-zA-Z0-9_]+", "_").Trim("_")
    if ([string]::IsNullOrWhiteSpace($clean)) {
        return "Campo"
    }
    return $clean
}

function DaxIdent {
    param([string]$Name)
    return ($Name -replace "'", "''")
}

function DaxColumnRef {
    param(
        [string]$TableName,
        [string]$ColumnName
    )

    $safeTable = DaxIdent $TableName
    $safeCol = ($ColumnName -replace "]", "]]")
    return "'$safeTable'[$safeCol]"
}

function New-UniqueMeasureName {
    param(
        [object]$Table,
        [string]$BaseName
    )

    $candidate = $BaseName
    $index = 1

    while ($true) {
        $exists = $false
        foreach ($m in $Table.Measures) {
            if ($m.Name -ieq $candidate) {
                $exists = $true
                break
            }
        }

        if (-not $exists) {
            return $candidate
        }

        $index += 1
        $candidate = "${BaseName}_${index}"
    }
}

function Set-TableMeasure {
    param(
        [object]$Table,
        [string]$Name,
        [string]$Expression,
        [string]$DisplayFolder,
        [string]$FormatString = ""
    )

    $existing = $null
    foreach ($measure in $Table.Measures) {
        if ($measure.Name -ieq $Name) {
            $existing = $measure
            break
        }
    }

    if ($null -eq $existing) {
        $existing = New-Object Microsoft.AnalysisServices.Tabular.Measure
        $existing.Name = $Name
        $Table.Measures.Add($existing)
    }

    $existing.Expression = $Expression
    $existing.DisplayFolder = $DisplayFolder
    if (-not [string]::IsNullOrWhiteSpace($FormatString)) {
        $existing.FormatString = $FormatString
    }
}

function Should-SkipTable {
    param([object]$Table)

    if ($Table.Name -like "LocalDateTable_*") { return $true }
    if ($Table.Name -like "DateTableTemplate_*") { return $true }
    return $false
}

$assemblyRoots = @(
    "$env:ProgramFiles\Microsoft Power BI Desktop\bin",
    "$env:ProgramW6432\Microsoft Power BI Desktop\bin",
    "$env:ProgramFiles\Microsoft SQL Server\160\SDK\Assemblies",
    "$env:ProgramFiles\Microsoft SQL Server\150\SDK\Assemblies",
    "$env:ProgramFiles\Microsoft.NET\ADOMD.NET\160",
    "$env:ProgramFiles\Microsoft.NET\ADOMD.NET\150"
)

$localNugetRoot = Join-Path $PSScriptRoot "..\..\data\nuget"
if (Test-Path $localNugetRoot) {
    $nugetLibDirs = Get-ChildItem -Path $localNugetRoot -Directory -Filter "Microsoft.AnalysisServices.retail.amd64*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object {
            $libPath = Join-Path $_.FullName "lib"
            if (Test-Path $libPath) {
                Get-ChildItem -Path $libPath -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
            }
        }
    if ($nugetLibDirs) {
        $assemblyRoots += $nugetLibDirs
    }
}

Import-AnalysisAssembly -AssemblyName "Microsoft.AnalysisServices.Core" -CandidatePaths ($assemblyRoots | ForEach-Object { Join-Path $_ "Microsoft.AnalysisServices.Core.dll" })
Import-AnalysisAssembly -AssemblyName "Microsoft.AnalysisServices" -CandidatePaths ($assemblyRoots | ForEach-Object { Join-Path $_ "Microsoft.AnalysisServices.dll" })
Import-AnalysisAssembly -AssemblyName "Microsoft.AnalysisServices.Tabular" -CandidatePaths ($assemblyRoots | ForEach-Object { Join-Path $_ "Microsoft.AnalysisServices.Tabular.dll" })

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $PSScriptRoot "..\..\data\reference\autobuild"
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("DataSource=localhost:$Port")

try {
    $candidateDatabases = @()
    foreach ($db in $server.Databases) {
        if ($null -ne $db.Model) {
            $candidateDatabases += $db
        }
    }

    if ($candidateDatabases.Count -eq 0) {
        throw "No hay modelos tabulares disponibles en localhost:$Port"
    }

    $selectedDb = $null
    if ([string]::IsNullOrWhiteSpace($DatabaseName)) {
        $selectedDb = $candidateDatabases | Sort-Object { $_.Model.Tables.Count } -Descending | Select-Object -First 1
    }
    else {
        foreach ($db in $candidateDatabases) {
            if ($db.Name -ieq $DatabaseName -or $db.ID -ieq $DatabaseName) {
                $selectedDb = $db
                break
            }
        }
    }

    if ($null -eq $selectedDb) {
        throw "No se encontro base valida para auto full build"
    }

    $model = $selectedDb.Model
    if ($model.Tables.Count -eq 0) {
        throw "El modelo abierto no tiene tablas. Carga una fuente en Power BI y reintenta."
    }

    $createdCount = 0
    $tablesProcessed = 0
    $numericCatalog = @()
    $textCatalog = @()
    $dateCatalog = @()

    foreach ($table in $model.Tables) {
        if (Should-SkipTable -Table $table) {
            continue
        }

        $tablesProcessed += 1
        $safeTable = Normalize-Name $table.Name
        $folder = "AutoBuild/$safeTable"

        $rowsMeasure = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_Rows"
        Set-TableMeasure -Table $table -Name $rowsMeasure -Expression "COUNTROWS('$($table.Name)')" -DisplayFolder $folder -FormatString "#,0"
        $createdCount += 1

        foreach ($column in $table.Columns) {
            $safeCol = Normalize-Name $column.Name
            $colRef = DaxColumnRef -TableName $table.Name -ColumnName $column.Name

            $distinctName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Distinct"
            Set-TableMeasure -Table $table -Name $distinctName -Expression "DISTINCTCOUNT($colRef)" -DisplayFolder $folder -FormatString "#,0"
            $createdCount += 1

            if ($column -is [Microsoft.AnalysisServices.Tabular.DataColumn]) {
                $dtName = $column.DataType.ToString()

                if ($dtName -in @("Int64", "Decimal", "Double")) {
                    $sumName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Sum"
                    $avgName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Avg"
                    Set-TableMeasure -Table $table -Name $sumName -Expression "SUM($colRef)" -DisplayFolder $folder -FormatString "#,0.00"
                    Set-TableMeasure -Table $table -Name $avgName -Expression "AVERAGE($colRef)" -DisplayFolder $folder -FormatString "#,0.00"
                    $createdCount += 2

                    $numericCatalog += [pscustomobject]@{
                        table = $table.Name
                        column = $column.Name
                        sumMeasure = $sumName
                        avgMeasure = $avgName
                    }
                }
                elseif ($dtName -eq "DateTime") {
                    $dateCatalog += [pscustomobject]@{
                        table = $table.Name
                        column = $column.Name
                    }
                }
                elseif ($dtName -eq "String") {
                    $textCatalog += [pscustomobject]@{
                        table = $table.Name
                        column = $column.Name
                    }
                }
            }
        }
    }

    $model.SaveChanges()

    $themePath = Join-Path $OutputDir "autobuild_theme_moderno.json"
    $blueprintPath = Join-Path $OutputDir "AUTOBUILD_REPORT_BLUEPRINT.md"

    $theme = @'
{
  "name": "AutoBuild Moderno",
  "foreground": "#1F2937",
  "background": "#F7F8FA",
  "tableAccent": "#0E7490",
  "dataColors": ["#0E7490", "#2563EB", "#0F766E", "#DC2626", "#CA8A04", "#7C3AED", "#475569", "#0891B2"],
  "textClasses": {
    "title": { "fontFace": "Segoe UI Semibold", "fontSize": 14 },
    "callout": { "fontFace": "Segoe UI", "fontSize": 28 },
    "header": { "fontFace": "Segoe UI Semibold", "fontSize": 12 },
    "label": { "fontFace": "Segoe UI", "fontSize": 10 }
  },
  "visualStyles": {
    "*": {
      "*": {
        "title": [{ "show": true, "color": { "solid": { "color": "#111827" } }, "fontSize": 12 }],
        "background": [{ "show": true, "color": { "solid": { "color": "#FFFFFF" } }, "transparency": 0 }],
        "border": [{ "show": true, "radius": 6, "color": { "solid": { "color": "#E5E7EB" } } }]
      }
    }
  }
}
'@
    Set-Content -Path $themePath -Value $theme -Encoding UTF8

    $topNumeric = $numericCatalog | Select-Object -First 12
    $topDate = $dateCatalog | Select-Object -First 3
    $topText = $textCatalog | Select-Object -First 8

    $md = @()
    $md += "# AutoBuild Report Blueprint"
    $md += ""
    $md += "## Estado"
    $md += "- Base seleccionada: $($selectedDb.Name)"
    $md += "- Tablas procesadas: $tablesProcessed"
    $md += "- Medidas generadas: $createdCount"
    $md += "- Tema sugerido: $themePath"
    $md += ""
    $md += "## Buenas practicas aplicadas"
    $md += "- Medidas por tabla con carpeta AutoBuild/<Tabla>."
    $md += "- KPI base por conteo de filas y métricas numéricas agregadas."
    $md += "- Formato numérico estándar para consistencia visual."
    $md += ""
    $md += "## Pagina 1 - Resumen Ejecutivo"
    $md += "- 4 tarjetas KPI con medidas AB_*_Rows de tablas principales."
    $md += "- 1 gráfico de columnas con la principal métrica SUM por categoría top."
    $md += "- 1 segmentador de fecha (si existe columna DateTime)."
    $md += ""
    $md += "## Pagina 2 - Tendencias"
    $md += "- 1 línea temporal usando fecha + medida SUM o Rows."
    $md += "- 1 área apilada por categoría clave."
    $md += ""
    $md += "## Pagina 3 - Detalle Analítico"
    $md += "- Matriz con categorías (texto) y medidas SUM/AVG."
    $md += "- Tabla detallada con drill-through recomendado."
    $md += ""
    $md += "## Campos recomendados detectados"
    $md += ""
    $md += "### Numéricos"
    foreach ($n in $topNumeric) {
        $md += "- $($n.table).$($n.column) -> $($n.sumMeasure), $($n.avgMeasure)"
    }
    $md += ""
    $md += "### Fechas"
    foreach ($d in $topDate) {
        $md += "- $($d.table).$($d.column)"
    }
    $md += ""
    $md += "### Categóricos"
    foreach ($t in $topText) {
        $md += "- $($t.table).$($t.column)"
    }
    $md += ""
    $md += "## Paso final en Power BI (1 minuto)"
    $md += "1. Vista -> Temas -> Examinar temas -> selecciona autobuild_theme_moderno.json"
    $md += "2. Crea 3 páginas con los bloques sugeridos arriba"
    $md += "3. Usa medidas AB_* del panel Campos (carpetas AutoBuild)"

    Set-Content -Path $blueprintPath -Value ($md -join "`r`n") -Encoding UTF8

    Write-Host "AUTOFULL_OK: SI"
    Write-Host "BASE_SELECCIONADA: $($selectedDb.Name)"
    Write-Host "TABLAS_PROCESADAS: $tablesProcessed"
    Write-Host "MEDIDAS_GENERADAS: $createdCount"
    Write-Host "THEME_JSON: $themePath"
    Write-Host "BLUEPRINT_MD: $blueprintPath"
}
catch {
    Write-Host "AUTOFULL_OK: NO"
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $server.Disconnect()
}
