[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$InstallerPath = Join-Path $ProjectRoot "release\AIImageLayerExtractor_Setup_0.1.0_x64.exe"

& (Join-Path $PSScriptRoot "clean_build.ps1")
& (Join-Path $PSScriptRoot "build_exe.ps1")
& (Join-Path $PSScriptRoot "build_installer.ps1")

Write-Host ""
Write-Host "All build steps completed successfully."
Write-Host "Final installer:"
Write-Host "  $InstallerPath"
