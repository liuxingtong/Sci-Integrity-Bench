# One-click: start viz server + meta-runner with --viz
# Self-re-invoke with ExecutionPolicy Bypass if blocked
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")) {
    $pol = Get-ExecutionPolicy -Scope CurrentUser
    if ($pol -eq 'Restricted' -or $pol -eq 'AllSigned') {
        Write-Host "Re-launching with ExecutionPolicy Bypass..." -ForegroundColor Yellow
        Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Wait
        exit
    }
}

$VizDir = $PSScriptRoot
$ProjectRoot = Split-Path (Split-Path $VizDir -Parent) -Parent

Write-Host ""
Write-Host "=== AI Scientist Live Viz ===" -ForegroundColor Cyan
Write-Host "Starting viz server on http://127.0.0.1:8765 ..." -ForegroundColor Green

    # Start server in a new cmd window so it stays alive
$serveCmd = "cd /d `"$VizDir`" && python serve.py --port 8765 && pause"
Start-Process cmd.exe -ArgumentList "/K", $serveCmd
Start-Sleep -Seconds 2

Write-Host "Opening Live Monitor ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8765/live"

Write-Host ""
Write-Host "Starting meta-runner with --viz ..." -ForegroundColor Green
Set-Location $ProjectRoot
python -m meta_benchmark.meta_runner --viz
