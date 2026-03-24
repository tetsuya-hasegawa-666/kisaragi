$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$projectRoot = Split-Path -Parent $PSScriptRoot
$testRoot = Join-Path $projectRoot "..\..\--testcode\prj-reviework"
$testlogsRoot = Join-Path $projectRoot "..\..\--testlogs\prj-reviework"
$trialDataRoot = Join-Path $projectRoot "..\..\..\--trial-data\prj-reviework"
$logsDir = Join-Path $testlogsRoot "logs"
$reportsDir = Join-Path $testlogsRoot "reports"
$pycacheDir = Join-Path $trialDataRoot "python-pycache"

New-Item -ItemType Directory -Force -Path $logsDir, $reportsDir, $pycacheDir | Out-Null

$logFile = Join-Path $logsDir "python-unittest.log"
$env:PYTHONPYCACHEPREFIX = $pycacheDir

Push-Location $testRoot
try {
    python -m unittest test_session_parser.py 2>&1 | Tee-Object -FilePath $logFile
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    @'
# verification-summary

- command: `python -m unittest test_session_parser.py`
- result: pass
'@ | Set-Content -Path (Join-Path $reportsDir "python-unittest-summary.md") -Encoding UTF8
}
finally {
    Pop-Location
}
