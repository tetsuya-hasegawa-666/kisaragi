$ErrorActionPreference = "Stop"

$projectRoot = "C:\Users\tetsuya\sandbox\codev-db\--process\--products\prj-codev-viewer"
$dashboardUrl = "http://127.0.0.1:4173/"

try {
  Set-Location $projectRoot

  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Please check the Node.js installation."
  }

  if (-not (Test-Path (Join-Path $projectRoot "node_modules"))) {
    Write-Host "Installing dependencies with npm ci..." -ForegroundColor Yellow
    npm ci
    if ($LASTEXITCODE -ne 0) {
      throw "npm ci failed."
    }
  }

  Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process "http://127.0.0.1:4173/"
  } | Out-Null

  Write-Host "Starting codev-viewer..." -ForegroundColor Cyan
  Write-Host "Press Ctrl+C in this window to stop the server." -ForegroundColor DarkGray

  npm run dashboard
  if ($LASTEXITCODE -ne 0) {
    throw "npm run dashboard failed."
  }
}
catch {
  Write-Host ""
  Write-Host "Dashboard launch failed." -ForegroundColor Red
  Write-Host $_ -ForegroundColor Red
  Read-Host "Press Enter to close"
  exit 1
}
