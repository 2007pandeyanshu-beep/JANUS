# Launch JANUS 5 Internal Specialist uAgents (Local HTTP IPC Mode)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment Python executable not found at: $PythonExe"
    exit 1
}

$specialists = @(
    @{ Name = "Auditor Agent (Port 8009)"; Script = "backend\agents\auditor_agent.py" },
    @{ Name = "Research Agent (Port 8010)"; Script = "backend\agents\research_agent.py" },
    @{ Name = "Hypothesis Analyst Agent (Port 8011)"; Script = "backend\agents\hypothesis_analyst_agent.py" },
    @{ Name = "Scientific Tool Agent (Port 8012)"; Script = "backend\agents\scientific_tool_agent.py" },
    @{ Name = "Experiment Designer Agent (Port 8013)"; Script = "backend\agents\experiment_designer_agent.py" }
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Starting 5 JANUS Internal Specialist uAgents (Local HTTP IPC Mode)..." -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

foreach ($s in $specialists) {
    $scriptPath = Join-Path $ProjectRoot $s.Script
    if (Test-Path $scriptPath) {
        Write-Host "Launching $($s.Name)..." -ForegroundColor Green
        Start-Process -FilePath $PythonExe -ArgumentList $scriptPath -WindowStyle Hidden
    } else {
        Write-Warning "Specialist script not found: $scriptPath"
    }
}

Write-Host "`nAll 5 specialists dispatched to background processes." -ForegroundColor Cyan
Write-Host "Ports listening on: 8009, 8010, 8011, 8012, 8013" -ForegroundColor Gray
