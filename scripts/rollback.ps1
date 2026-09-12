$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[ROLLBACK] Restoring the last locally built release..."
Remove-Item -Path '.env.local' -Force -ErrorAction SilentlyContinue
docker compose up -d --no-build --wait

$urls = @(
    'http://localhost:18080/health',
    'http://localhost:19001/health',
    'http://localhost:19000/health'
)

foreach ($url in $urls) {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
    Write-Host "[ROLLBACK] $url -> $($response.StatusCode)"
}

Write-Host "[ROLLBACK] Previous healthy local release is available."
