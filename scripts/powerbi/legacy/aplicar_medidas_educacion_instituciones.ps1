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

function Find-TableByName {
    param(
        [object]$Model,
        [string]$Name
    )

    foreach ($table in $Model.Tables) {
        if ($table.Name -ieq $Name) {
            return $table
        }
    }

    return $null
}

function Find-ColumnByName {
    param(
        [object]$Table,
        [string]$Name
    )

    foreach ($column in $Table.Columns) {
        if ($column.Name -ieq $Name) {
            return $column
        }
    }

    return $null
}

function Set-ModelMeasure {
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

    $action = "actualizada"
    if ($null -eq $existing) {
        $existing = New-Object Microsoft.AnalysisServices.Tabular.Measure
        $existing.Name = $Name
        $Table.Measures.Add($existing)
        $action = "creada"
    }

    $existing.Expression = $Expression
    $existing.DisplayFolder = $DisplayFolder
    return $action
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
        foreach ($db in $candidateDatabases) {
            $factCandidate = Find-TableByName -Model $db.Model -Name "Hecho_Participacion_General"
            if ($null -ne $factCandidate) {
                $selectedDb = $db
                break
            }
        }
    }
    else {
        foreach ($db in $candidateDatabases) {
            if ($db.Name -ieq $DatabaseName) {
                $selectedDb = $db
                break
            }
        }
    }

    if ($null -eq $selectedDb) {
        throw "No se encontro una base valida para crear medidas de instituciones educativas"
    }

    $model = $selectedDb.Model
    $factTable = Find-TableByName -Model $model -Name "Hecho_Participacion_General"
    $medidasTable = Find-TableByName -Model $model -Name "_Medidas"

    if ($null -eq $factTable) {
        throw "No existe la tabla Hecho_Participacion_General en el modelo seleccionado"
    }

    if ($null -eq $medidasTable) {
        throw "No existe la tabla _Medidas. Creala en el modelo y reintenta"
    }

    $requiredColumns = @(
        "institucion_educativa_norm",
        "comuna_institucion_educativa_cod",
        "bloque_educacion",
        "seccion_tablero",
        "comuna_cod"
    )

    $missing = @()
    foreach ($col in $requiredColumns) {
        if ($null -eq (Find-ColumnByName -Table $factTable -Name $col)) {
            $missing += $col
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host "BLOQUEO_REFRESH: SI"
        Write-Host "MOTIVO: El modelo live aun no expone columnas nuevas requeridas para medidas educativas"
        Write-Host ("COLUMNAS_FALTANTES: " + ($missing -join ", "))
        Write-Host "ACCION_REQUERIDA: refrescar el PBIX (Inicio > Refrescar) y reintentar este script"
        exit 2
    }

    $displayFolder = "Educativa/Instituciones"
    $measureDefinitions = [ordered]@{
        GenF_Edu_Instituciones_Unicas = @'
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
RETURN
    CALCULATE(
        DISTINCTCOUNT(Hecho_Participacion_General[institucion_educativa_norm]),
        Hecho_Participacion_General[seccion_tablero] = "Educativa",
        NOT(ISBLANK(Hecho_Participacion_General[institucion_educativa_norm])),
        REMOVEFILTERS(Hecho_Participacion_General[comuna_cod]),
        KEEPFILTERS(TREATAS(_ComunasSeleccionadas, Hecho_Participacion_General[comuna_institucion_educativa_cod]))
    )
'@
        GenF_Edu_Instituciones_Media = @'
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
RETURN
    CALCULATE(
        DISTINCTCOUNT(Hecho_Participacion_General[institucion_educativa_norm]),
        Hecho_Participacion_General[seccion_tablero] = "Educativa",
        Hecho_Participacion_General[bloque_educacion] = "Basica Media",
        NOT(ISBLANK(Hecho_Participacion_General[institucion_educativa_norm])),
        REMOVEFILTERS(Hecho_Participacion_General[comuna_cod]),
        KEEPFILTERS(TREATAS(_ComunasSeleccionadas, Hecho_Participacion_General[comuna_institucion_educativa_cod]))
    )
'@
        GenF_Edu_Instituciones_Superior = @'
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
RETURN
    CALCULATE(
        DISTINCTCOUNT(Hecho_Participacion_General[institucion_educativa_norm]),
        Hecho_Participacion_General[seccion_tablero] = "Educativa",
        Hecho_Participacion_General[bloque_educacion] = "Educacion Superior",
        NOT(ISBLANK(Hecho_Participacion_General[institucion_educativa_norm])),
        REMOVEFILTERS(Hecho_Participacion_General[comuna_cod]),
        KEEPFILTERS(TREATAS(_ComunasSeleccionadas, Hecho_Participacion_General[comuna_institucion_educativa_cod]))
    )
'@
        GenF_Edu_Instituciones_PrimeraInfancia = @'
VAR _ComunasSeleccionadas = VALUES(Dim_Comuna[comuna_cod])
RETURN
    CALCULATE(
        DISTINCTCOUNT(Hecho_Participacion_General[institucion_educativa_norm]),
        Hecho_Participacion_General[seccion_tablero] = "Educativa",
        Hecho_Participacion_General[bloque_educacion] = "Instituciones Primera Infancia",
        NOT(ISBLANK(Hecho_Participacion_General[institucion_educativa_norm])),
        REMOVEFILTERS(Hecho_Participacion_General[comuna_cod]),
        KEEPFILTERS(TREATAS(_ComunasSeleccionadas, Hecho_Participacion_General[comuna_institucion_educativa_cod]))
    )
'@
    }

    $measureActions = @()
    foreach ($measureName in $measureDefinitions.Keys) {
        $action = Set-ModelMeasure -Table $medidasTable -Name $measureName -Expression $measureDefinitions[$measureName] -DisplayFolder $displayFolder
        $measureActions += [pscustomobject]@{
            medida = $measureName
            accion = $action
            displayFolder = $displayFolder
        }
    }

    $model.SaveChanges()

    Write-Host "BLOQUEO_REFRESH: NO"
    Write-Host "BASE_SELECCIONADA: $($selectedDb.Name)"
    Write-Host "MEDIDAS_CREADAS_O_ACTUALIZADAS:"
    $measureActions | Format-Table -AutoSize | Out-String | Write-Host
}
catch {
    Write-Host "BLOQUEO_REFRESH: NO"
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $server.Disconnect()
}
