Set-StrictMode -Version Latest

function Get-DefaultEvidenceRoot {
    [CmdletBinding()]
    param(
        [string]$ScriptRoot = $PSScriptRoot
    )

    if ([string]::IsNullOrWhiteSpace($ScriptRoot)) {
        $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    }

    return [System.IO.Path]::GetFullPath((Join-Path $ScriptRoot "..\..\..\--testlogs\prj-remote-pwsh"))
}

function New-RemoteRecoverySession {
    [CmdletBinding()]
    param(
        [string]$SessionId,
        [string]$EvidenceRoot
    )

    if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
        $EvidenceRoot = Get-DefaultEvidenceRoot
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    if ([string]::IsNullOrWhiteSpace($SessionId)) {
        $SessionId = "rr-$timestamp"
    }

    $resolvedRoot = [System.IO.Path]::GetFullPath($EvidenceRoot)
    foreach ($directoryName in @("logs", "artifacts", "reports")) {
        $directoryPath = Join-Path $resolvedRoot $directoryName
        if (-not (Test-Path -LiteralPath $directoryPath)) {
            New-Item -ItemType Directory -Path $directoryPath -Force | Out-Null
        }
    }

    [pscustomobject]@{
        SessionId    = $SessionId
        Timestamp    = $timestamp
        EvidenceRoot = $resolvedRoot
        LogsPath     = Join-Path $resolvedRoot "logs"
        ArtifactsPath = Join-Path $resolvedRoot "artifacts"
        ReportsPath  = Join-Path $resolvedRoot "reports"
        CapturesPath = Join-Path $resolvedRoot "captures"
    }
}

function Get-ResumeLockPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session
    )

    return Join-Path $Session.EvidenceRoot "artifacts\resume.lock.json"
}

function Acquire-ResumeLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session,
        [int]$TimeoutMinutes = 30,
        [switch]$Force
    )

    $lockPath = Get-ResumeLockPath -Session $Session
    if (Test-Path -LiteralPath $lockPath) {
        $content = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
        $lockedAt = [datetime]$content.lockedAt
        $isStale = ((Get-Date) - $lockedAt).TotalMinutes -ge $TimeoutMinutes
        if ((-not $Force) -and (-not $isStale)) {
            throw "resume lock is active by session $($content.sessionId) on $($content.hostName)."
        }

        if ($isStale -or $Force) {
            Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
        }
    }

    $payload = [pscustomobject]@{
        sessionId = $Session.SessionId
        hostName = $env:COMPUTERNAME
        lockedAt = (Get-Date).ToString("o")
    }
    $json = $payload | ConvertTo-Json -Depth 4
    try {
        $fs = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($json)
            $fs.Write($bytes, 0, $bytes.Length)
        }
        finally {
            $fs.Dispose()
        }
    }
    catch [System.IO.IOException] {
        $content = Get-Content -Raw -LiteralPath $lockPath -ErrorAction SilentlyContinue
        if ($content) {
            $existing = $content | ConvertFrom-Json
            throw "resume lock is active by session $($existing.sessionId) on $($existing.hostName)."
        }
        throw "resume lock is active."
    }

    return $lockPath
}

function Release-ResumeLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session
    )

    $lockPath = Get-ResumeLockPath -Session $Session
    if (Test-Path -LiteralPath $lockPath) {
        Remove-Item -LiteralPath $lockPath -Force
    }
}

function Get-RecoveryEvidencePath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session,
        [Parameter(Mandatory = $true)]
        [string]$Phase,
        [Parameter(Mandatory = $true)]
        [ValidateSet("json", "md")]
        [string]$Extension
    )

    $baseName = "{0}-{1}-{2}.{3}" -f $Session.Timestamp, $Session.SessionId, $Phase, $Extension
    switch ($Phase) {
        "summary" {
            if ($Extension -eq "json") {
                return Join-Path $Session.ArtifactsPath $baseName
            }

            return Join-Path $Session.ReportsPath $baseName
        }
        default {
            return Join-Path $Session.LogsPath $baseName
        }
    }
}

function Write-RecoveryJson {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [object]$Data
    )

    [System.IO.File]::WriteAllText($Path, ($Data | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
    return $Path
}

function Write-RecoveryMarkdown {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string[]]$Lines
    )

    [System.IO.File]::WriteAllText($Path, ($Lines -join [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
    return $Path
}

function Get-RemoteRecoveryTargets {
    [CmdletBinding()]
    param()

    @(
        [pscustomobject]@{ Name = "Slack"; CheckKind = "placeholder"; ResumeKind = "placeholder" }
        [pscustomobject]@{ Name = "Docker"; CheckKind = "service"; ResumeKind = "service" }
        [pscustomobject]@{ Name = "PostgreSQL"; CheckKind = "service"; ResumeKind = "service" }
        [pscustomobject]@{ Name = "Synceller"; CheckKind = "placeholder"; ResumeKind = "placeholder" }
        [pscustomobject]@{ Name = "app-server"; CheckKind = "placeholder"; ResumeKind = "placeholder" }
    )
}

function Get-SyncellerProjectRoot {
    [CmdletBinding()]
    param()

    $productsRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
    $candidate = Join-Path $productsRoot "prj-synceller"
    if (Test-Path -LiteralPath $candidate) {
        return $candidate
    }

    return $null
}

function Invoke-SyncellerScriptCapture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("doctor", "resume")]
        [string]$ScriptName
    )

    $projectRoot = Get-SyncellerProjectRoot
    if ([string]::IsNullOrWhiteSpace($projectRoot)) {
        return $null
    }

    $scriptPath = Join-Path $projectRoot ("scripts\{0}.ps1" -f $ScriptName)
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return $null
    }

    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1
    $lines = @($output | ForEach-Object { "$_" })
    return [pscustomobject]@{
        projectRoot = $projectRoot
        scriptPath = $scriptPath
        lines = $lines
        exitCode = $LASTEXITCODE
    }
}

function Convert-TextStateToStatus {
    [CmdletBinding()]
    param(
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "unknown"
    }

    switch -Regex ($Value.ToLowerInvariant()) {
        "(ready|connected|running|available|ok|online)" { return "healthy" }
        "(not ready|missing|stopped|failed|down|error|duplicated)" { return "down" }
        default { return "degraded" }
    }
}

function Find-LineAfterMarker {
    [CmdletBinding()]
    param(
        [string[]]$Lines,
        [string]$Marker
    )

    for ($index = 0; $index -lt $Lines.Count; $index++) {
        if ($Lines[$index] -eq $Marker) {
            if (($index + 1) -lt $Lines.Count) {
                return $Lines[$index + 1].Trim()
            }
        }
    }

    return $null
}

function Get-SyncellerDoctorComponents {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string[]]$Lines
    )

    $dockerLine = Find-LineAfterMarker -Lines $Lines -Marker "[doctor] docker ready"
    $postgresLine = Find-LineAfterMarker -Lines $Lines -Marker "[doctor] postgres readiness"
    $runtimeLine = Find-LineAfterMarker -Lines $Lines -Marker "[doctor] synceller host runtime"
    $statusLine = $Lines | Where-Object { $_ -like "availability=* slack=* app_server=* reason=*" } | Select-Object -Last 1

    $slackState = $null
    $appServerState = $null
    $availabilityState = $null
    if ($statusLine -match "availability=(\S+)\s+slack=(\S+)\s+app_server=(\S+)\s+reason=(.*)$") {
        $availabilityState = $matches[1]
        $slackState = $matches[2]
        $appServerState = $matches[3]
    }

    $components = @(
        [pscustomobject]@{
            name = "Slack"
            status = Convert-TextStateToStatus -Value $slackState
            detail = if ($statusLine) { $statusLine } else { "Synceller doctor output did not include Slack state." }
            checkedAt = (Get-Date).ToString("o")
            manualIntervention = $false
        }
        [pscustomobject]@{
            name = "Docker"
            status = Convert-TextStateToStatus -Value $dockerLine
            detail = if ($dockerLine) { $dockerLine } else { "Synceller doctor output did not include Docker readiness." }
            checkedAt = (Get-Date).ToString("o")
            manualIntervention = $false
        }
        [pscustomobject]@{
            name = "PostgreSQL"
            status = Convert-TextStateToStatus -Value $postgresLine
            detail = if ($postgresLine) { $postgresLine } else { "Synceller doctor output did not include PostgreSQL readiness." }
            checkedAt = (Get-Date).ToString("o")
            manualIntervention = $false
        }
        [pscustomobject]@{
            name = "Synceller"
            status = Convert-TextStateToStatus -Value $availabilityState
            detail = if ($runtimeLine) { $runtimeLine } else { "Synceller doctor output did not include runtime state." }
            checkedAt = (Get-Date).ToString("o")
            manualIntervention = $false
        }
        [pscustomobject]@{
            name = "app-server"
            status = Convert-TextStateToStatus -Value $appServerState
            detail = if ($statusLine) { $statusLine } else { "Synceller doctor output did not include app-server state." }
            checkedAt = (Get-Date).ToString("o")
            manualIntervention = $false
        }
    )

    return $components
}

function Get-PlaceholderComponentStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Target
    )

    $detail = switch ($Target.CheckKind) {
        "service" {
            "Runtime command is not wired yet. Service-specific mapping will be added in MRL-3."
        }
        default {
            "Placeholder target. Real diagnostic command is pending."
        }
    }

    [pscustomobject]@{
        name = $Target.Name
        status = "unknown"
        detail = $detail
        checkedAt = (Get-Date).ToString("o")
        manualIntervention = $false
    }
}

function Get-OverallStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Components
    )

    if ($Components.status -contains "down") {
        return "needs_manual_intervention"
    }

    if (($Components.status -contains "degraded") -or ($Components.status -contains "unknown")) {
        return "needs_resume"
    }

    return "ready"
}

function Invoke-DoctorContract {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session
    )

    $components = foreach ($target in Get-RemoteRecoveryTargets) {
        Get-PlaceholderComponentStatus -Target $target
    }

    $syncellerDoctor = Invoke-SyncellerScriptCapture -ScriptName "doctor"
    if ($syncellerDoctor -and $syncellerDoctor.exitCode -eq 0) {
        $components = Get-SyncellerDoctorComponents -Lines $syncellerDoctor.lines
    }

    $result = [pscustomobject]@{
        sessionId = $Session.SessionId
        phase = "doctor"
        executedAt = (Get-Date).ToString("o")
        overallStatus = Get-OverallStatus -Components $components
        manualInterventionRequired = (($components.status -contains "down") -or ($syncellerDoctor -and $syncellerDoctor.exitCode -ne 0))
        degradedComponents = @($components | Where-Object { $_.status -in @("degraded", "down", "unknown") } | Select-Object -ExpandProperty name)
        components = $components
        source = if ($syncellerDoctor -and $syncellerDoctor.exitCode -eq 0) { "synceller-doctor" } else { "placeholder" }
        sourceScript = if ($syncellerDoctor) { $syncellerDoctor.scriptPath } else { $null }
        evidencePath = Get-RecoveryEvidencePath -Session $Session -Phase "doctor" -Extension "json"
    }

    Write-RecoveryJson -Path $result.evidencePath -Data $result | Out-Null
    return $result
}

function Invoke-ResumeContract {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session,
        [string[]]$ResumeTarget,
        [switch]$WhatIf,
        [switch]$Force
    )

    if (-not $ResumeTarget -or $ResumeTarget.Count -eq 0) {
        $ResumeTarget = @("Slack", "Docker", "PostgreSQL", "Synceller", "app-server")
    }

    $syncellerResume = $null
    $lockPath = $null
    if (-not $WhatIf) {
        $lockPath = Acquire-ResumeLock -Session $Session -Force:$Force
        try {
            $syncellerResume = Invoke-SyncellerScriptCapture -ScriptName "resume"
        }
        finally {
            Release-ResumeLock -Session $Session
        }
    }

    $steps = foreach ($target in $ResumeTarget) {
        $detail = if ($WhatIf) {
            "Preview only. Remote wrapper did not execute Synceller resume."
        } elseif ($syncellerResume -and $syncellerResume.exitCode -eq 0) {
            "Executed through --process/--products/prj-synceller/scripts/resume.ps1."
        } elseif ($syncellerResume) {
            "Synceller resume exited with code $($syncellerResume.exitCode)."
        } else {
            "Concrete resume command will be wired in MRL-3."
        }

        [pscustomobject]@{
            target = $target
            action = if ($WhatIf) { "preview-resume" } else { "synceller-resume" }
            status = if ($WhatIf) { "preview" } elseif ($syncellerResume -and $syncellerResume.exitCode -eq 0) { "completed" } else { "pending-implementation" }
            detail = $detail
        }
    }

    $result = [pscustomobject]@{
        sessionId = $Session.SessionId
        phase = "resume"
        executedAt = (Get-Date).ToString("o")
        whatIf = [bool]$WhatIf
        steps = $steps
        failedTargets = if ($syncellerResume -and $syncellerResume.exitCode -ne 0) { @($ResumeTarget) } else { @() }
        source = if ($WhatIf) { "preview" } elseif ($syncellerResume) { "synceller-resume" } else { "placeholder" }
        sourceScript = if ($syncellerResume) { $syncellerResume.scriptPath } else { $null }
        lockPath = $lockPath
        evidencePath = Get-RecoveryEvidencePath -Session $Session -Phase "resume" -Extension "json"
    }

    Write-RecoveryJson -Path $result.evidencePath -Data $result | Out-Null
    return $result
}

function Save-CaptureEvidence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session,
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [string]$Label = "slack-status"
    )

    if (-not (Test-Path -LiteralPath $Session.CapturesPath)) {
        New-Item -ItemType Directory -Path $Session.CapturesPath -Force | Out-Null
    }

    $extension = [System.IO.Path]::GetExtension($SourcePath)
    $destination = Join-Path $Session.CapturesPath ("{0}-{1}-{2}{3}" -f $Session.Timestamp, $Session.SessionId, $Label, $extension)
    Copy-Item -LiteralPath $SourcePath -Destination $destination -Force
    return $destination
}

function Invoke-RecheckContract {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session
    )

    $doctor = Invoke-DoctorContract -Session $Session
    $doctor.phase = "recheck"
    $doctor.evidencePath = Get-RecoveryEvidencePath -Session $Session -Phase "recheck" -Extension "json"
    Write-RecoveryJson -Path $doctor.evidencePath -Data $doctor | Out-Null
    return $doctor
}

function New-RecoverySummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Session,
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Doctor,
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Resume,
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Recheck
    )

    $overallStatus = if ($Recheck.overallStatus -eq "ready") { "ready" } else { "needs_manual_intervention" }
    $nextAction = if ($overallStatus -eq "ready") { "Run /codex status from Slack." } else { "Review evidence and wire concrete runtime commands before live recovery." }

    $summary = [pscustomobject]@{
        sessionId = $Session.SessionId
        phase = "summary"
        executedAt = (Get-Date).ToString("o")
        overallStatus = $overallStatus
        manualInterventionRequired = ($overallStatus -ne "ready")
        nextAction = $nextAction
        shouldRevalidateSlack = $true
        evidence = [pscustomobject]@{
            doctor = $Doctor.evidencePath
            resume = $Resume.evidencePath
            recheck = $Recheck.evidencePath
        }
        notes = @(
            "This is a contract-level placeholder summary."
            "Replace placeholder checks with Synceller runtime commands in MRL-3."
        )
    }

    $jsonPath = Get-RecoveryEvidencePath -Session $Session -Phase "summary" -Extension "json"
    $mdPath = Get-RecoveryEvidencePath -Session $Session -Phase "summary" -Extension "md"
    Write-RecoveryJson -Path $jsonPath -Data $summary | Out-Null

    $lines = @(
        "# Remote Recovery Summary"
        ""
        "- session: ``{0}``" -f $summary.sessionId
        "- overall status: ``{0}``" -f $summary.overallStatus
        "- manual intervention required: ``{0}``" -f $summary.manualInterventionRequired
        "- next action: {0}" -f $summary.nextAction
        "- doctor evidence: ``{0}``" -f $summary.evidence.doctor
        "- resume evidence: ``{0}``" -f $summary.evidence.resume
        "- recheck evidence: ``{0}``" -f $summary.evidence.recheck
    )
    Write-RecoveryMarkdown -Path $mdPath -Lines $lines | Out-Null

    $summary | Add-Member -NotePropertyName jsonPath -NotePropertyValue $jsonPath
    $summary | Add-Member -NotePropertyName markdownPath -NotePropertyValue $mdPath
    return $summary
}
