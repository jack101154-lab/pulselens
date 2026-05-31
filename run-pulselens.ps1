$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path $BundledPython) {
    $Python = $BundledPython
} else {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $Python) {
    Write-Host "Python was not found. Install Python 3.10+ or run this project from Codex's bundled runtime." -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot
& $Python -m pulselens.cli @args
