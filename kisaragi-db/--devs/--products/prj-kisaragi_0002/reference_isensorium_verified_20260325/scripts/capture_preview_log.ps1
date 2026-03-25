param(
    [int]$DurationSeconds = 20
)

$adb = "C:\Android\platform-tools\adb.exe"

& $adb logcat -c | Out-Null
$start = Get-Date
Write-Host "Collecting preview logs for $DurationSeconds seconds..."
Write-Host "Start recording now, then wait."

$process = Start-Process -FilePath $adb -ArgumentList @(
    "logcat",
    "isensorium-preview:D",
    "AndroidRuntime:E",
    "*:S"
) -NoNewWindow -PassThru

Start-Sleep -Seconds $DurationSeconds

Stop-Process -Id $process.Id -Force
Write-Host "Done. Copy the terminal output."
