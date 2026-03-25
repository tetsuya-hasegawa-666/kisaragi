$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$projectRoot = Split-Path -Parent $PSScriptRoot
$testRoot = Join-Path $projectRoot "..\..\--testcode\prj-reviework"
$testlogsRoot = Join-Path $projectRoot "..\..\--testlogs\prj-reviework"
$exsamsRoot = Join-Path $projectRoot "..\..\..\--exsams\prj-reviework"
$logsDir = Join-Path $testlogsRoot "logs"
$reportsDir = Join-Path $testlogsRoot "reports"
$pycacheDir = Join-Path $exsamsRoot "python-pycache"

New-Item -ItemType Directory -Force -Path $logsDir, $reportsDir, $pycacheDir | Out-Null

$logFile = Join-Path $logsDir "python-unittest.log"
$env:PYTHONPYCACHEPREFIX = $pycacheDir

Push-Location $testRoot
try {
    $command = 'python -m unittest test_session_parser.py test_project_contracts.py > "' + $logFile + '" 2>&1'
    cmd /d /c $command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Get-Content -Path $logFile

    @'
# verification-summary

- command: `python -m unittest test_session_parser.py test_project_contracts.py`
- result: pass
'@ | Set-Content -Path (Join-Path $reportsDir "python-unittest-summary.md") -Encoding UTF8
}
finally {
    Pop-Location
}
