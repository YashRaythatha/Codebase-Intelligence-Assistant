@echo off
REM Start the Next.js frontend (UI on http://localhost:3000)
cd /d "%~dp0\frontend"
echo Starting frontend...
call npm run dev
pause
