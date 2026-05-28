<#
Short helper to run the ETL pipeline from project root using the project venv.
Usage:
  .\run_etl_full.ps1            # run ETL only
    .\run_etl_full.ps1 -Repair    # compatible alias; repair now runs after ETL by default
# Optional:
#   .\run_etl_full.ps1 -ClosePowerBI -OpenPowerBI
#>

param(
    [switch]$Repair,
    [switch]$ClosePowerBI,
    [switch]$OpenPowerBI
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot '..\..')
Set-Location $repoRoot

# Normalizar nombre del archivo fuente "Reporte de actividades..."
$sourceDir = Join-Path $PWD "data\source"
$expectedName = "Reporte de actividades equipo social 2026 (1).xlsx"
$expectedPath = Join-Path $sourceDir $expectedName

if (Test-Path $sourceDir) {
    $candidates = Get-ChildItem -Path $sourceDir -Filter "Reporte de actividades equipo social*.xlsx" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($candidates.Count -gt 0) {
        $chosen = $candidates[0]
        if ($chosen.Name -ne $expectedName) {
            Write-Output "Se detectó archivo fuente actualizado: $($chosen.Name). Copiando a nombre esperado: $expectedName"
            try {
                Copy-Item -Path $chosen.FullName -Destination $expectedPath -Force
                Write-Output "Copia realizada: $expectedPath"
            } catch {
                Write-Warning ("No se pudo copiar {0} a {1}: {2}" -f $chosen.FullName, $expectedPath, $_)
            }
        } else {
            Write-Output "Archivo fuente con nombre esperado presente: $expectedName"
        }
    } else {
        Write-Warning "No se encontró ningún archivo coincidente 'Reporte de actividades equipo social*.xlsx' en $sourceDir"
    }
} else {
    Write-Warning "Directorio fuente no encontrado: $sourceDir"
}

$pbixPath = Join-Path $PWD "Tableros\tableroDAGRDCOPIA.pbix"
$shouldReopenPowerBI = $false

$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python virtual environment not found at $py. Activate venv or create it first."
    exit 1
}

if ($ClosePowerBI) {
    Write-Output "Closing Power BI Desktop before ETL to avoid file locks..."
    Get-Process PBIDesktop -ErrorAction SilentlyContinue | Stop-Process -Force
    $shouldReopenPowerBI = $OpenPowerBI -or (Test-Path $pbixPath)
}

Write-Output "Using Python: $py"

try {
    Write-Output "Running ETL: scripts/etl/extraer_consultas_paginas_reporte.py"
    & $py ".\scripts\etl\extraer_consultas_paginas_reporte.py"
    if ($LASTEXITCODE -ne 0) {
        throw "ETL failed with exit code $LASTEXITCODE"
    }

    $repair = Join-Path $PWD ".\scripts\etl\reparar_hojas_modelo_para_powerbi.py"
    if (Test-Path $repair) {
        Write-Output "Running mandatory post-ETL repair script: $repair"
        & $py $repair
        if ($LASTEXITCODE -ne 0) {
            throw "Repair script failed with exit code $LASTEXITCODE"
        }
    } else {
        throw "Repair script not found: $repair"
    }

    if ($OpenPowerBI) {
        $shouldReopenPowerBI = $true
    }
}
catch {
    Write-Host "Error during ETL execution"
    Write-Host "$_"
    if ($shouldReopenPowerBI -and (Test-Path $pbixPath)) {
        Write-Output "Reopening Power BI Desktop after failure: $pbixPath"
        Start-Process $pbixPath
    }
    exit 1
}

if ($shouldReopenPowerBI) {
    if (Test-Path $pbixPath) {
        Write-Output "Opening Power BI Desktop: $pbixPath"
        Start-Process $pbixPath
    } else {
        Write-Output "Power BI file not found; skipping reopen: $pbixPath"
    }
}

Write-Output "ETL completed successfully. Output: data/model/Modelo_Reporte_Paginas_2026.xlsx"
