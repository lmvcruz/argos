@echo off
cd /d D:\playground\argos\lens\frontend
echo ========================================
echo   Lens Frontend Server
echo ========================================
echo.
echo Starting frontend on http://localhost:3000
echo.
echo WARNING: DO NOT CLOSE THIS WINDOW!
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
npm run dev -- --port 3000
pause
