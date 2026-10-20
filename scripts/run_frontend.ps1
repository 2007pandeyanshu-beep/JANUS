# Launch JANUS React + Vite Frontend Server
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location "$ProjectRoot\frontend"
Write-Host "Starting JANUS Frontend on http://localhost:5173 ..." -ForegroundColor Cyan
npm run dev
