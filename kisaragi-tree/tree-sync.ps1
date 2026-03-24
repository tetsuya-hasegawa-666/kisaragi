$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Remove-TreeNode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-Item -LiteralPath $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        cmd /c "rmdir `"$Path`"" | Out-Null
        return
    }

    Remove-Item -LiteralPath $Path -Recurse -Force
}

function New-Junction {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LinkPath,
        [Parameter(Mandatory = $true)]
        [string]$TargetPath
    )

    if (Test-Path -LiteralPath $LinkPath) {
        Remove-TreeNode -Path $LinkPath
    }

    cmd /c "mklink /J `"$LinkPath`" `"$TargetPath`"" | Out-Null
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$devRoot = Join-Path $repoRoot "kisaragi-db\--devs"
$treeRoot = Join-Path $repoRoot "kisaragi-tree"

$categoryDirs = Get-ChildItem -LiteralPath $devRoot -Directory |
    Where-Object { $_.Name -like "--*" }

$projectMap = [ordered]@{}
foreach ($categoryDir in $categoryDirs) {
    $projectDirs = Get-ChildItem -LiteralPath $categoryDir.FullName -Directory |
        Where-Object { $_.Name -like "prj-*" }

    foreach ($projectDir in $projectDirs) {
        if (-not $projectMap.Contains($projectDir.Name)) {
            $projectMap[$projectDir.Name] = [ordered]@{}
        }

        $projectMap[$projectDir.Name][$categoryDir.Name] = $projectDir.FullName
    }
}

Get-ChildItem -LiteralPath $treeRoot -Force -Directory |
    Where-Object { $_.Name -like "prj-*" } |
    ForEach-Object { Remove-TreeNode -Path $_.FullName }

foreach ($projectName in $projectMap.Keys) {
    $projectRoot = Join-Path $treeRoot $projectName
    New-Item -ItemType Directory -Force -Path $projectRoot | Out-Null

    foreach ($categoryName in $projectMap[$projectName].Keys) {
        $linkPath = Join-Path $projectRoot $categoryName
        $targetPath = $projectMap[$projectName][$categoryName]
        New-Junction -LinkPath $linkPath -TargetPath $targetPath
    }
}

Write-Host "tree sync completed"
