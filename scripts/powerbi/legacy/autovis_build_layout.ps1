param(
    [int]$Port = 65106,
    [string]$DatabaseName = "",
    [string]$LayoutPath = ""
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

function Detect-TextEncoding {
    param([byte[]]$Bytes)

    if ($Bytes.Length -ge 2) {
        if ($Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) { return [Text.Encoding]::Unicode }
        if ($Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF) { return [Text.Encoding]::BigEndianUnicode }
    }

    if ($Bytes.Length -ge 4) {
        if ($Bytes[0] -eq 0x00 -and $Bytes[1] -ne 0x00) { return [Text.Encoding]::BigEndianUnicode }
        if ($Bytes[0] -ne 0x00 -and $Bytes[1] -eq 0x00) { return [Text.Encoding]::Unicode }
    }

    return [Text.Encoding]::UTF8
}

function ConvertTo-Hashtable {
    param($Obj)

    if ($null -eq $Obj) {
        return $null
    }

    if ($Obj -is [System.Collections.IDictionary]) {
        $h = @{}
        foreach ($k in $Obj.Keys) {
            $h[$k] = ConvertTo-Hashtable $Obj[$k]
        }
        return $h
    }

    if ($Obj.PSObject -and $Obj.PSObject.Properties.Count -gt 0) {
        $h = @{}
        foreach ($p in $Obj.PSObject.Properties) {
            $h[$p.Name] = ConvertTo-Hashtable $p.Value
        }
        return $h
    }

    if ($Obj -is [System.Collections.IEnumerable] -and -not ($Obj -is [string])) {
        $arr = @()
        foreach ($i in $Obj) {
            $arr += ,(ConvertTo-Hashtable $i)
        }
        return $arr
    }

    return $Obj
}

function New-CardPrototypeQuery {
    param(
        [string]$TableName,
        [string]$MeasureName
    )

    return @{
        Version = 2
        From = @(
            @{
                Name = "t"
                Entity = $TableName
                Type = 0
            }
        )
        Select = @(
            @{
                Measure = @{
                    Expression = @{
                        SourceRef = @{
                            Source = "t"
                        }
                    }
                    Property = $MeasureName
                }
                Name = "$TableName.$MeasureName"
                NativeReferenceName = $MeasureName
            }
        )
        OrderBy = @(
            @{
                Direction = 2
                Expression = @{
                    Measure = @{
                        Expression = @{
                            SourceRef = @{
                                Source = "t"
                            }
                        }
                        Property = $MeasureName
                    }
                }
            }
        )
    }
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

if ([string]::IsNullOrWhiteSpace($LayoutPath)) {
    $LayoutPath = Join-Path $PSScriptRoot "..\..\Tableros\_pbix_extract_temp\Report\Layout"
}

if (-not (Test-Path $LayoutPath)) {
    throw "No existe Layout para autovis: $LayoutPath"
}

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
        throw "No se encontro base valida para autovis"
    }

    $measureCatalog = @()
    foreach ($t in $selectedDb.Model.Tables) {
        foreach ($m in $t.Measures) {
            if ($m.Name -like "AB_*") {
                $measureCatalog += [pscustomobject]@{
                    table = $t.Name
                    measure = $m.Name
                }
            }
        }
    }

    if ($measureCatalog.Count -eq 0) {
        throw "No hay medidas AB_* en el modelo. Ejecuta /autobuild o /autofull primero."
    }

    $picked = $measureCatalog | Select-Object -First 6
    if ($picked.Count -lt 6) {
        $extra = @()
        while (($picked.Count + $extra.Count) -lt 6) {
            $extra += $measureCatalog[0]
        }
        $picked = @($picked + $extra)
    }

    $rawBytes = [IO.File]::ReadAllBytes($LayoutPath)
    $enc = Detect-TextEncoding -Bytes $rawBytes
    $rawText = $enc.GetString($rawBytes)
    $layoutObj = $rawText | ConvertFrom-Json
    $layout = ConvertTo-Hashtable $layoutObj

    if (-not $layout.ContainsKey("sections") -or $layout["sections"].Count -eq 0) {
        throw "Layout sin secciones, no se puede inyectar página automática."
    }

    $cardTemplate = $null
    foreach ($s in $layout["sections"]) {
        foreach ($vc in ($s["visualContainers"] | ForEach-Object { $_ })) {
            if (-not $vc.ContainsKey("config")) { continue }
            try {
                $cfg = ConvertTo-Hashtable (($vc["config"] | ConvertFrom-Json))
                if (($cfg["singleVisual"]["visualType"]) -eq "card") {
                    $cardTemplate = ConvertTo-Hashtable $vc
                    break
                }
            }
            catch {
            }
        }
        if ($null -ne $cardTemplate) { break }
    }

    if ($null -eq $cardTemplate) {
        throw "No se encontro plantilla de visual tipo card en Layout."
    }

    $sectionTemplate = ConvertTo-Hashtable $layout["sections"][0]
    $newSection = ConvertTo-Hashtable $sectionTemplate
    $newSection["name"] = "AutoVisSection_" + [DateTime]::Now.ToString("yyyyMMdd_HHmmss")
    $newSection["displayName"] = "AutoVis IA"
    $newSection["ordinal"] = ($layout["sections"] | Measure-Object).Count
    $newSection["visualContainers"] = @()
    $newSection["filters"] = "[]"

    $xStart = 30
    $yStart = 60
    $cardW = 390
    $cardH = 220
    $gapX = 25
    $gapY = 30

    for ($i = 0; $i -lt 6; $i++) {
        $item = $picked[$i]
        $row = [math]::Floor($i / 3)
        $col = $i % 3

        $vc = ConvertTo-Hashtable $cardTemplate
        $vc["x"] = $xStart + ($col * ($cardW + $gapX))
        $vc["y"] = $yStart + ($row * ($cardH + $gapY))
        $vc["z"] = 10 + $i
        $vc["width"] = $cardW
        $vc["height"] = $cardH
        $vc["filters"] = "[]"

        $cfg = ConvertTo-Hashtable (($vc["config"] | ConvertFrom-Json))
        $cfg["name"] = "AutoVisCard_" + ($i + 1)

        if (-not $cfg.ContainsKey("singleVisual")) {
            $cfg["singleVisual"] = @{}
        }
        $cfg["singleVisual"]["visualType"] = "card"
        $cfg["singleVisual"]["prototypeQuery"] = New-CardPrototypeQuery -TableName $item.table -MeasureName $item.measure
        $cfg["singleVisual"]["projections"] = @{ Values = @(@{ queryRef = "$($item.table).$($item.measure)" }) }

        $vcObj = $cfg["singleVisual"]["vcObjects"]
        if ($null -ne $vcObj -and $vcObj.ContainsKey("title")) {
            $titleArr = $vcObj["title"]
            if ($titleArr -is [System.Collections.IEnumerable] -and $titleArr.Count -gt 0) {
                $titleEntry = $titleArr[0]
                if (-not $titleEntry.ContainsKey("properties")) {
                    $titleEntry["properties"] = @{}
                }
                $titleEntry["properties"]["text"] = @{ expr = @{ Literal = @{ Value = "'$($item.measure)'" } } }
                $titleEntry["properties"]["show"] = @{ expr = @{ Literal = @{ Value = "true" } } }
            }
        }

        $vc["config"] = ($cfg | ConvertTo-Json -Depth 100 -Compress)
        $newSection["visualContainers"] += ,$vc
    }

    $layout["sections"] += ,$newSection

    $jsonOut = ($layout | ConvertTo-Json -Depth 100 -Compress)
    [IO.File]::WriteAllText($LayoutPath, $jsonOut, $enc)

    Write-Host "AUTOVIS_OK: SI"
    Write-Host "BASE_SELECCIONADA: $($selectedDb.Name)"
    Write-Host "MEDIDAS_USADAS: $($picked.Count)"
    Write-Host "LAYOUT_ACTUALIZADO: $LayoutPath"
    Write-Host "SECCION_AGREGADA: $($newSection['displayName'])"
}
catch {
    Write-Host "AUTOVIS_OK: NO"
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
finally {
    $server.Disconnect()
}
