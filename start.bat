@echo off
setlocal enabledelayedexpansion
title Maphiver

set "ROOT=%~dp0"

echo.
echo =================================================
echo   Maphiver v0.2.6
echo =================================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1 || (echo [ERROR] Python not found, please install Python 3.10+ && pause && exit /b 1)

echo [2/4] Checking Node.js...
where node >nul 2>&1 || (echo [ERROR] Node.js not found && pause && exit /b 1)

if not exist "%ROOT%backend\.env" (
    echo [INFO] Creating backend\.env from .env.example ...
    copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
    echo [INFO] Edit backend\.env and set DEEPSEEK_API_KEY, then restart.
    pause
)

echo [3/4] Installing dependencies...
echo        pip install ...
python -m pip install -r "%ROOT%backend\requirements.txt" -q
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip install failed, check network/requirements.
    pause
    exit /b 1
)
if not exist "%ROOT%frontend\node_modules" (
    echo        npm install ...
    cd /d "%ROOT%frontend"
    call npm install
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    cd /d "%ROOT%"
)

echo [4/4] Starting services...
echo.

echo [*] Checking port 8742...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8742" ^| findstr /i "LISTENING 监听"') do (
    echo        Releasing port 8742 (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [*] Starting Backend on http://localhost:8742
start "Maphiver-Backend" cmd /k "cd /d %ROOT%backend && python -m uvicorn main:app --reload --port 8742"

echo [*] Waiting for Backend...
set "READY="
for /l %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    curl -sf http://localhost:8742/api/health >nul 2>&1
    if not errorlevel 1 set "READY=1" & goto :start_frontend
)
:start_frontend
if defined READY (echo        Backend is ready.) else echo [WARN] Backend not responding, continuing...

echo.
echo [*] Starting Frontend on http://localhost:4173
start "Maphiver-Frontend" cmd /k "cd /d %ROOT%frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo [*] Opening browser...
start "" http://localhost:4173

echo.
echo =================================================
echo   Backend : http://localhost:8742
echo   Frontend: http://localhost:4173
echo =================================================
echo.
echo Close this window to keep services running.
pause >nul
