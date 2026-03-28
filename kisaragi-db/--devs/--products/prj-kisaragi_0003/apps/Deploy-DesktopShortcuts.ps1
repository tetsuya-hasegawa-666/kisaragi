[CmdletBinding()]
param(
    [string]$DesktopPath = [Environment]::GetFolderPath("Desktop")
)

$sourceDir = Join-Path $PSScriptRoot ""
$shell = New-Object -ComObject WScript.Shell

$shortcuts = @(
    @{ Name = "Remote Doctor.lnk"; Target = Join-Path $sourceDir "RemoteDoctor.cmd" }
    @{ Name = "Remote Resume.lnk"; Target = Join-Path $sourceDir "RemoteResume.cmd" }
    @{ Name = "Remote Recover Preview.lnk"; Target = Join-Path $sourceDir "RemoteRecoverPreview.cmd" }
    @{ Name = "Open Evidence Folder.lnk"; Target = Join-Path $sourceDir "OpenEvidenceFolder.cmd" }
)

foreach ($item in $shortcuts) {
    $shortcutPath = Join-Path $DesktopPath $item.Name
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $item.Target
    $shortcut.WorkingDirectory = $PSScriptRoot
    $shortcut.Save()
}

Write-Host "Desktop shortcuts deployed to $DesktopPath"
