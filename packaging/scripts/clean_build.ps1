[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Remove-PathInsideProject {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $Resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $Resolved.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside project: $Resolved"
    }

    Write-Host "Removing $Resolved"
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}

Write-Host "Project root: $ProjectRoot"

Remove-PathInsideProject (Join-Path $ProjectRoot "build")
Remove-PathInsideProject (Join-Path $ProjectRoot "dist")
Remove-PathInsideProject (Join-Path $ProjectRoot "release")

Get-ChildItem -LiteralPath $ProjectRoot -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike (Join-Path $ProjectRoot ".venv*") + "*" } |
    ForEach-Object {
        Remove-PathInsideProject $_.FullName
    }

Get-ChildItem -LiteralPath $ProjectRoot -File -Filter "*.spec" -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-PathInsideProject $_.FullName
    }

Write-Host "Clean complete."
