[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$SpecPath = Join-Path $ProjectRoot "packaging\pyinstaller\AIImageLayerExtractor.spec"
$ExePath = Join-Path $ProjectRoot "dist\AIImageLayerExtractor\AIImageLayerExtractor.exe"

function Invoke-Logged {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Command,
        [Parameter(Mandatory = $true)][string]$Message
    )

    Write-Host ""
    Write-Host "==> $Message"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Message failed with exit code $LASTEXITCODE."
    }
}

function Get-HostPythonCommand {
    $PyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        return @($PyLauncher.Source, "-3")
    }

    $Python = Get-Command "python.exe" -ErrorAction SilentlyContinue
    if ($null -ne $Python) {
        return @($Python.Source)
    }

    throw "Python was not found. Install Python 3.10+ and make it available on PATH."
}

Push-Location $ProjectRoot
try {
    Write-Host "Project root: $ProjectRoot"

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        $HostPython = Get-HostPythonCommand
        Write-Host "Creating virtual environment at $VenvDir"
        $HostPythonArgs = @()
        if ($HostPython.Count -gt 1) {
            $HostPythonArgs = $HostPython[1..($HostPython.Count - 1)]
        }
        $HostPythonExe = $HostPython[0]
        & $HostPythonExe @HostPythonArgs -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "Creating virtual environment failed with exit code $LASTEXITCODE."
        }
    }

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        throw "Virtual environment Python was not created: $VenvPython"
    }

    Invoke-Logged { & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt") } "Installing runtime dependencies"
    Invoke-Logged { & $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements-dev.txt") } "Installing development and packaging dependencies"

    if (-not $SkipTests) {
        Invoke-Logged { & $VenvPython -B -m pytest } "Running tests"
    }

    Invoke-Logged { & $VenvPython -m PyInstaller --noconfirm $SpecPath } "Building onedir EXE with PyInstaller"

    if (-not (Test-Path -LiteralPath $ExePath)) {
        throw "PyInstaller build finished, but EXE was not found: $ExePath"
    }

    if (-not $SkipSmokeTest) {
        Write-Host ""
        Write-Host "==> Running packaged EXE smoke test"
        $OldQtPlatform = $env:QT_QPA_PLATFORM
        $OldLocalAppData = $env:LOCALAPPDATA
        $env:QT_QPA_PLATFORM = "offscreen"
        $env:LOCALAPPDATA = Join-Path $ProjectRoot "build\smoke_localappdata"
        try {
            $Process = Start-Process -FilePath $ExePath -ArgumentList "--smoke-test" -Wait -PassThru
            if ($Process.ExitCode -ne 0) {
                throw "Packaged EXE smoke test failed with exit code $($Process.ExitCode)."
            }
        }
        finally {
            $env:QT_QPA_PLATFORM = $OldQtPlatform
            $env:LOCALAPPDATA = $OldLocalAppData
        }
    }

    Write-Host ""
    Write-Host "EXE build complete:"
    Write-Host "  $ExePath"
}
finally {
    Pop-Location
}
