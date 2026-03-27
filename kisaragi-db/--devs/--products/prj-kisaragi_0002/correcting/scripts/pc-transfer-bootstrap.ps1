param(
    [int]$BootstrapPort = 47110,
    [int]$TransferPort = 47111,
    [int]$IdleSeconds = 300,
    [string]$TargetRoot = "C:\Users\tetsuya\kisaragi\kisaragi-db\--exsams\prj-kisaragi_0002\pc-transfer-inbox"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$receiverScript = Join-Path $PSScriptRoot "pc-transfer-receiver.ps1"
$udpClient = [System.Net.Sockets.UdpClient]::new($BootstrapPort)
$udpClient.Client.ReceiveTimeout = 1000
$lastActivity = Get-Date

function Test-SameSubnet24 {
    param(
        [string]$Left,
        [string]$Right
    )

    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
        return $false
    }

    $leftParts = $Left.Split(".")
    $rightParts = $Right.Split(".")
    if ($leftParts.Count -ne 4 -or $rightParts.Count -ne 4) {
        return $false
    }
    return $leftParts[0] -eq $rightParts[0] -and $leftParts[1] -eq $rightParts[1] -and $leftParts[2] -eq $rightParts[2]
}

function Get-LocalIpv4Address {
    param([string]$RemoteAddress)

    $candidates =
        Get-NetIPConfiguration |
        Where-Object {
            $null -ne $_.IPv4Address -and
            $_.NetAdapter.Status -eq "Up" -and
            -not $_.IPv4Address.IPAddress.StartsWith("169.254.") -and
            $_.InterfaceAlias -notmatch "Bluetooth|Loopback" -and
            $_.InterfaceDescription -notmatch "Tailscale|Hyper-V|Virtual|VMware|Wintun"
        } |
        Select-Object `
            @{ Name = "InterfaceAlias"; Expression = { $_.InterfaceAlias } }, `
            @{ Name = "InterfaceDescription"; Expression = { $_.InterfaceDescription } }, `
            @{ Name = "IPAddress"; Expression = { $_.IPv4Address.IPAddress } }, `
            @{ Name = "HasGateway"; Expression = { $null -ne $_.IPv4DefaultGateway } }

    $ranked =
        $candidates |
        Sort-Object `
            @{ Expression = { if (Test-SameSubnet24 $_.IPAddress $RemoteAddress) { 0 } else { 1 } } }, `
            @{ Expression = { if ($_.InterfaceAlias -match "^Wi-Fi") { 0 } else { 1 } } }, `
            @{ Expression = { if ($_.HasGateway) { 0 } else { 1 } } }, `
            InterfaceAlias

    return ($ranked | Select-Object -First 1).IPAddress
}

function Start-ReceiverIfNeeded {
    $existing =
        Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -like "*pc-transfer-receiver.ps1*" -and
            $_.CommandLine -like "*-Port $TransferPort*"
        } |
        Select-Object -First 1

    if ($null -ne $existing) {
        return
    }

    Start-Process powershell -ArgumentList @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $receiverScript,
        "-Port", $TransferPort,
        "-TargetRoot", $TargetRoot,
        "-IdleSeconds", 120
    ) | Out-Null
}

try {
    while ($true) {
        try {
            $remoteEndpoint = [System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any, 0)
            $bytes = $udpClient.Receive([ref]$remoteEndpoint)
            $message = [System.Text.Encoding]::UTF8.GetString($bytes)
            if ($message.StartsWith("TRAJECTREVIEW_BOOTSTRAP|")) {
                Start-ReceiverIfNeeded
                $replyHost = Get-LocalIpv4Address -RemoteAddress $remoteEndpoint.Address.IPAddressToString
                if ([string]::IsNullOrWhiteSpace($replyHost)) {
                    $replyHost = $env:COMPUTERNAME
                }
                $reply = "READY|$replyHost|$TransferPort|$env:COMPUTERNAME|$TargetRoot"
                $replyBytes = [System.Text.Encoding]::UTF8.GetBytes($reply)
                [void]$udpClient.Send($replyBytes, $replyBytes.Length, $remoteEndpoint)
                $lastActivity = Get-Date
            }
        } catch [System.Net.Sockets.SocketException] {
        }

        if (((Get-Date) - $lastActivity).TotalSeconds -ge $IdleSeconds) {
            break
        }
    }
} finally {
    $udpClient.Close()
}
