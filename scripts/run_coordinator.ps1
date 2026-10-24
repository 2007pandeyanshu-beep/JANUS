# Launch JANUS Fetch.ai Coordinator Agent (Agentverse Mailbox Mode)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment Python executable not found at: $PythonExe"
    exit 1
}

$CoordinatorScript = Join-Path $ProjectRoot "backend\agents\fetch_agent.py"
if (-not (Test-Path $CoordinatorScript)) {
    Write-Error "Coordinator script not found at: $CoordinatorScript"
    exit 1
}

# Explicitly enable Mailbox mode for the public Coordinator
$env:JANUS_USE_MAILBOX = "true"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Starting JANUS Coordinator uAgent (Agentverse Mailbox Mode)..." -ForegroundColor Cyan
Write-Host " Python:       $PythonExe" -ForegroundColor Gray
Write-Host " Mailbox Mode: Enabled (JANUS_USE_MAILBOX=true)" -ForegroundColor Gray
Write-Host " Target:       $CoordinatorScript" -ForegroundColor Gray
Write-Host "================================================================================" -ForegroundColor Cyan

try {
    & $PythonExe $CoordinatorScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "JANUS Coordinator process exited with code $LASTEXITCODE."
        exit $LASTEXITCODE
    }
}
catch {
    Write-Error "Failed to run JANUS Coordinator uAgent: $_"
    exit 1
}
