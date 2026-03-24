[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [string]$SessionId,
    [string]$EvidenceRoot,
    [string]$Label = "slack-status"
)

. (Join-Path $PSScriptRoot "RemoteRecovery.Common.ps1")

$EvidenceRoot = if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) { Get-DefaultEvidenceRoot } else { $EvidenceRoot }
$session = New-RemoteRecoverySession -SessionId $SessionId -EvidenceRoot $EvidenceRoot
$savedPath = Save-CaptureEvidence -Session $session -SourcePath $SourcePath -Label $Label

[pscustomobject]@{
    sessionId = $session.SessionId
    savedPath = $savedPath
} | ConvertTo-Json -Depth 4
