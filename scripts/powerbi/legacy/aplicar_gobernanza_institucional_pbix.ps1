param(
    [int]$Port = 57948,
    [string]$DatabaseName = ""
)

$scriptPath = Join-Path $PSScriptRoot "aplicar_gobernanza_institucional_57948.ps1"
& $scriptPath -Port $Port -DatabaseName $DatabaseName
