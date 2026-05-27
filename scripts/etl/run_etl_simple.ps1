# ETL Pipeline Runner - Simplified version
# Runs ETL scripts without complex parameter handling

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $repoRoot '..\..')
Set-Location $repoRoot

Write-Host "Iniciando pipeline ETL..."

# Variables
$sourceDir = Join-Path $PWD "data\source"
$expectedName = "Reporte de actividades equipo social 2026 (1).xlsx"
$expectedPath = Join-Path $sourceDir $expectedName
$py = Join-Path $PWD ".venv\Scripts\python.exe"

# Validar Python
if (-not (Test-Path $py)) {
    Write-Host "ERROR: Python no encontrado en $py"
    exit 1
}

# Validar y preparar archivo fuente
if (Test-Path $sourceDir) {
    $candidates = Get-ChildItem -Path $sourceDir -Filter "Reporte de actividades equipo social*.xlsx" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($candidates.Count -gt 0) {
        $chosen = $candidates[0]
        if ($chosen.Name -ne $expectedName) {
            Write-Host "Copiando archivo: $($chosen.Name)"
            Copy-Item -Path $chosen.FullName -Destination $expectedPath -Force
        }
    }
}

Write-Host ""
Write-Host "Archivo fuente: $expectedName"
Write-Host "Python: $py"
Write-Host ""

# Paso 1
Write-Host "Paso 1: Extrayendo datos..."
$output1 = & $py "scripts\etl\extraer_consultas_paginas_reporte.py" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR en Paso 1:"
    Write-Host $output1
    exit 1
}
Write-Host "Paso 1 completado"
Write-Host $output1 | Select-Object -Last 5

Write-Host ""

# Paso 2
Write-Host "Paso 2: Reparando modelo..."
$repairScript = "scripts\etl\reparar_hojas_modelo_para_powerbi.py"
if (Test-Path $repairScript) {
    $output2 = & $py $repairScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR en Paso 2:"
        Write-Host $output2
        exit 1
    }
    Write-Host "Paso 2 completado"
    Write-Host $output2
}
else {
    Write-Host "ERROR: Script no encontrado: $repairScript"
    exit 1
}

Write-Host ""
Write-Host "ETL COMPLETADO EXITOSAMENTE"
Write-Host ""
exit 0
