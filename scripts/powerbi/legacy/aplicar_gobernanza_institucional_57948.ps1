param(
    [int]$Port = 57948,
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

function Find-MeasureByName {
    param(
        [object]$Model,
        [string]$Name
    )

    foreach ($table in $Model.Tables) {
        foreach ($measure in $table.Measures) {
            if ($measure.Name -ieq $Name) {
                return $measure
            }
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
    "$env:ProgramFiles\\Microsoft Power BI Desktop\\bin",
    "$env:ProgramFiles\\Microsoft SQL Server\\160\\SDK\\Assemblies",
    "$env:ProgramFiles\\Microsoft SQL Server\\150\\SDK\\Assemblies",
    "$env:ProgramFiles\\Microsoft.NET\\ADOMD.NET\\160",
    "$env:ProgramFiles\\Microsoft.NET\\ADOMD.NET\\150"
)

$localNugetRoot = Join-Path $PSScriptRoot "..\\..\\data\\nuget"
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
Import-AnalysisAssembly -AssemblyName "Microsoft.AnalysisServices.AdomdClient" -CandidatePaths ($assemblyRoots | ForEach-Object { Join-Path $_ "Microsoft.AnalysisServices.AdomdClient.dll" })

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
        throw "No se encontro una base valida para ejecutar medidas institucionales"
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

    $ambitoCol = Find-ColumnByName -Table $factTable -Name "ambito_institucional"
    $subbloqueCol = Find-ColumnByName -Table $factTable -Name "subbloque_institucional"

    if ($null -eq $ambitoCol -or $null -eq $subbloqueCol) {
        Write-Host "BLOQUEO_REFRESH: SI"
        Write-Host "MOTIVO: El modelo aun no expone Hecho_Participacion_General[ambito_institucional] y/o [subbloque_institucional]"
        Write-Host "ACCION_REQUERIDA: Ejecutar Refresh del PBIX activo y reintentar"
        exit 2
    }

    $genfMeasure = Find-MeasureByName -Model $model -Name "GenF_Institucional_Actividades"
    if ($null -eq $genfMeasure) {
        throw "No existe la medida GenF_Institucional_Actividades"
    }

    $displayFolder = "Institucional/Gobernanza"
    $measureDefinitions = [ordered]@{
        InstExt_Actividades = 'CALCULATE(COUNTROWS(Hecho_Participacion_General), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "Institucional Externa")'
        InstExt_Participaciones = 'CALCULATE(SUM(Hecho_Participacion_General[participantes]), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "Institucional Externa")'
        IntDAGRD_Actividades = 'CALCULATE(COUNTROWS(Hecho_Participacion_General), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "Interna DAGRD")'
        IntDAGRD_Participaciones = 'CALCULATE(SUM(Hecho_Participacion_General[participantes]), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "Interna DAGRD")'
        PDLPP_Actividades = 'CALCULATE(COUNTROWS(Hecho_Participacion_General), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "PDL y PP")'
        PDLPP_Participaciones = 'CALCULATE(SUM(Hecho_Participacion_General[participantes]), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[ambito_institucional] = "PDL y PP")'
        Inst_Ambiguas_Articulacion_Actividades = 'CALCULATE(COUNTROWS(Hecho_Participacion_General), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[subbloque_institucional] IN {"Articulacion masiva comunitaria sin detalle", "Articulacion coordinacion DAGRD sin detalle", "Articulacion sin detalle no PDD", "Articulacion sin detalle por depurar"})'
        Inst_Ambiguas_Articulacion_Participaciones = 'CALCULATE(SUM(Hecho_Participacion_General[participantes]), Hecho_Participacion_General[seccion_tablero] = "Institucional", Hecho_Participacion_General[subbloque_institucional] IN {"Articulacion masiva comunitaria sin detalle", "Articulacion coordinacion DAGRD sin detalle", "Articulacion sin detalle no PDD", "Articulacion sin detalle por depurar"})'
        Ctl_Inst_NoMezcla_OK = 'IF([GenF_Institucional_Actividades] = [InstExt_Actividades] + [IntDAGRD_Actividades] + [PDLPP_Actividades], "SI", "NO")'
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

    $conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port;Initial Catalog=$($selectedDb.Name)")
    $conn.Open()

    try {
$query = @"
EVALUATE
ROW(
    ""InstExt_Actividades"", [InstExt_Actividades],
    ""InstExt_Participaciones"", [InstExt_Participaciones],
    ""IntDAGRD_Actividades"", [IntDAGRD_Actividades],
    ""IntDAGRD_Participaciones"", [IntDAGRD_Participaciones],
    ""PDLPP_Actividades"", [PDLPP_Actividades],
    ""PDLPP_Participaciones"", [PDLPP_Participaciones],
    ""Inst_Ambiguas_Articulacion_Actividades"", [Inst_Ambiguas_Articulacion_Actividades],
    ""Inst_Ambiguas_Articulacion_Participaciones"", [Inst_Ambiguas_Articulacion_Participaciones],
    ""Ctl_Inst_NoMezcla_OK"", [Ctl_Inst_NoMezcla_OK]
)
"@

        $cmd = $conn.CreateCommand()
        $cmd.CommandText = $query
        $reader = $cmd.ExecuteReader()

        if (-not $reader.Read()) {
            throw "La consulta de validacion no devolvio filas"
        }

        $validationRow = [ordered]@{}
        for ($i = 0; $i -lt $reader.FieldCount; $i++) {
            $colName = $reader.GetName($i)
            $colValue = $null
            if (-not $reader.IsDBNull($i)) {
                $colValue = $reader.GetValue($i)
            }
            $validationRow[$colName] = $colValue
        }

        $expected = [ordered]@{
            InstExt_Actividades = 881
            InstExt_Participaciones = 35434
            IntDAGRD_Actividades = 519
            IntDAGRD_Participaciones = 2832
            PDLPP_Actividades = 138
            PDLPP_Participaciones = 4017
            Ctl_Inst_NoMezcla_OK = "SI"
        }

        $checks = @()
        $allOk = $true
        foreach ($key in $expected.Keys) {
            $actual = $validationRow[$key]
            $target = $expected[$key]
            $ok = "$actual" -eq "$target"
            if (-not $ok) {
                $allOk = $false
            }
            $checks += [pscustomobject]@{
                medida = $key
                actual = $actual
                esperado = $target
                ok = if ($ok) { "SI" } else { "NO" }
            }
        }

        Write-Host "BLOQUEO_REFRESH: NO"
        Write-Host "BASE_SELECCIONADA: $($selectedDb.Name)"
        Write-Host "MEDIDAS_CREADAS_O_ACTUALIZADAS:"
        $measureActions | Format-Table -AutoSize | Out-String | Write-Host

        Write-Host "VALIDACION_ROW:"
        ([pscustomobject]$validationRow | ConvertTo-Json -Compress) | Write-Host

        Write-Host "VALIDACION_ESPERADOS:"
        $checks | Format-Table -AutoSize | Out-String | Write-Host

        Write-Host ("CTL_GLOBAL_VALIDACION: " + $(if ($allOk) { "SI" } else { "NO" }))
    }
    finally {
        if ($null -ne $conn) {
            $conn.Close()
        }
    }
}
catch {
    Write-Host "BLOQUEO_REFRESH: NO"
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $server.Disconnect()
}
