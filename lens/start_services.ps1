# Start Lens Backend and Frontend Services
# This script starts both services in separate PowerShell windows

Write-Host "============================================================"
Write-Host "Starting Lens Services"
Write-Host "============================================================"
Write-Host ""

# Change to the argos root directory
$argosRoot = "D:\playground\argos"
$lensRoot = "D:\playground\argos\lens"

# Start Backend (must run from argos root for database access)
Write-Host "Starting Backend Server on port 8000..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$argosRoot'; Write-Host 'Backend Server (Port 8000)' -ForegroundColor Green; python -m uvicorn lens.backend.server:app --port 8000 --host 0.0.0.0"
)

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend Dev Server on port 3000..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$lensRoot\frontend'; Write-Host 'Frontend Dev Server (Port 3000)' -ForegroundColor Cyan; npm run dev -- --port 3000"
)

Write-Host ""
Write-Host "============================================================"
Write-Host "Services Started Successfully!"
Write-Host "============================================================"
Write-Host ""
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Both services are running in separate windows."
Write-Host "Close this window or press Ctrl+C to exit this script."
Write-Host "To stop services, close their respective windows or run:"
Write-Host "  python lens\kill_services.py"
Write-Host ""
