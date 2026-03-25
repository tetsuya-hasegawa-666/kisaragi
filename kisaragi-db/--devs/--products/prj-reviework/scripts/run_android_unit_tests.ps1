$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$projectRoot = Split-Path -Parent $PSScriptRoot
$testlogsRoot = Join-Path $projectRoot "..\..\--testlogs\prj-reviework"
$exsamsRoot = Join-Path $projectRoot "..\..\..\--exsams\prj-reviework"
$logsDir = Join-Path $testlogsRoot "logs"
$reportsDir = Join-Path $testlogsRoot "reports"
$legacyArtifactsDir = Join-Path $testlogsRoot "artifacts"
$artifactsDir = Join-Path $exsamsRoot "android-test"
$gradleUserHome = Join-Path $exsamsRoot "gradle-user-home"
$projectCacheDir = Join-Path $exsamsRoot "project-cache"
$appBuildDir = Join-Path $exsamsRoot "app-build"

if (Test-Path $legacyArtifactsDir) {
    Remove-Item -Recurse -Force $legacyArtifactsDir
}

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

    $summaryPath = Join-Path $reportsDir "android-test-summary.md"
    @(
        "# android-test-summary",
        "",
        ("- command: gradlew.bat --project-cache-dir=" + $projectCacheDir + " :app:testDebugUnitTest"),
        ("- raw artifacts: " + $artifactsDir),
        ("- reports: " + $reportsDir)
    ) | Set-Content -Path $summaryPath -Encoding UTF8

    if (Test-Path $legacyArtifactsDir) {
        Remove-Item -Recurse -Force $legacyArtifactsDir
    }
}
finally {
    Pop-Location
}
