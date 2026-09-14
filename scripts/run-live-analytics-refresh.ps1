param(
    [string]$TargetDatabaseUrl = $env:TARGET_DATABASE_URL,
    [string]$LiveAppBaseUrl = $(if ($env:RENDER_APP_BASE_URL) { $env:RENDER_APP_BASE_URL } else { "https://thinkspace-management.onrender.com" }),
    [switch]$SkipDbtTest,
    [switch]$SkipApiCheck,
    [switch]$VerboseDbt
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dbtProjectDir = Join-Path $projectRoot "analytics\dbt_thinkspace"

function Assert-TargetDatabaseUrl {
    $script:TargetDatabaseUrl = $TargetDatabaseUrl.Trim()

    if ([string]::IsNullOrWhiteSpace($TargetDatabaseUrl)) {
        throw "Thieu TARGET_DATABASE_URL. Hay set bien moi truong TARGET_DATABASE_URL bang connection string Neon truoc khi chay."
    }

    $knownPlaceholders = @(
        "DAN_CONNECTION_STRING_NEON_CUA_BAN",
        "postgresql://...",
        "<NEON_DATABASE_URL>",
        "<TARGET_DATABASE_URL>"
    )

    if ($knownPlaceholders -contains $TargetDatabaseUrl -or ($TargetDatabaseUrl -notlike "postgresql://*" -and $TargetDatabaseUrl -notlike "postgres://*")) {
        throw "TARGET_DATABASE_URL khong hop le. Gia tri phai la connection string PostgreSQL that, khong phai placeholder."
    }
}

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
            throw "Lenh that bai: $Command. Da an tham so de tranh lo connection string."
        }
    }
    finally {
        Pop-Location
    }
}

function Get-QueryValue {
    param(
        [string]$Query,
        [string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Query)) {
        return $null
    }

    $pairs = $Query.TrimStart("?").Split("&", [System.StringSplitOptions]::RemoveEmptyEntries)
    foreach ($pair in $pairs) {
        $parts = $pair.Split("=", 2)
        if ($parts[0] -eq $Name -and $parts.Count -eq 2) {
            return [System.Uri]::UnescapeDataString($parts[1])
        }
    }

    return $null
}

function Convert-DatabaseUrlToDbtEnv {
    $uri = [System.Uri]$TargetDatabaseUrl

    if ($uri.Scheme -ne "postgresql" -and $uri.Scheme -ne "postgres") {
        throw "TARGET_DATABASE_URL phai dung scheme postgresql hoac postgres."
    }

    $userInfo = $uri.UserInfo.Split(":", 2)
    if ($userInfo.Count -lt 2) {
        throw "TARGET_DATABASE_URL phai co user va password."
    }

    $databaseName = $uri.AbsolutePath.TrimStart("/")
    if ([string]::IsNullOrWhiteSpace($databaseName)) {
        throw "TARGET_DATABASE_URL phai co ten database."
    }

    $sslMode = Get-QueryValue -Query $uri.Query -Name "sslmode"
    if ([string]::IsNullOrWhiteSpace($sslMode)) {
        if ($uri.Host -eq "localhost" -or $uri.Host -eq "127.0.0.1") {
            $sslMode = "prefer"
        }
        else {
            $sslMode = "require"
        }
    }

    $env:DBT_POSTGRES_HOST = $uri.Host
    $env:DBT_POSTGRES_PORT = if ($uri.IsDefaultPort) { "5432" } else { [string]$uri.Port }
    $env:DBT_POSTGRES_DB = [System.Uri]::UnescapeDataString($databaseName)
    $env:DBT_POSTGRES_USER = [System.Uri]::UnescapeDataString($userInfo[0])
    $env:DBT_POSTGRES_PASSWORD = [System.Uri]::UnescapeDataString($userInfo[1])
    $env:DBT_POSTGRES_SSLMODE = $sslMode
}

function Save-DbtEnv {
    return @{
        DBT_POSTGRES_HOST = $env:DBT_POSTGRES_HOST
        DBT_POSTGRES_PORT = $env:DBT_POSTGRES_PORT
        DBT_POSTGRES_DB = $env:DBT_POSTGRES_DB
        DBT_POSTGRES_USER = $env:DBT_POSTGRES_USER
        DBT_POSTGRES_PASSWORD = $env:DBT_POSTGRES_PASSWORD
        DBT_POSTGRES_SSLMODE = $env:DBT_POSTGRES_SSLMODE
    }
}

function Restore-DbtEnv {
    param([hashtable]$PreviousEnv)

    foreach ($key in $PreviousEnv.Keys) {
        if ([string]::IsNullOrEmpty($PreviousEnv[$key])) {
            Remove-Item "Env:\$key" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item "Env:\$key" $PreviousEnv[$key]
        }
    }
}

if (-not (Test-Path $dbtProjectDir)) {
    throw "Khong tim thay dbt project: $dbtProjectDir"
}

Assert-TargetDatabaseUrl
$previousEnv = Save-DbtEnv

try {
    Convert-DatabaseUrlToDbtEnv

    $dbtRunArguments = @("run", "--profiles-dir", ".", "--threads", "1")
    $dbtTestArguments = @("test", "--profiles-dir", ".", "--threads", "1")

    if (-not $VerboseDbt) {
        $dbtRunArguments += "--quiet"
        $dbtTestArguments += "--quiet"
        Write-Host "Dang chay dbt live o che do gon. Dung -VerboseDbt neu muon xem log chi tiet."
    }

    Write-Host "Chay dbt run tren target database..."
    Invoke-CheckedCommand `
        -Command "dbt" `
        -Arguments $dbtRunArguments `
        -WorkingDirectory $dbtProjectDir

    if (-not $SkipDbtTest) {
        Write-Host "Chay dbt test tren target database..."
        Invoke-CheckedCommand `
            -Command "dbt" `
            -Arguments $dbtTestArguments `
            -WorkingDirectory $dbtProjectDir
    }

    if (-not $SkipApiCheck) {
        if ([string]::IsNullOrWhiteSpace($LiveAppBaseUrl)) {
            throw "Thieu LiveAppBaseUrl. Hay truyen -LiveAppBaseUrl hoac set RENDER_APP_BASE_URL."
        }

        $baseUrl = $LiveAppBaseUrl.TrimEnd("/")
        Write-Host "Kiem tra API dashboard live..."
        $overview = Invoke-RestMethod "$baseUrl/api/v1/moodle-logs/learning-dashboard-overview"

        if ($overview.data_schema -ne "analytics") {
            throw "Dashboard live chua doc schema analytics. data_schema hien tai: $($overview.data_schema)"
        }

        $summary = [PSCustomObject]@{
            data_schema = $overview.data_schema
            registered_users = $overview.registered_summary.total_registered_users
            projects = $overview.project_summary.total_projects
            app_url = $baseUrl
            refreshed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        }

        Write-Host "Refresh analytics live thanh cong."
        $summary | Format-List
    }
    else {
        Write-Host "Refresh analytics live thanh cong. Da bo qua buoc kiem tra API."
    }
}
finally {
    Restore-DbtEnv -PreviousEnv $previousEnv
}
