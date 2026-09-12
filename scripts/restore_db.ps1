param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

Write-Host "[RESTORE] Restoring PostgreSQL state from $BackupFile..."
docker exec healthcare-db psql -U healthcare -d healthcare -v ON_ERROR_STOP=1 -c "DROP TABLE IF EXISTS appointments CASCADE;"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to prepare the database for restore."
}

Get-Content -Raw -Path $BackupFile | docker exec -i healthcare-db psql -U healthcare -d healthcare -v ON_ERROR_STOP=1
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL restore failed."
}

Write-Host "[RESTORE] Restore completed."
