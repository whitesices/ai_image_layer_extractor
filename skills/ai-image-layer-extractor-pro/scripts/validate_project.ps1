param(
    [string]$ProjectRoot,
    [string]$PythonExe,
    [switch]$SkipCompile,
    [switch]$SkipPytest,
    [switch]$SkipLauncherSmoke
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonExe = $venvPython
    } else {
        $PythonExe = "python"
    }
}

Push-Location $ProjectRoot
try {
    Write-Host "ProjectRoot: $ProjectRoot"
    Write-Host "PythonExe:   $PythonExe"

    if (-not $SkipCompile) {
        Write-Host "Running compileall..."
        & $PythonExe -m compileall app core llm image_editors segmenters detectors matting pipeline exporters tests main.py launcher.py
        if ($LASTEXITCODE -ne 0) { throw "compileall failed with exit code $LASTEXITCODE" }
    }

    if (-not $SkipPytest) {
        Write-Host "Running pytest..."
        & $PythonExe -B -m pytest
        if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
    }

    if (-not $SkipLauncherSmoke) {
        Write-Host "Running launcher smoke test..."
        $oldQt = $env:QT_QPA_PLATFORM
        $oldLocalAppData = $env:LOCALAPPDATA
        $env:QT_QPA_PLATFORM = "offscreen"
        $env:LOCALAPPDATA = Join-Path $ProjectRoot "build\skill_smoke_localappdata"
        New-Item -ItemType Directory -Force -Path $env:LOCALAPPDATA | Out-Null
        try {
            & $PythonExe launcher.py --smoke-test
            if ($LASTEXITCODE -ne 0) { throw "launcher smoke test failed with exit code $LASTEXITCODE" }
        } finally {
            $env:QT_QPA_PLATFORM = $oldQt
            $env:LOCALAPPDATA = $oldLocalAppData
        }
    }

    Write-Host "Validation OK"
} finally {
    Pop-Location
}
