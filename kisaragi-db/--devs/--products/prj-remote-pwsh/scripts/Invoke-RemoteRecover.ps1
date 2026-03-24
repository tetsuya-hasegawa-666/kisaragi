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
$doctor = Invoke-DoctorContract -Session $session
$resume = Invoke-ResumeContract -Session $session -ResumeTarget $ResumeTarget -WhatIf:$WhatIf -Force:$Force
$recheck = Invoke-RecheckContract -Session $session
$summary = New-RecoverySummary -Session $session -Doctor $doctor -Resume $resume -Recheck $recheck

[pscustomobject]@{
    sessionId = $session.SessionId
    doctor = $doctor
    resume = $resume
    recheck = $recheck
    summary = $summary
} | ConvertTo-Json -Depth 10
