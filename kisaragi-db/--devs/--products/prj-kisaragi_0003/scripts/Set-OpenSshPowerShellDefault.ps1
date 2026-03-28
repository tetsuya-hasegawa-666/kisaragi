[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$PwshPath = "C:\Program Files\PowerShell\7\pwsh.exe",
    [string]$WindowsPowerShellPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
)

$registryPath = "HKLM:\SOFTWARE\OpenSSH"
$registryName = "DefaultShell"
$resolvedPath = if (Test-Path -LiteralPath $PwshPath) { $PwshPath } else { $WindowsPowerShellPath }

if (-not (Test-Path -LiteralPath $resolvedPath)) {
    throw "PowerShell executable was not found. Checked: $PwshPath and $WindowsPowerShellPath"
}

if ($PSCmdlet.ShouldProcess($registryPath, "Set $registryName to $resolvedPath")) {
    if (-not (Test-Path -LiteralPath $registryPath)) {
        New-Item -Path $registryPath -Force | Out-Null
    }

    New-ItemProperty -Path $registryPath -Name $registryName -Value $resolvedPath -PropertyType String -Force | Out-Null
}

[pscustomobject]@{
    registryPath = $registryPath
    registryName = $registryName
    defaultShell = $resolvedPath
}
