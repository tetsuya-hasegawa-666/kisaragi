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

function Get-LocalIpv4Address {
    $addresses =
        [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
        Where-Object { $_.OperationalStatus -eq "Up" } |
        ForEach-Object {
            $_.GetIPProperties().UnicastAddresses |
            Where-Object {
                $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
                -not $_.Address.IPAddressToString.StartsWith("169.254.")
            } |
            Select-Object -ExpandProperty Address
        }
    return ($addresses | Select-Object -First 1).IPAddressToString
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
                $replyHost = Get-LocalIpv4Address
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
