[CmdletBinding()]
param(
    [string]$SessionId,
    [string]$EvidenceRoot,
    [string[]]$ResumeTarget,
    [switch]$WhatIf,
    [switch]$Force
)

. (Join-Path $PSScriptRoot "RemoteRecovery.Common.ps1")

$EvidenceRoot = if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) { Get-DefaultEvidenceRoot } else { $EvidenceRoot }
$session = New-RemoteRecoverySession -SessionId $SessionId -EvidenceRoot $EvidenceRoot
$resume = Invoke-ResumeContract -Session $session -ResumeTarget $ResumeTarget -WhatIf:$WhatIf -Force:$Force
$resume | ConvertTo-Json -Depth 8
