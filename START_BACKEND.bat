@echo off
cd /d D:\playground\argos
echo ========================================
echo   Lens Backend Server
echo ========================================
echo.
echo Starting backend on http://127.0.0.1:8000
echo.
echo WARNING: DO NOT CLOSE THIS WINDOW!
echo WARNING: DO NOT RUN OTHER COMMANDS HERE!
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
python -m uvicorn lens.backend.server:app --port 8000 --host 127.0.0.1
pause
