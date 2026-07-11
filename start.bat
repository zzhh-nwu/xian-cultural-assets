@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   西安文化数字资产平台
echo   本地启动中...
echo ============================================
echo.

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 没有找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo [√] Python 已就绪

:: Check Node
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 没有找到 Node.js，将跳过前端启动
    set NO_FRONTEND=1
) else (
    echo [√] Node.js 已就绪
)

echo.
echo [1] 启动后端 API 服务 (端口 8000)...
start "西安文化-后端API" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo     后端窗口已打开

if not defined NO_FRONTEND (
    echo [2] 启动前端服务 (端口 5173)...
    start "西安文化-前端Web" cmd /k "cd /d "%~dp0frontend" && npm run dev"
    echo     前端窗口已打开
    echo.
    echo 等待前端启动...
    timeout /t 6 /nobreak >nul
    start http://localhost:5173
    echo.
    echo ============================================
    echo   浏览器将打开: http://localhost:5173
    echo   线上地址: https://xian-cultural-assets.onrender.com
    echo   关闭此窗口不影响服务运行
    echo ============================================
) else (
    echo.
    timeout /t 3 /nobreak >nul
    start http://localhost:8000/docs
    echo ============================================
    echo   浏览器将打开: http://localhost:8000/docs
    echo ============================================
)

pause
