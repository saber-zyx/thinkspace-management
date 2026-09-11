param(
    [string]$BaseUrl = "http://localhost:8080",
    [int]$IntervalMinutes = 30,
    [int]$MaxRuns = 0
)

$ErrorActionPreference = "Stop"

if ($IntervalMinutes -lt 1) {
    throw "IntervalMinutes phai lon hon hoac bang 1."
}

$runIndex = 0
$statusUrl = "$BaseUrl/api/v1/moodle-logs/live-ingestion/status"
$runUrl = "$BaseUrl/api/v1/moodle-logs/live-ingestion/run-once"

Write-Host "Bat dau vong lap lay Moodle logs."
Write-Host "API app: $BaseUrl"
Write-Host "Chu ky: $IntervalMinutes phut"
Write-Host "Nhan Ctrl + C de dung."

while ($true) {
    $runIndex += 1
    $startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ""
    Write-Host "[$startedAt] Lan chay #$runIndex"

    try {
        $status = Invoke-RestMethod -Method Get -Uri $statusUrl
        if (-not $status.is_configured) {
            Write-Host "Nguon log Moodle chua duoc cau hinh. Hay kiem tra MOODLE_LOG_SOURCE_DATABASE_URL trong .env."
            Write-Host "Script se dung de tranh ghi audit not_configured lien tuc."
            break
        }

        $result = Invoke-RestMethod -Method Post -Uri $runUrl
        $run = $result.run
        $state = $result.state

        Write-Host ("Trang thai: {0}" -f $run.status)
        Write-Host ("Lay ve: {0} dong | Insert moi: {1} | Trung: {2} | Loi: {3}" -f $run.rows_fetched, $run.inserted_count, $run.duplicate_count, $run.failed_count)
        Write-Host ("Watermark: {0} -> {1}" -f $run.previous_watermark_id, $run.new_watermark_id)
        if ($state.last_success_at) {
            Write-Host ("Lan thanh cong gan nhat: {0}" -f $state.last_success_at)
        }
        if ($run.error_message) {
            Write-Host ("Loi: {0}" -f $run.error_message)
        }
    }
    catch {
        Write-Host ("Loi khi goi ingestion API: {0}" -f $_.Exception.Message)
    }

    if ($MaxRuns -gt 0 -and $runIndex -ge $MaxRuns) {
        Write-Host "Da dat MaxRuns=$MaxRuns. Dung vong lap."
        break
    }

    Start-Sleep -Seconds ($IntervalMinutes * 60)
}
