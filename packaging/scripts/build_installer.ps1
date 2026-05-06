[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ExePath = Join-Path $ProjectRoot "dist\AIImageLayerExtractor\AIImageLayerExtractor.exe"
$IssPath = Join-Path $ProjectRoot "packaging\inno\AIImageLayerExtractor.iss"
$InstallerPath = Join-Path $ProjectRoot "release\AIImageLayerExtractor_Setup_0.1.0_x64.exe"

function Resolve-Iscc {
    $Command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($null -ne $Command) {
        return $Command.Source
    }

    $CommonPaths = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($Path in $CommonPaths) {
        if (Test-Path -LiteralPath $Path) {
            return $Path
        }
    }

    throw "ISCC.exe not found. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php and rerun this script."
}

Push-Location $ProjectRoot
try {
    Write-Host "Project root: $ProjectRoot"

    if (-not (Test-Path -LiteralPath $ExePath)) {
        throw "Packaged EXE not found. Run .\packaging\scripts\build_exe.ps1 first. Missing: $ExePath"
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "release") | Out-Null

    $Iscc = Resolve-Iscc
    Write-Host "Using Inno Setup compiler: $Iscc"
    & $Iscc $IssPath
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compiler failed with exit code $LASTEXITCODE."
    }

    if (-not (Test-Path -LiteralPath $InstallerPath)) {
        throw "Installer build finished, but output was not found: $InstallerPath"
    }

    Write-Host ""
    Write-Host "Installer build complete:"
    Write-Host "  $InstallerPath"
}
finally {
    Pop-Location
}
