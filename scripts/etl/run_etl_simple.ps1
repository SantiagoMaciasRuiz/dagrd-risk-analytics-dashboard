# ETL Pipeline Runner - Simplified version
# Runs ETL scripts without complex parameter handling

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $repoRoot '..\..')
Set-Location $repoRoot

Write-Host "Iniciando pipeline ETL..."

# Cargar configuración centralizada
$configFile = Join-Path $repoRoot "scripts\etl\etl_config.json"
if (-not (Test-Path $configFile)) {
    Write-Host "ERROR: Archivo de configuración no encontrado en $configFile"
    exit 1
}
$config = Get-Content $configFile -Raw | ConvertFrom-Json
$sourceSubDir = $config.paths.source_dir
$sourcePattern = $config.paths.source_file_pattern

$sourceDir = Join-Path $repoRoot $sourceSubDir
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"

# Validar Python
if (-not (Test-Path $py)) {
    Write-Host "ERROR: Python no encontrado en $py"
    exit 1
}

# Validar y preparar archivo fuente
$chosen = $null
if (Test-Path $sourceDir) {
    $candidates = Get-ChildItem -Path $sourceDir -Filter $sourcePattern -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    if ($candidates.Count -gt 0) {
        $chosen = $candidates[0]
        Write-Host "Archivo fuente detectado: $($chosen.Name)"
    }
}

Write-Host ""
Write-Host "Archivo fuente: $(if ($chosen) { $chosen.Name } else { 'No encontrado' })"
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
