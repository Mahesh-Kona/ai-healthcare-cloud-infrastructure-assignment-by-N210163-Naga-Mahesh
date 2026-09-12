$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[INFO] Starting cloud simulation environment..."
docker compose up --build -d

Write-Host "[INFO] Environment started."
Write-Host "[INFO] API: http://localhost:18080"
Write-Host "[INFO] Prometheus: http://localhost:19090"
Write-Host "[INFO] Grafana: http://localhost:13000"
