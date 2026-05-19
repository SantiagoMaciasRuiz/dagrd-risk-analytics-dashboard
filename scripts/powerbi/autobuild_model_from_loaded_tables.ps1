param(
    [int]$Port = 65106,
    [string]$DatabaseName = ""
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
        [string]$DisplayFolder
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
        throw "No se encontro base valida para autobuild"
    }

    $model = $selectedDb.Model
    if ($model.Tables.Count -eq 0) {
        throw "El modelo abierto no tiene tablas. Carga una fuente en Power BI y reintenta."
    }

    $createdCount = 0
    $updatedTables = @()

    foreach ($table in $model.Tables) {
        if (Should-SkipTable -Table $table) {
            continue
        }

        $safeTable = Normalize-Name $table.Name
        $folder = "AutoBuild/$safeTable"

        $rowsMeasure = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_Rows"
        Set-TableMeasure -Table $table -Name $rowsMeasure -Expression "COUNTROWS('$($table.Name)')" -DisplayFolder $folder
        $createdCount += 1

        foreach ($column in $table.Columns) {
            $safeCol = Normalize-Name $column.Name

            $distinctName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Distinct"
            Set-TableMeasure -Table $table -Name $distinctName -Expression "DISTINCTCOUNT('$($table.Name)'[$($column.Name)])" -DisplayFolder $folder
            $createdCount += 1

            if ($column -is [Microsoft.AnalysisServices.Tabular.DataColumn]) {
                $dtName = $column.DataType.ToString()
                if ($dtName -in @("Int64", "Decimal", "Double")) {
                    $sumName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Sum"
                    $avgName = New-UniqueMeasureName -Table $table -BaseName "AB_${safeTable}_${safeCol}_Avg"
                    Set-TableMeasure -Table $table -Name $sumName -Expression "SUM('$($table.Name)'[$($column.Name)])" -DisplayFolder $folder
                    Set-TableMeasure -Table $table -Name $avgName -Expression "AVERAGE('$($table.Name)'[$($column.Name)])" -DisplayFolder $folder
                    $createdCount += 2
                }
            }
        }

        $updatedTables += $table.Name
    }

    $model.SaveChanges()

    Write-Host "AUTOBUILD_OK: SI"
    Write-Host "BASE_SELECCIONADA: $($selectedDb.Name)"
    Write-Host "TABLAS_ACTUALIZADAS: $($updatedTables.Count)"
    Write-Host "MEDIDAS_GENERADAS: $createdCount"
}
catch {
    Write-Host "AUTOBUILD_OK: NO"
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $server.Disconnect()
}
