param(
    [int]$Port = 47111,
    [string]$TargetRoot = "C:\Users\tetsuya\kisaragi\kisaragi-db\--exsams\prj-kisaragi_0002\pc-transfer-inbox",
    [int]$IdleSeconds = 120
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
$listener.Start()
$listener.Server.ReceiveTimeout = 1000

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
$lastActivity = Get-Date

function Read-HttpRequest {
    param([System.Net.Sockets.TcpClient]$Client)

    $stream = $Client.GetStream()
    $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::ASCII, $false, 8192, $true)
    $requestLine = $reader.ReadLine()
    if ([string]::IsNullOrWhiteSpace($requestLine)) {
        return $null
    }
    $headers = @{}
    while ($true) {
        $line = $reader.ReadLine()
        if ([string]::IsNullOrEmpty($line)) {
            break
        }
        $separator = $line.IndexOf(":")
        if ($separator -gt 0) {
            $headers[$line.Substring(0, $separator).Trim()] = $line.Substring($separator + 1).Trim()
        }
    }
    $length = 0
    if ($headers.ContainsKey("Content-Length")) {
        $length = [int]$headers["Content-Length"]
    }
    $body = New-Object byte[] $length
    $offset = 0
    while ($offset -lt $length) {
        $read = $stream.Read($body, $offset, $length - $offset)
        if ($read -le 0) {
            break
        }
        $offset += $read
    }
    [pscustomobject]@{
        RequestLine = $requestLine
        Headers = $headers
        Body = $body
        Stream = $stream
    }
}

function Write-HttpJson {
    param(
        [System.Net.Sockets.NetworkStream]$Stream,
        [int]$StatusCode,
        [string]$Body
    )

    $reason = if ($StatusCode -eq 200) { "OK" } else { "Bad Request" }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $header =
        "HTTP/1.1 $StatusCode $reason`r`n" +
        "Content-Type: application/json; charset=utf-8`r`n" +
        "Content-Length: $($bytes.Length)`r`n" +
        "Connection: close`r`n`r`n"
    $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($header)
    $Stream.Write($headerBytes, 0, $headerBytes.Length)
    $Stream.Write($bytes, 0, $bytes.Length)
}

function Expand-ZipToTarget {
    param(
        [byte[]]$ZipBytes,
        [string]$SessionId
    )

    $zipPath = Join-Path $TargetRoot "$SessionId.zip"
    [System.IO.File]::WriteAllBytes($zipPath, $ZipBytes)
    $sessionRoot = Join-Path $TargetRoot $SessionId
    if (Test-Path $sessionRoot) {
        Remove-Item -Recurse -Force $sessionRoot
    }
    New-Item -ItemType Directory -Force -Path $sessionRoot | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $sessionRoot -Force
    return $sessionRoot
}

try {
    while ($true) {
        if ($listener.Pending()) {
            $client = $listener.AcceptTcpClient()
            try {
                $request = Read-HttpRequest -Client $client
                if ($null -eq $request) {
                    continue
                }
                $lastActivity = Get-Date
                $parts = $request.RequestLine.Split(" ")
                $method = $parts[0]
                $path = $parts[1]

                if ($method -eq "GET" -and $path -eq "/health") {
                    Write-HttpJson -Stream $request.Stream -StatusCode 200 -Body (@{
                        status = "ready"
                        port = $Port
                        targetRoot = $TargetRoot
                    } | ConvertTo-Json -Compress)
                    continue
                }

                if ($method -ne "POST" -or -not $path.StartsWith("/upload")) {
                    Write-HttpJson -Stream $request.Stream -StatusCode 400 -Body (@{ error = "unsupported request" } | ConvertTo-Json -Compress)
                    continue
                }

                $sessionId = "session-" + (Get-Date -Format "yyyyMMdd-HHmmss")
                if ($path -match "sessionId=([^& ]+)") {
                    $sessionId = [System.Uri]::UnescapeDataString($matches[1])
                }
                $storedPath = Expand-ZipToTarget -ZipBytes $request.Body -SessionId $sessionId
                Write-HttpJson -Stream $request.Stream -StatusCode 200 -Body (@{
                    status = "stored"
                    sessionId = $sessionId
                    targetRoot = $storedPath
                } | ConvertTo-Json -Compress)
            } finally {
                $client.Close()
            }
        } else {
            Start-Sleep -Milliseconds 500
        }

        if (((Get-Date) - $lastActivity).TotalSeconds -ge $IdleSeconds) {
            break
        }
    }
} finally {
    $listener.Stop()
}
