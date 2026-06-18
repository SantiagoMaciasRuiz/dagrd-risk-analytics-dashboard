param([switch]$GenerateReport)

$root = "C:\Users\santi\OneDrive\Escritorio\Chamba\Dashboard"
$today = Get-Date
$sixMonthsAgo = $today.AddMonths(-6)

function Analyze-Directory {
    param([string]$Path, [string]$Label)
    
    if (-not (Test-Path $Path)) { return @() }
    
    $items = @()
    Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | 
        Where-Object { $_.PSIsContainer -eq $false } | 
        ForEach-Object {
            $relative = $_.FullName -replace [regex]::Escape($root), ""
            $age = (New-TimeSpan -Start $_.LastWriteTime -End $today).Days
            $items += @{
                Name = $_.Name
                Path = $relative
                Size = $_.Length
                Age = $age
                Modified = $_.LastWriteTime
            }
        }
    return $items
}

# ANÁLISIS POR SECCIÓN
$report = @{}

# RAÍZ
$rootFiles = Get-ChildItem -Path $root -Depth 0 -Force | Where-Object { $_.PSIsContainer -eq $false }
$report["ROOT"] = @{
    Count = $rootFiles.Count
    Size = ($rootFiles | Measure-Object -Property Length -Sum).Sum
    Files = $rootFiles | Select-Object Name, @{N="MB";E={[math]::Round($_.Length/1MB,2)}}, @{N="Age(d)";E={(New-TimeSpan -Start $_.LastWriteTime -End $today).Days}}
}

# DATA
$dataItems = Analyze-Directory "$root\data" "data"
$report["DATA"] = @{
    Count = $dataItems.Count
    Size = ($dataItems | Measure-Object -Property Size -Sum).Sum
    Details = $dataItems | Group-Object { Split-Path $_.Path -Parent } | ForEach-Object { 
        @{
            Subfolder = $_.Name
            Files = $_.Group.Count
            Size = ($_.Group | Measure-Object -Property Size -Sum).Sum
        }
    }
}

# SCRIPTS
$scriptsItems = Analyze-Directory "$root\scripts" "scripts"
$report["SCRIPTS"] = @{
    Count = $scriptsItems.Count
    Size = ($scriptsItems | Measure-Object -Property Size -Sum).Sum
    Details = $scriptsItems | Group-Object { Split-Path $_.Path -Parent } | ForEach-Object { 
        @{
            Subfolder = $_.Name
            Files = $_.Group.Count
            Size = ($_.Group | Measure-Object -Property Size -Sum).Sum
        }
    }
}

# POWERBI
$powerbiItems = Analyze-Directory "$root\powerbi" "powerbi"
$report["POWERBI"] = @{
    Count = $powerbiItems.Count
    Size = ($powerbiItems | Measure-Object -Property Size -Sum).Sum
}

# DOCS
$docsItems = Analyze-Directory "$root\docs" "docs"
$report["DOCS"] = @{
    Count = $docsItems.Count
    Size = ($docsItems | Measure-Object -Property Size -Sum).Sum
}

# ENTREGABLES
$entregablesItems = Analyze-Directory "$root\entregables" "entregables"
$report["ENTREGABLES"] = @{
    Count = $entregablesItems.Count
    Size = ($entregablesItems | Measure-Object -Property Size -Sum).Sum
}

# TABLEROS
$tablerosItems = Analyze-Directory "$root\Tableros" "Tableros"
$report["TABLEROS"] = @{
    Count = $tablerosItems.Count
    Size = ($tablerosItems | Measure-Object -Property Size -Sum).Sum
}

# BACKUP
$backupItems = Analyze-Directory "$root\BACKUP_2026-05-26" "BACKUP"
$report["BACKUP_2026-05-26"] = @{
    Count = $backupItems.Count
    Size = ($backupItems | Measure-Object -Property Size -Sum).Sum
}

# Salida
$report | ConvertTo-Json -Depth 3 | Out-File -FilePath "$root\AUDITORIA_COMPLETA.json" -Encoding UTF8
Write-Host "=== AUDITORIA GENERADA ===" -ForegroundColor Green
Write-Host "Archivo guardado: $root\AUDITORIA_COMPLETA.json"

# Resumen rápido
$totalSize = (Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
Write-Host "`nTAMAÑO TOTAL: $('{0:N2}' -f ($totalSize/1MB)) MB"

$sections = @("ROOT", "DATA", "SCRIPTS", "POWERBI", "DOCS", "ENTREGABLES", "TABLEROS", "BACKUP_2026-05-26")
foreach ($sec in $sections) {
    if ($report[$sec]) {
        $sizeMB = [math]::Round($report[$sec].Size / 1MB, 2)
        $count = $report[$sec].Count
        Write-Host "$sec`: $count archivos, $sizeMB MB"
    }
}
