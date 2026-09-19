@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM BrandAnalysis: Unified Windows Startup Script
REM Starts the Streamlit Dashboard or forwards commands to the CLI.
REM ==============================================================================

cd /d "%~dp0"

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ============================================================
echo    BrandAnalysis: Personal Branding ^& Micro-SaaS AI
echo ============================================================

REM Detect Python
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_EXEC=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PYTHON_EXEC=py
    ) else (
        echo [ERROR] Python is not installed or not found in PATH.
        exit /b 1
    )
)

REM Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment .venv...
    call ".venv\Scripts\activate.bat"
)
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment venv...
    call "venv\Scripts\activate.bat"
)

echo [OK] Using Python:
%PYTHON_EXEC% --version

REM Check essential dependencies
%PYTHON_EXEC% -c "import streamlit, rich, pydantic, dotenv" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required dependencies from requirements.txt...
    %PYTHON_EXEC% -m pip install -r requirements.txt
)

REM Check Ollama connectivity
curl -s -f -m 2 http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Ollama is running on http://localhost:11434
) else (
    echo [WARNING] Ollama is not detected at http://localhost:11434.
    echo Ensure Ollama is started with ollama serve for AI analysis.
)

echo ------------------------------------------------------------

if "%~1"=="" (
    echo [START] Launching BrandAnalysis Streamlit Dashboard...
    echo [URL] Opening at http://localhost:8501
    %PYTHON_EXEC% -m streamlit run app.py
) else (
    echo [START] Forwarding arguments to CLI...
    %PYTHON_EXEC% cli.py %*
)
