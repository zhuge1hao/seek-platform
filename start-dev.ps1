$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $root "apps\api"
$webDir = Join-Path $root "apps\web"

Write-Host ""
Write-Host "meizhaiseek-platform dev launcher" -ForegroundColor Magenta
Write-Host "Root: $root"
Write-Host ""

function Test-CommandExists {
  param([string]$Command)
  $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "python")) {
  throw "Python is not available in PATH."
}

if (-not (Test-CommandExists "npm.cmd")) {
  throw "npm.cmd is not available in PATH."
}

if (-not (Test-Path (Join-Path $apiDir "requirements.txt"))) {
  throw "Cannot find apps\api\requirements.txt."
}

if (-not (Test-Path (Join-Path $webDir "package.json"))) {
  throw "Cannot find apps\web\package.json."
}

Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
Push-Location $apiDir
python -m pip install -r requirements.txt
Pop-Location

Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location $webDir
if (-not (Test-Path (Join-Path $webDir "node_modules"))) {
  npm.cmd install
} else {
  Write-Host "node_modules exists, skipping npm install."
}
Pop-Location

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop both services." -ForegroundColor Yellow
Write-Host ""

$apiJob = Start-Job -Name "meizhaiseek-api" -ScriptBlock {
  param($apiDir)
  Set-Location $apiDir
  python -m uvicorn main:app --reload --port 8000
} -ArgumentList $apiDir

$webJob = Start-Job -Name "meizhaiseek-web" -ScriptBlock {
  param($webDir)
  Set-Location $webDir
  npm.cmd run dev -- -p 3000
} -ArgumentList $webDir

try {
  while ($true) {
    Receive-Job -Job $apiJob,$webJob -Keep | ForEach-Object {
      Write-Host $_
    }

    $failed = @($apiJob, $webJob) | Where-Object { $_.State -in @("Failed", "Stopped", "Completed") }
    if ($failed.Count -gt 0) {
      Write-Host ""
      Write-Host "A service stopped. Showing latest job output:" -ForegroundColor Red
      Receive-Job -Job $apiJob,$webJob -Keep
      break
    }

    Start-Sleep -Milliseconds 600
  }
}
finally {
  Write-Host ""
  Write-Host "Stopping services..." -ForegroundColor Yellow
  Stop-Job -Job $apiJob,$webJob -ErrorAction SilentlyContinue
  Remove-Job -Job $apiJob,$webJob -Force -ErrorAction SilentlyContinue
  Write-Host "Done." -ForegroundColor Green
}
