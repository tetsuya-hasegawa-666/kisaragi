param(
    [string]$AdbPath = "C:/Android/platform-tools/adb.exe",
    [int]$Runs = 3,
    [int]$RecordSeconds = 6,
    [int]$TapX = 806,
    [int]$TapY = 2230,
    [string]$PackageName = "com.isensorium.app",
    [string]$ActivityName = ".MainActivity"
)

$ErrorActionPreference = "Stop"

function Invoke-Adb {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $AdbPath @Arguments
}

Write-Host "Checking device connection..."
Invoke-Adb @("devices")

for ($run = 1; $run -le $Runs; $run++) {
    Write-Host "Run $run/$Runs"
    Invoke-Adb @("shell", "am", "start", "-n", "$PackageName/$ActivityName") | Out-Null
    Start-Sleep -Seconds 2
    Invoke-Adb @("shell", "input", "tap", "$TapX", "$TapY") | Out-Null
    Start-Sleep -Seconds $RecordSeconds
    Invoke-Adb @("shell", "input", "tap", "$TapX", "$TapY") | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "Recent sessions:"
Invoke-Adb @("shell", "ls", "/sdcard/Android/data/$PackageName/files/Documents/sessions")
