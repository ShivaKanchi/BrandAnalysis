#!/usr/bin/env bash

# ==============================================================================
# BrandAnalysis: Unified Startup Script
# Starts the Streamlit Dashboard or forwards commands to the CLI.
# ==============================================================================

set -e

# Force UTF-8 encoding for Python output across all terminals
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# Resolve project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "   ⚡ BrandAnalysis: Personal Branding & Micro-SaaS AI"
echo "============================================================"

# Detect Python interpreter
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
elif command -v py &>/dev/null; then
    PYTHON_CMD="py"
else
    echo "❌ Error: Python is not installed or not in PATH."
    exit 1
fi

# Detect and activate virtual environment if present
if [ -d ".venv" ]; then
    if [ -f ".venv/bin/activate" ]; then
        echo "🔹 Activating virtual environment (.venv)..."
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        echo "🔹 Activating virtual environment (.venv/Scripts)..."
        source .venv/Scripts/activate
    fi
elif [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        echo "🔹 Activating virtual environment (venv)..."
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        echo "🔹 Activating virtual environment (venv/Scripts)..."
        source venv/Scripts/activate
    fi
fi

# Re-evaluate Python command inside environment
if command -v python &>/dev/null; then
    PYTHON_EXEC="python"
else
    PYTHON_EXEC="$PYTHON_CMD"
fi

echo "✅ Using Python: $($PYTHON_EXEC --version 2>&1)"

# Check if essential requirements are installed
if ! $PYTHON_EXEC -c "import streamlit, rich, pydantic, dotenv" 2>/dev/null; then
    echo "📦 Missing required dependencies. Installing from requirements.txt..."
    $PYTHON_EXEC -m pip install -r requirements.txt
fi

# Ensure Playwright browser is available
if ! $PYTHON_EXEC -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null; then
    echo "🌐 Playwright Chromium not found. Installing..."
    $PYTHON_EXEC -m playwright install chromium
fi

# Check Ollama connectivity
echo "🔍 Checking Ollama connectivity..."
if curl -s -f -m 2 http://localhost:11434/api/tags &>/dev/null; then
    echo "🟢 Ollama is running on http://localhost:11434"
else
    echo "⚠️  WARNING: Ollama does not appear to be running on http://localhost:11434."
    echo "   Ensure Ollama is started ('ollama serve' or start Ollama app) for AI analysis."
fi

echo "------------------------------------------------------------"

# If arguments were provided, pass them to CLI; otherwise launch Streamlit Dashboard
if [ "$#" -gt 0 ]; then
    echo "🚀 Running CLI with arguments: $@"
    $PYTHON_EXEC cli.py "$@"
else
    echo "🚀 Starting BrandAnalysis Streamlit Dashboard..."
    echo "🌐 Dashboard will be accessible at: http://localhost:8501"
    $PYTHON_EXEC -m streamlit run app.py
fi
