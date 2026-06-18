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

# Cargar configuración centralizada
$configFile = Join-Path $repoRoot "scripts\etl\etl_config.json"
if (-not (Test-Path $configFile)) {
    Write-Error "ERROR: Archivo de configuración no encontrado en $configFile"
    exit 1
}
$config = Get-Content $configFile -Raw | ConvertFrom-Json
$sourceSubDir = $config.paths.source_dir
$sourcePattern = $config.paths.source_file_pattern

$sourceDir = Join-Path $repoRoot $sourceSubDir
$chosen = $null

if (Test-Path $sourceDir) {
    $candidates = Get-ChildItem -Path $sourceDir -Filter $sourcePattern -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($candidates.Count -gt 0) {
        $chosen = $candidates[0]
        Write-Output "Archivo fuente detectado: $($chosen.Name)"
    } else {
        Write-Warning "No se encontró ningún archivo coincidente '$sourcePattern' en $sourceDir"
    }
} else {
    Write-Warning "Directorio fuente no encontrado: $sourceDir"
}

$pbixPath = Join-Path $repoRoot "Tableros\tableroDAGRDCOPIA.pbix"
$shouldReopenPowerBI = $false

$py = Join-Path $repoRoot ".venv\Scripts\python.exe"
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

    $repair = Join-Path $repoRoot "scripts\etl\reparar_hojas_modelo_para_powerbi.py"
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
