$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[INFO] Stopping cloud simulation environment..."
docker compose down

Write-Host "[INFO] Environment stopped."
