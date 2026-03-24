[CmdletBinding()]
param(
    [string]$SessionId,
    [string]$EvidenceRoot,
    [ValidateSet("Json", "Table")]
    [string]$Format = "Json"
)

. (Join-Path $PSScriptRoot "RemoteRecovery.Common.ps1")

$EvidenceRoot = if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) { Get-DefaultEvidenceRoot } else { $EvidenceRoot }
$session = New-RemoteRecoverySession -SessionId $SessionId -EvidenceRoot $EvidenceRoot
$doctor = Invoke-DoctorContract -Session $session

if ($Format -eq "Table") {
    $doctor.components | Format-Table name, status, detail -AutoSize
} else {
    $doctor | ConvertTo-Json -Depth 8
}
