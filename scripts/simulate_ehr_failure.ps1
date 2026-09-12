$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[INFO] Stopping EHR mock to simulate external dependency failure..."
docker compose stop ehr-mock

Write-Host "[INFO] EHR mock stopped. Observe timeout, retry, or failure handling in the worker."
Start-Sleep -Seconds 10

Write-Host "[INFO] Restarting EHR mock to demonstrate recovery..."
docker compose start ehr-mock

Write-Host "[INFO] Recovery completed."
