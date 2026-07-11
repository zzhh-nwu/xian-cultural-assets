@echo off
cd /d %~dp0

echo ============================================
echo   Xi'an Cultural Digital Asset Platform
echo   233 Projects (9+102+122)
echo ============================================
echo.

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] python not found in PATH!
    echo Please install Python or add it to system PATH.
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Node
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARN] node not found, frontend will be skipped.
    set NO_FRONTEND=1
) else (
    echo [OK] Node found
)

echo.
echo [0] Killing old processes on ports 8000 and 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do taskkill /f /pid %%a >nul 2>nul
echo [0] Old processes cleared.

echo [1] Starting backend on port 8000...
start "Backend-API" cmd /k "cd /d %~dp0 && set PYTHONIOENCODING=utf-8 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo [1] Backend window opened.

if not defined NO_FRONTEND (
    echo [2] Starting frontend on port 5173...
    start "Frontend-Web" cmd /k "cd /d %~dp0frontend && npm run dev"
    echo [2] Frontend window opened.
    timeout /t 5 /nobreak >nul
    start http://localhost:5173
) else (
    timeout /t 3 /nobreak >nul
    start http://localhost:8000/docs
)

echo.
echo ============================================
echo   Done! Close this window to keep running.
echo ============================================
pause
