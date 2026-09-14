param(
    [int]$IntervalMinutes = 30,
    [int]$MaxRuns = 0
)

$ErrorActionPreference = "Stop"

if ($IntervalMinutes -lt 1) {
    throw "IntervalMinutes phai lon hon hoac bang 1."
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$exportScript = Join-Path $projectRoot "scripts\export_moodle_logs_once.py"
$refreshScript = Join-Path $projectRoot "scripts\run-local-analytics-refresh.ps1"

if (-not (Test-Path $exportScript)) {
    throw "Khong tim thay script export: $exportScript"
}

if (-not (Test-Path $refreshScript)) {
    throw "Khong tim thay script refresh analytics: $refreshScript"
}

$runIndex = 0

Write-Host "Bat dau pipeline Moodle UI logs."
Write-Host "Chu ky: $IntervalMinutes phut"
Write-Host "Script: $exportScript"
Write-Host "Nhan Ctrl + C de dung."

while ($true) {
    $runIndex += 1
    $startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    Write-Host ""
    Write-Host "[$startedAt] Lan chay #$runIndex"

    try {
        python $exportScript
        if ($LASTEXITCODE -ne 0) {
            throw "Python script tra exit code $LASTEXITCODE"
        }
        & $refreshScript -SkipDockerUp
        Write-Host "Lan chay #$runIndex thanh cong."
    }
    catch {
        Write-Host ("Lan chay #{0} that bai: {1}" -f $runIndex, $_.Exception.Message)
    }

    if ($MaxRuns -gt 0 -and $runIndex -ge $MaxRuns) {
        Write-Host "Da dat MaxRuns=$MaxRuns. Dung pipeline."
        break
    }

    Start-Sleep -Seconds ($IntervalMinutes * 60)
}
