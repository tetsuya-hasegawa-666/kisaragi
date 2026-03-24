[CmdletBinding()]
param(
    [string]$SessionId,
    [string]$EvidenceRoot,
    [switch]$WhatIf,
    [switch]$Force
)

. (Join-Path $PSScriptRoot "RemoteRecovery.Common.ps1")

$EvidenceRoot = if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) { Get-DefaultEvidenceRoot } else { $EvidenceRoot }
$session = New-RemoteRecoverySession -SessionId $SessionId -EvidenceRoot $EvidenceRoot
$doctor = Invoke-DoctorContract -Session $session

$shouldResume = ($doctor.overallStatus -eq "needs_resume")
$resume = if ($shouldResume -or (-not $WhatIf)) {
    Invoke-ResumeContract -Session $session -WhatIf:$WhatIf -Force:$Force
} else {
    [pscustomobject]@{
        sessionId = $session.SessionId
        phase = "resume"
        executedAt = (Get-Date).ToString("o")
        whatIf = $true
        steps = @()
        failedTargets = @()
        source = "guided-skip"
        sourceScript = $null
        lockPath = $null
        evidencePath = $null
    }
}
$recheck = Invoke-RecheckContract -Session $session
$summary = New-RecoverySummary -Session $session -Doctor $doctor -Resume $resume -Recheck $recheck

[pscustomobject]@{
    sessionId = $session.SessionId
    guided = $true
    initialStatus = $doctor.overallStatus
    shouldResume = $shouldResume
    nextAction = $summary.nextAction
    doctor = $doctor
    resume = $resume
    recheck = $recheck
    summary = $summary
} | ConvertTo-Json -Depth 10
