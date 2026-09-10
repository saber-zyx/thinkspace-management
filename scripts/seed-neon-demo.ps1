param(
    [string]$TargetDatabaseUrl = $env:TARGET_DATABASE_URL,
    [switch]$ResetTarget
)

$ErrorActionPreference = "Stop"

$ContainerName = "thinkspace_management-db-1"
$LocalDatabaseName = "thinkspacedb"
$LocalDatabaseUser = "thinkspace"

$Tables = @(
    "public.sync_jobs",
    "public.registrations",
    "public.raw_moodle_log_files",
    "public.raw_moodle_participant_files",
    "public.raw_moodle_participants",
    "public.raw_ueh_lms_course_enrollments",
    "public.bronze_moodle_log_events",
    "public.moodle_log_user_exclusions",
    "public.moodle_participant_email_exclusions"
)

function Assert-TargetDatabaseUrl {
    if ([string]::IsNullOrWhiteSpace($TargetDatabaseUrl)) {
        throw "Thieu TARGET_DATABASE_URL. Hay set bien moi truong TARGET_DATABASE_URL bang connection string Neon truoc khi chay script."
    }

    if ($TargetDatabaseUrl -like "*<*" -or $TargetDatabaseUrl -like "*>*" -or $TargetDatabaseUrl -notlike "postgresql://*") {
        throw "TARGET_DATABASE_URL khong hop le. Gia tri phai la connection string PostgreSQL that, khong phai placeholder."
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

Write-Host "Tao lai cac view phan tich tren Neon bang code app..."
$PreviousDatabaseUrl = $env:DATABASE_URL
$env:DATABASE_URL = $TargetDatabaseUrl
try {
    & python -c "import src.app.main; print('Da tao lai schema va cac view phan tich tren Neon')"
    if ($LASTEXITCODE -ne 0) {
        throw "Khong tao lai duoc schema/view bang code app."
    }
}
finally {
    if ([string]::IsNullOrEmpty($PreviousDatabaseUrl)) {
        Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $PreviousDatabaseUrl
    }

}

Write-Host "Kiem tra so dong bang chinh tren Neon..."
Invoke-CheckedDocker @(
    "exec",
    $ContainerName,
    "psql",
    $TargetDatabaseUrl,
    "-c",
    "SELECT 'registrations' AS table_name, COUNT(*) AS row_count FROM registrations UNION ALL SELECT 'raw_moodle_participants', COUNT(*) FROM raw_moodle_participants UNION ALL SELECT 'bronze_moodle_log_events', COUNT(*) FROM bronze_moodle_log_events ORDER BY table_name;"
)

Write-Host "Hoan thanh seed demo Neon. Hay mo lai app Render va bam Ctrl + F5 de kiem tra dashboard."
