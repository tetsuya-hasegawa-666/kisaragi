param(
  [string]$LaunchAnchorPath,
  [string]$DisplayRoot
)

$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference = "Stop"

$projectRoot = "C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-direview"
$dashboardUrl = "http://127.0.0.1:4173/"
$manifestOutputDir = "C:\Users\tetsuya\kisaragi\kisaragi-db\--exsams\prj-direview\launch"

function Resolve-DisplayRoot {
  param(
    [string]$LaunchAnchorPath,
    [string]$DisplayRoot
  )

  if ($DisplayRoot) {
    return (Resolve-Path -LiteralPath $DisplayRoot).Path
  }

  $anchor = if ($LaunchAnchorPath) { $LaunchAnchorPath } else { (Get-Location).Path }
  $resolvedAnchor = (Resolve-Path -LiteralPath $anchor).Path
  $parent = Split-Path -Parent $resolvedAnchor

  if (-not $parent) {
    throw "Display root parent could not be resolved from launch anchor."
  }

  return $parent
}

function New-LaunchManifest {
  param(
    [string]$ManifestPath,
    [string]$ResolvedDisplayRoot
  )

  $workspaceParent = Split-Path -Parent $ResolvedDisplayRoot
  if (-not $workspaceParent) {
    throw "Display root parent was not found."
  }
  $displayRootName = Split-Path -Leaf $ResolvedDisplayRoot
  $dbRoot = Join-Path $ResolvedDisplayRoot "kisaragi-db"
  $treeRoot = Join-Path $ResolvedDisplayRoot "kisaragi-tree"
  $sourceProfiles = @()

  if (Test-Path -LiteralPath $dbRoot) {
    $sourceProfiles += @{
      profileId = "db-view"
      label = "db-view"
      projectRoot = $workspaceParent
      documentRoots = @($displayRootName)
      compareRoots = @($displayRootName)
    }
  }

  if (Test-Path -LiteralPath $treeRoot) {
    $sourceProfiles += @{
      profileId = "prj-view"
      label = "prj-view"
      projectRoot = $workspaceParent
      documentRoots = @($displayRootName)
      compareRoots = @($displayRootName)
    }
  }

  if ($sourceProfiles.Count -eq 0) {
    throw "Neither 'kisaragi-db' nor 'kisaragi-tree' was found under display root."
  }

  $manifest = @{
    projectId = "prj-direview"
    sourceProfiles = $sourceProfiles
    ignoreGlobs = @(
      "**/node_modules/**",
      "**/.git/**",
      "**/dist/**",
      "**/build/**",
      "**/--trial-data/**"
    )
    readOnly = $true
  }

  $json = $manifest | ConvertTo-Json -Depth 6
  [System.IO.File]::WriteAllText(
    $ManifestPath,
    $json,
    [System.Text.UTF8Encoding]::new($false)
  )
}

try {
  $resolvedDisplayRoot = Resolve-DisplayRoot -LaunchAnchorPath $LaunchAnchorPath -DisplayRoot $DisplayRoot
  New-Item -ItemType Directory -Force -Path $manifestOutputDir | Out-Null
  $manifestPath = Join-Path $manifestOutputDir "active-project-manifest.json"
  New-LaunchManifest -ManifestPath $manifestPath -ResolvedDisplayRoot $resolvedDisplayRoot

  Set-Location $projectRoot

  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Please check the Node.js installation."
  }

  if (-not (Test-Path (Join-Path $projectRoot "node_modules"))) {
    Write-Host "Installing dependencies with npm ci..." -ForegroundColor Yellow
    npm ci
    if ($LASTEXITCODE -ne 0) {
      throw "npm ci failed."
    }
  }

  $env:DIREVIEW_MANIFEST_PATH = $manifestPath
  $env:CODEV_VIEWER_MANIFEST_PATH = $manifestPath

  Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process $using:dashboardUrl
  } | Out-Null

  Write-Host "Starting direview..." -ForegroundColor Cyan
  Write-Host "Display root: $resolvedDisplayRoot" -ForegroundColor DarkGray
  Write-Host "Press Ctrl+C in this window to stop the server." -ForegroundColor DarkGray

  npm run dashboard
  if ($LASTEXITCODE -ne 0) {
    throw "npm run dashboard failed."
  }
}
catch {
  Write-Host ""
  Write-Host "Dashboard launch failed." -ForegroundColor Red
  Write-Host $_ -ForegroundColor Red
  Read-Host "Press Enter to close"
  exit 1
}
