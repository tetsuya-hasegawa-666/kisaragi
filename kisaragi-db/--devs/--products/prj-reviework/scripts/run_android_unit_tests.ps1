$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$projectRoot = Split-Path -Parent $PSScriptRoot
$testlogsRoot = Join-Path $projectRoot "..\..\--testlogs\prj-reviework"
$trialDataRoot = Join-Path $projectRoot "..\..\..\--trial-data\prj-reviework"
$logsDir = Join-Path $testlogsRoot "logs"
$reportsDir = Join-Path $testlogsRoot "reports"
$artifactsDir = Join-Path $testlogsRoot "artifacts"
$gradleUserHome = Join-Path $trialDataRoot "gradle-user-home"
$projectCacheDir = Join-Path $trialDataRoot "project-cache"
$appBuildDir = Join-Path $trialDataRoot "app-build"

New-Item -ItemType Directory -Force -Path $logsDir, $reportsDir, $artifactsDir, $gradleUserHome, $projectCacheDir | Out-Null

$logFile = Join-Path $logsDir "gradle-testDebugUnitTest.log"
$env:GRADLE_USER_HOME = $gradleUserHome

Push-Location $projectRoot
try {
    & (Join-Path $projectRoot "gradlew.bat") `
        "--project-cache-dir=$projectCacheDir" `
        ":app:testDebugUnitTest" *>&1 | Tee-Object -FilePath $logFile

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $htmlSource = Join-Path $appBuildDir "reports\\tests\\testDebugUnitTest"
    $xmlSource = Join-Path $appBuildDir "test-results\\testDebugUnitTest"
    $htmlTarget = Join-Path $reportsDir "testDebugUnitTest\\html"
    $xmlTarget = Join-Path $reportsDir "testDebugUnitTest\\junit"

    if (Test-Path $htmlSource) {
        New-Item -ItemType Directory -Force -Path $htmlTarget | Out-Null
        Copy-Item -Path (Join-Path $htmlSource '*') -Destination $htmlTarget -Recurse -Force
    }

    if (Test-Path $xmlSource) {
        New-Item -ItemType Directory -Force -Path $xmlTarget | Out-Null
        Copy-Item -Path (Join-Path $xmlSource '*') -Destination $xmlTarget -Recurse -Force
    }
}
finally {
    Pop-Location
}
