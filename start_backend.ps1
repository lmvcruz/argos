# Start Lens Backend Server
Set-Location d:\playground\argos
Write-Host "Starting Lens Backend Server on http://0.0.0.0:8000" -ForegroundColor Green
python -m uvicorn lens.backend.server:app --host 0.0.0.0 --port 8000
