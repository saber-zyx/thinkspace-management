param(
    [string]$AppBaseUrl = "http://localhost:8080",
    [switch]$SkipDockerUp,
    [switch]$SkipDbtTest,
    [switch]$RestartApp,
    [switch]$VerboseDbt
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dbtProjectDir = Join-Path $projectRoot "analytics\dbt_thinkspace"

function Invoke-CheckedCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Lenh that bai: $Command $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Set-DefaultDbtEnv {
    if (-not $env:DBT_POSTGRES_HOST) { $env:DBT_POSTGRES_HOST = "localhost" }
    if (-not $env:DBT_POSTGRES_PORT) { $env:DBT_POSTGRES_PORT = "5433" }
    if (-not $env:DBT_POSTGRES_DB) { $env:DBT_POSTGRES_DB = "thinkspacedb" }
    if (-not $env:DBT_POSTGRES_USER) { $env:DBT_POSTGRES_USER = "thinkspace" }
    if (-not $env:DBT_POSTGRES_PASSWORD) { $env:DBT_POSTGRES_PASSWORD = "password123" }
}

if (-not (Test-Path $dbtProjectDir)) {
    throw "Khong tim thay dbt project: $dbtProjectDir"
}

Write-Host "Bat dau refresh analytics local..."

if (-not $SkipDockerUp) {
    Write-Host "Dam bao PostgreSQL va app local dang chay..."
    Invoke-CheckedCommand `
        -Command "docker" `
        -Arguments @("compose", "up", "-d", "db", "app") `
        -WorkingDirectory $projectRoot

    Invoke-CheckedCommand `
        -Command "docker" `
        -Arguments @("compose", "exec", "-T", "db", "pg_isready", "-U", "thinkspace", "-d", "thinkspacedb") `
        -WorkingDirectory $projectRoot
}

Set-DefaultDbtEnv

$dbtRunArguments = @("run", "--profiles-dir", ".", "--threads", "1")
$dbtTestArguments = @("test", "--profiles-dir", ".", "--threads", "1")

if (-not $VerboseDbt) {
    $dbtRunArguments += "--quiet"
    $dbtTestArguments += "--quiet"
    Write-Host "Dang chay dbt o che do gon. Dung -VerboseDbt neu muon xem log chi tiet."
}

Write-Host "Chay dbt run de cap nhat schema analytics..."
Invoke-CheckedCommand `
    -Command "dbt" `
    -Arguments $dbtRunArguments `
    -WorkingDirectory $dbtProjectDir

if (-not $SkipDbtTest) {
    Write-Host "Chay dbt test de kiem tra chat luong du lieu..."
    Invoke-CheckedCommand `
        -Command "dbt" `
        -Arguments $dbtTestArguments `
        -WorkingDirectory $dbtProjectDir
}

if ($RestartApp) {
    Write-Host "Restart app local theo yeu cau..."
    Invoke-CheckedCommand `
        -Command "docker" `
        -Arguments @("compose", "restart", "app") `
        -WorkingDirectory $projectRoot
    Start-Sleep -Seconds 4
}

Write-Host "Kiem tra dashboard API..."
$overview = Invoke-RestMethod "$AppBaseUrl/api/v1/moodle-logs/learning-dashboard-overview"

if ($overview.data_schema -ne "analytics") {
    throw "Dashboard chua doc schema analytics. data_schema hien tai: $($overview.data_schema)"
}

$summary = [PSCustomObject]@{
    data_schema = $overview.data_schema
    registered_users = $overview.registered_summary.total_registered_users
    projects = $overview.project_summary.total_projects
    top_activities = $overview.top_viewed_activities.Count
    refreshed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

Write-Host "Refresh analytics local thanh cong."
$summary | Format-List
