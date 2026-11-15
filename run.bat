@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM BrandAnalysis : Unified Windows Startup Script
REM Manages dependencies and launches FastAPI (:8000) & Next.js (:3000)
REM Also supports CLI, Streamlit, and tests via arguments.
REM ==============================================================================

cd /d "%~dp0"

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo    ⚡ BrandAnalysis AI: Autonomous Intelligence & Automations
echo ============================================================

REM ------------------------------------------------------------------------------
REM 1. Detect Python Interpreter
REM ------------------------------------------------------------------------------
set PYTHON_EXEC=

REM Check virtual environments first
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXEC=.venv\Scripts\python.exe
    echo [INFO] Found virtual environment at .venv
    call ".venv\Scripts\activate.bat" >nul 2>&1
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXEC=venv\Scripts\python.exe
    echo [INFO] Found virtual environment at venv
    call "venv\Scripts\activate.bat" >nul 2>&1
)

if "%PYTHON_EXEC%"=="" (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PYTHON_EXEC=python
    ) else (
        where py >nul 2>&1
        if %ERRORLEVEL% equ 0 (
            set PYTHON_EXEC=py
        ) else (
            echo [ERROR] Python is not installed or not found in PATH.
            echo Please install Python 3.10+ and add it to your PATH.
            exit /b 1
        )
    )
)

echo [OK] Using Python:
%PYTHON_EXEC% --version

REM ------------------------------------------------------------------------------
REM 2. Check and Install Python Dependencies
REM ------------------------------------------------------------------------------
echo [INFO] Checking Python dependencies...
%PYTHON_EXEC% -c "import fastapi, uvicorn, pydantic, requests, bs4, rich, dotenv" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Missing Python dependencies. Installing from requirements.txt...
    %PYTHON_EXEC% -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Pip install returned a non-zero code. Attempting to proceed...
    )
) else (
    echo [OK] Python dependencies verified.
)

REM Verify Playwright browser availability
%PYTHON_EXEC% -c "import playwright; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Playwright Chromium browser not detected. Installing...
    %PYTHON_EXEC% -m playwright install chromium
)

REM ------------------------------------------------------------------------------
REM 3. Check Node.js and Frontend Dependencies
REM ------------------------------------------------------------------------------
echo [INFO] Checking Node.js environment...
set NODE_AVAILABLE=0
where node >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set NODE_AVAILABLE=1
    echo [OK] Node.js is installed:
    node -v
) else (
    echo [WARNING] Node.js is not installed or not in PATH.
    echo Next.js modern UI requires Node.js (v18+ recommended).
)

if %NODE_AVAILABLE% equ 1 (
    if not exist "frontend\node_modules" (
        echo [INFO] Frontend dependencies not found in frontend\node_modules.
        echo [INFO] Installing frontend packages with npm...
        pushd frontend
        call npm install
        popd
        echo [OK] Frontend packages installed.
    ) else (
        echo [OK] Frontend packages verified.
    )
)

REM ------------------------------------------------------------------------------
REM 4. Check Ollama Connectivity
REM ------------------------------------------------------------------------------
echo [INFO] Checking Ollama connectivity...
curl -s -f -m 2 http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Ollama is active on http://localhost:11434
) else (
    echo [NOTE] Ollama is not detected at http://localhost:11434.
    echo        If using local AI models, run 'ollama serve' in another window.
)

echo ------------------------------------------------------------

REM ------------------------------------------------------------------------------
REM 5. Command Routing & Execution
REM ------------------------------------------------------------------------------
if /i "%~1"=="streamlit" (
    echo [START] Launching Streamlit Studio at http://localhost:8501...
    %PYTHON_EXEC% -m streamlit run app.py
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="legacy" (
    echo [START] Launching Streamlit Studio at http://localhost:8501...
    %PYTHON_EXEC% -m streamlit run app.py
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="backend" (
    echo [START] Launching FastAPI Backend on http://localhost:8000...
    %PYTHON_EXEC% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="frontend" (
    if %NODE_AVAILABLE% equ 0 (
        echo [ERROR] Node.js is required to start frontend.
        exit /b 1
    )
    echo [START] Launching Next.js UI on http://localhost:3000...
    cd /d "%~dp0frontend"
    npm run dev
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="test" (
    echo [START] Running Pytest test suite...
    %PYTHON_EXEC% -m pytest tests/ -v
    exit /b %ERRORLEVEL%
)

if /i "%~1"=="cli" (
    shift
    echo [START] Forwarding arguments to CLI...
    %PYTHON_EXEC% cli.py %*
    exit /b %ERRORLEVEL%
)

if not "%~1"=="" (
    echo [START] Passing arguments to BrandAnalysis CLI...
    %PYTHON_EXEC% cli.py %*
    exit /b %ERRORLEVEL%
)

REM Default: Launch Unified Stack (FastAPI Backend + Next.js UI)
echo ============================================================
echo   🚀 Launching Unified BrandAnalysis Stack
echo ============================================================
echo.
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "BrandAnalysis - FastAPI Backend (:8000)" cmd /k "cd /d "%~dp0" && %PYTHON_EXEC% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

if %NODE_AVAILABLE% equ 1 (
    echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
    start "BrandAnalysis - Next.js UI (:3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"
) else (
    echo [2/2] Skipping frontend start (Node.js not installed).
)

echo.
echo ============================================================
echo   ⚡ BrandAnalysis AI Platform is LIVE!
echo ============================================================
echo   🌐 Web UI (Next.js):     http://localhost:3000
echo   ⚡ Backend API (FastAPI): http://localhost:8000
echo   📖 API Docs (Swagger):   http://localhost:8000/docs
echo   📊 Streamlit Studio:     run.bat streamlit
echo ============================================================
echo Both servers are running in separate titled console windows.
echo Close their respective windows or press Ctrl+C in them to stop.
echo.
pause
