param(
    [string]$TargetDatabaseUrl = $env:TARGET_DATABASE_URL,
    [string]$LiveAppBaseUrl = $(if ($env:RENDER_APP_BASE_URL) { $env:RENDER_APP_BASE_URL } else { "https://thinkspace-management.onrender.com" }),
    [switch]$ResetTarget,
    [switch]$SkipLiveAnalyticsRefresh,
    [switch]$SkipDbtTest,
    [switch]$SkipApiCheck,
    [switch]$VerboseDbt
)

$ErrorActionPreference = "Stop"

$ContainerName = "thinkspace_management-db-1"
$LocalDatabaseName = "thinkspacedb"
$LocalDatabaseUser = "thinkspace"
$RefreshScript = Join-Path $PSScriptRoot "run-live-analytics-refresh.ps1"

$Tables = @(
    "public.sync_jobs",
    "public.registrations",
    "public.raw_moodle_log_files",
    "public.raw_moodle_participant_files",
    "public.raw_moodle_participants",
    "public.raw_ueh_lms_course_enrollments",
    "public.bronze_moodle_log_events",
    "public.moodle_log_ingestion_state",
    "public.moodle_log_ingestion_runs",
    "public.moodle_log_user_exclusions",
    "public.moodle_participant_email_exclusions"
)

function Assert-TargetDatabaseUrl {
    $script:TargetDatabaseUrl = $TargetDatabaseUrl.Trim()

    if ([string]::IsNullOrWhiteSpace($TargetDatabaseUrl)) {
        throw "Thieu TARGET_DATABASE_URL. Hay set bien moi truong TARGET_DATABASE_URL bang connection string Neon truoc khi chay script."
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

function Invoke-LiveAnalyticsRefresh {
    if ($SkipLiveAnalyticsRefresh) {
        Write-Host "Bo qua buoc refresh analytics live theo yeu cau."
        return
    }

    if (-not (Test-Path $RefreshScript)) {
        throw "Khong tim thay script refresh analytics live: $RefreshScript"
    }

    $RefreshArguments = @(
        "-TargetDatabaseUrl", $TargetDatabaseUrl,
        "-LiveAppBaseUrl", $LiveAppBaseUrl
    )

    if ($SkipDbtTest) { $RefreshArguments += "-SkipDbtTest" }
    if ($SkipApiCheck) { $RefreshArguments += "-SkipApiCheck" }
    if ($VerboseDbt) { $RefreshArguments += "-VerboseDbt" }

    Write-Host "Refresh analytics tren target database bang dbt..."
    & $RefreshScript @RefreshArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Refresh analytics live that bai. Da an tham so de tranh lo connection string."
    }
}

function Invoke-CheckedDocker {
    param(
        [string[]]$Arguments,
        [switch]$Quiet
    )

    if ($Quiet) {
        & docker @Arguments | Out-Null
    }
    else {
        & docker @Arguments
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Lenh docker that bai. Da an tham so de tranh lo connection string."
    }
}

Assert-TargetDatabaseUrl

Write-Host "Kiem tra container PostgreSQL local..."
Invoke-CheckedDocker @("exec", $ContainerName, "pg_isready", "-U", $LocalDatabaseUser, "-d", $LocalDatabaseName)

$TableArgs = @()
foreach ($Table in $Tables) {
    $TableArgs += "-t"
    $TableArgs += $Table
}

Write-Host "Tao schema dump tu database local..."
$SchemaDumpArgs = @(
    "exec",
    $ContainerName,
    "pg_dump",
    "-U",
    $LocalDatabaseUser,
    "-d",
    $LocalDatabaseName,
    "--schema-only",
    "--no-owner",
    "--no-privileges"
) + $TableArgs + @("-f", "/tmp/thinkspace_demo_schema.sql")

Invoke-CheckedDocker $SchemaDumpArgs

Write-Host "Tao data dump co ten cot tu database local..."
$DataDumpArgs = @(
    "exec",
    $ContainerName,
    "pg_dump",
    "-U",
    $LocalDatabaseUser,
    "-d",
    $LocalDatabaseName,
    "--data-only",
    "--column-inserts",
    "--no-owner",
    "--no-privileges"
) + $TableArgs + @("-f", "/tmp/thinkspace_demo_data.sql")

Invoke-CheckedDocker $DataDumpArgs

if ($ResetTarget) {
    Write-Host "Reset schema public tren Neon..."
    Invoke-CheckedDocker @(
        "exec",
        $ContainerName,
        "psql",
        $TargetDatabaseUrl,
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO CURRENT_USER; DO `$`$ BEGIN EXECUTE format('ALTER ROLE %I IN DATABASE %I SET search_path TO public', current_user, current_database()); END `$`$; SET search_path TO public;"
    )
}

Write-Host "Restore schema len Neon..."
Invoke-CheckedDocker @(
    "exec",
    $ContainerName,
    "psql",
    $TargetDatabaseUrl,
    "-q",
    "-v",
    "ON_ERROR_STOP=1",
    "-f",
    "/tmp/thinkspace_demo_schema.sql"
) -Quiet

Write-Host "Restore data len Neon..."
Invoke-CheckedDocker @(
    "exec",
    $ContainerName,
    "psql",
    $TargetDatabaseUrl,
    "-q",
    "-v",
    "ON_ERROR_STOP=1",
    "-f",
    "/tmp/thinkspace_demo_data.sql"
) -Quiet

Write-Host "Kiem tra so dong bang chinh tren Neon..."
Invoke-CheckedDocker @(
    "exec",
    $ContainerName,
    "psql",
    $TargetDatabaseUrl,
    "-c",
    "SELECT 'public.registrations' AS table_name, COUNT(*) AS row_count FROM public.registrations UNION ALL SELECT 'public.raw_moodle_participants', COUNT(*) FROM public.raw_moodle_participants UNION ALL SELECT 'public.bronze_moodle_log_events', COUNT(*) FROM public.bronze_moodle_log_events UNION ALL SELECT 'public.moodle_log_ingestion_state', COUNT(*) FROM public.moodle_log_ingestion_state UNION ALL SELECT 'public.moodle_log_ingestion_runs', COUNT(*) FROM public.moodle_log_ingestion_runs ORDER BY table_name;"
)

Invoke-LiveAnalyticsRefresh

if (-not $SkipLiveAnalyticsRefresh) {
    Write-Host "Kiem tra so dong analytics mart tren Neon..."
    Invoke-CheckedDocker @(
        "exec",
        $ContainerName,
        "psql",
        $TargetDatabaseUrl,
        "-c",
        "SELECT 'analytics.gold_registered_user_learning_summary' AS table_name, COUNT(*) AS row_count FROM analytics.gold_registered_user_learning_summary UNION ALL SELECT 'analytics.gold_project_learning_summary', COUNT(*) FROM analytics.gold_project_learning_summary UNION ALL SELECT 'analytics.gold_milestone_traction_summary', COUNT(*) FROM analytics.gold_milestone_traction_summary ORDER BY table_name;"
    )
}

Write-Host "Hoan thanh sync demo data va refresh analytics live. Hay mo lai app Render va bam Ctrl + F5 de kiem tra dashboard."
