[CmdletBinding()]
param()

$defaultShell = Get-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name "DefaultShell" -ErrorAction SilentlyContinue
$service = Get-Service -Name "sshd" -ErrorAction SilentlyContinue

[pscustomobject]@{
    sshdInstalled = $null -ne $service
    sshdStatus = if ($service) { $service.Status.ToString() } else { "missing" }
    defaultShell = if ($defaultShell) { $defaultShell.DefaultShell } else { $null }
    pwshExists = Test-Path -LiteralPath "C:\Program Files\PowerShell\7\pwsh.exe"
    windowsPowerShellExists = Test-Path -LiteralPath "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
}
