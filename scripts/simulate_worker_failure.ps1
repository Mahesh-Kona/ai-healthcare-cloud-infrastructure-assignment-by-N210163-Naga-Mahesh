$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[INFO] Stopping worker to simulate infrastructure failure..."
docker compose stop worker

Write-Host "[INFO] Worker stopped. Queue will grow while processing is paused."
Start-Sleep -Seconds 10

Write-Host "[INFO] Restarting worker to demonstrate recovery..."
docker compose start worker

Write-Host "[INFO] Recovery initiated. Check logs and queue depth to confirm resumed processing."
