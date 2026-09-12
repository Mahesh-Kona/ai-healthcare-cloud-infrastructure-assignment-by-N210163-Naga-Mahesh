$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$backupDirectory = Join-Path $ProjectRoot 'backups'
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupPath = Join-Path $backupDirectory "healthcare-$timestamp.sql"

Write-Host "[BACKUP] Creating PostgreSQL backup at $backupPath..."
docker exec healthcare-db pg_dump -U healthcare -d healthcare --format=plain | Set-Content -Path $backupPath -Encoding utf8
Write-Host "[BACKUP] Backup completed."
