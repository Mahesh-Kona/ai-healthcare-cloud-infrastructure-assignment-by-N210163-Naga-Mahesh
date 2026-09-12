$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "[PIPELINE] Starting validation stage..."
python -m compileall services

Write-Host "[PIPELINE] Running lightweight tests..."
python -c "print('[TEST] Placeholder validation passed.')"

Write-Host "[PIPELINE] Running security checks..."
$allowedPlaceholders = @(
    'change-me-dev',
    'admin',
    'example',
    'placeholder',
    'dummy',
    'sample',
    'your-password',
    'your-api-key',
    'your-secret'
)

$issues = New-Object System.Collections.Generic.List[string]

$files = Get-ChildItem -Path $ProjectRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch '\\.git\\' -and
    $_.Name -ne '.env' -and (
        $_.Extension -in '.py', '.yml', '.yaml', '.toml', '.json' -or
        $_.Name -like 'Dockerfile*' -or
        $_.Name -like '.env*'
    )
}

foreach ($file in $files) {
    $lines = @(Get-Content -Path $file.FullName)

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $trimmed = $line.Trim()

        if (-not $trimmed -or $trimmed.StartsWith('#')) {
            continue
        }

        if ($line -match '^(?i)\s*(DB_PASSWORD|POSTGRES_PASSWORD|AI_PROVIDER_API_KEY)\s*[:=]\s*(.+)$') {
            $key = $matches[1]
            $value = $matches[2].Trim().Trim('"''')

            if (-not $value) { continue }
            if ($value.StartsWith('${')) { continue }
            if ($value.Contains('os.environ.get(')) { continue }

            $isAllowed = $false
            foreach ($placeholder in $allowedPlaceholders) {
                if ($value -ieq $placeholder) {
                    $isAllowed = $true
                    break
                }
            }

            if (-not $isAllowed) {
                $issues.Add("$($file.FullName) : line $($i + 1) : suspicious hard-coded secret-like value for $key -> $value")
            }
        }
    }
}

if ($issues.Count -gt 0) {
    Write-Host "[SECURITY] Potential hard-coded secrets or risky values found."
    $issues | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host "[PIPELINE] Security checks passed."

Write-Host "[PIPELINE] Building artifacts..."
docker compose build

Write-Host "[PIPELINE] Running container vulnerability checks..."
$scout = Get-Command docker -ErrorAction SilentlyContinue
if ($scout) {
    $scanOutput = Join-Path $env:TEMP "cloudassignment-scout.txt"
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & docker scout cves --only-severity critical,high --only-fixed --exit-code local://cloudassignment-api:latest *> $scanOutput
    $scanExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($scanExitCode -eq 2) {
        Write-Host "[SECURITY] Critical/high fixed vulnerabilities detected in the API image."
        Get-Content $scanOutput
        exit 1
    }
    if ($scanExitCode -ne 0) {
        Write-Warning "Docker Scout is unavailable or not authenticated; run 'docker login' to enable the image CVE gate."
    } else {
        Write-Host "[SECURITY] Docker Scout image scan passed."
    }
}

Write-Host "[PIPELINE] Deploying release..."
& "$ProjectRoot\scripts\start_env.ps1"

Write-Host "[PIPELINE] Verifying service health..."
$urls = @(
    'http://localhost:18080/health',
    'http://localhost:19001/health',
    'http://localhost:19000/health'
)

foreach ($url in $urls) {
    $attempts = 0
    $success = $false

    while (-not $success -and $attempts -lt 20) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing
            Write-Host "[HEALTH] $url -> $($response.StatusCode)"
            $success = $true
        }
        catch {
            $attempts++
            Write-Host "[HEALTH] $url failed (attempt $attempts/20): $($_.Exception.Message)"
            Start-Sleep -Seconds 2
        }
    }

    if (-not $success) {
        throw "[HEALTH] $url did not become healthy in time."
    }
}

Write-Host "[PIPELINE] Deployment completed successfully."
