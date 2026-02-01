@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "BACKEND_PORT=5000"
set "FRONTEND_PORT=8000"

echo Starting backend on port %BACKEND_PORT%...
start "backend" /B python "%ROOT%server.py"

ping -n 2 127.0.0.1 >nul

echo Starting frontend on port %FRONTEND_PORT%...
start "frontend" /B python -m http.server %FRONTEND_PORT%

ping -n 2 127.0.0.1 >nul

start "" "http://localhost:%FRONTEND_PORT%/HTMLs/index.html"

echo.
echo Frontend: http://localhost:%FRONTEND_PORT%/HTMLs/index.html
echo Backend:  http://localhost:%BACKEND_PORT%
echo.
echo Close this window to stop. Use Task Manager to end python if needed.
pause
