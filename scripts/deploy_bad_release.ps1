$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

@'
DB_PASSWORD=bad-secret-value
'@ | Set-Content -Path '.env.local'

Write-Host "[INFO] A deliberately unsafe configuration is now active."
Write-Host "[INFO] Run the pipeline to observe that the release should be blocked."
