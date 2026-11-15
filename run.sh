#!/usr/bin/env bash

# ==============================================================================
# BrandAnalysis: Unified POSIX Startup Script
# Manages dependencies and launches FastAPI (:8000) & Next.js (:3000)
# Also supports CLI, Streamlit, and tests via arguments.
# ==============================================================================

set -e

# Force UTF-8 encoding for Python output across all terminals
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# Resolve project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "   ⚡ BrandAnalysis AI: Autonomous Intelligence & Automations"
echo "============================================================"

# ------------------------------------------------------------------------------
# 1. Detect Python Interpreter & Virtual Environment
# ------------------------------------------------------------------------------
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

if command -v python3 &>/dev/null; then
    PYTHON_EXEC="python3"
elif command -v python &>/dev/null; then
    PYTHON_EXEC="python"
elif command -v py &>/dev/null; then
    PYTHON_EXEC="py"
else
    echo "❌ Error: Python is not installed or not in PATH."
    exit 1
fi

echo "✅ Using Python: $($PYTHON_EXEC --version 2>&1)"

# ------------------------------------------------------------------------------
# 2. Check and Install Python Dependencies
# ------------------------------------------------------------------------------
echo "🔹 Checking Python dependencies..."
if ! $PYTHON_EXEC -c "import fastapi, uvicorn, pydantic, requests, bs4, rich, dotenv" 2>/dev/null; then
    echo "📦 Missing required Python packages. Installing from requirements.txt..."
    $PYTHON_EXEC -m pip install -r requirements.txt || echo "⚠️ Pip install warning, continuing..."
else
    echo "✅ Python dependencies verified."
fi

# Ensure Playwright browser is available
if ! $PYTHON_EXEC -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null; then
    echo "🌐 Playwright Chromium not found. Installing..."
    $PYTHON_EXEC -m playwright install chromium || true
fi

# ------------------------------------------------------------------------------
# 3. Check Node.js and Frontend Dependencies
# ------------------------------------------------------------------------------
echo "🔹 Checking Node.js environment..."
NODE_AVAILABLE=0
if command -v node &>/dev/null; then
    NODE_AVAILABLE=1
    echo "✅ Node.js is installed: $(node -v)"
    
    if [ ! -d "frontend/node_modules" ]; then
        echo "📦 Installing frontend dependencies in frontend/..."
        (cd frontend && npm install)
        echo "✅ Frontend dependencies installed."
    else
        echo "✅ Frontend packages verified."
    fi
else
    echo "⚠️ Node.js is not installed. Next.js web UI requires Node.js (v18+ recommended)."
fi

# ------------------------------------------------------------------------------
# 4. Check Ollama Connectivity
# ------------------------------------------------------------------------------
echo "🔍 Checking Ollama connectivity..."
if curl -s -f -m 2 http://localhost:11434/api/tags &>/dev/null; then
    echo "🟢 Ollama is running on http://localhost:11434"
else
    echo "⚠️  Ollama does not appear to be running on http://localhost:11434."
    echo "   Ensure Ollama is started ('ollama serve') for local AI workflows."
fi

echo "------------------------------------------------------------"

# ------------------------------------------------------------------------------
# 5. Command Routing & Execution
# ------------------------------------------------------------------------------
MODE="${1:-}"

if [ "$MODE" = "streamlit" ] || [ "$MODE" = "legacy" ]; then
    echo "🚀 Starting Streamlit Studio at http://localhost:8501..."
    exec $PYTHON_EXEC -m streamlit run app.py
fi

if [ "$MODE" = "backend" ]; then
    echo "🚀 Starting FastAPI Backend on http://localhost:8000..."
    exec $PYTHON_EXEC -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi

if [ "$MODE" = "frontend" ]; then
    if [ "$NODE_AVAILABLE" -eq 0 ]; then
        echo "❌ Node.js is required to start the frontend."
        exit 1
    fi
    echo "🚀 Starting Next.js Frontend on http://localhost:3000..."
    cd frontend && exec npm run dev
fi

if [ "$MODE" = "test" ]; then
    echo "🧪 Running Pytest test suite..."
    exec $PYTHON_EXEC -m pytest tests/ -v
fi

if [ "$MODE" = "cli" ]; then
    shift
    echo "🚀 Running CLI with arguments: $@"
    exec $PYTHON_EXEC cli.py "$@"
fi

if [ -n "$MODE" ]; then
    echo "🚀 Passing arguments to BrandAnalysis CLI: $@"
    exec $PYTHON_EXEC cli.py "$@"
fi

# Default: Unified Stack Execution
echo "============================================================"
echo "   🚀 Launching Unified BrandAnalysis Stack"
echo "============================================================"

# Background FastAPI server and track PID
echo "🔹 [1/2] Starting FastAPI Backend on http://localhost:8000 ..."
$PYTHON_EXEC -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cleanup() {
    echo ""
    echo "🛑 Shutting down backend (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
    echo "👋 Shutdown complete."
}
trap cleanup EXIT INT TERM

sleep 2

echo "============================================================"
echo "   ⚡ BrandAnalysis AI Platform is LIVE!"
echo "============================================================"
echo "   🌐 Web UI (Next.js):     http://localhost:3000"
echo "   ⚡ Backend API (FastAPI): http://localhost:8000"
echo "   📖 API Docs (Swagger):   http://localhost:8000/docs"
echo "   📊 Streamlit Studio:     ./run.sh streamlit"
echo "============================================================"

if [ "$NODE_AVAILABLE" -eq 1 ]; then
    echo "🔹 [2/2] Starting Next.js Frontend on http://localhost:3000 ..."
    (cd frontend && npm run dev)
else
    echo "⚠️ Skipping frontend (Node.js not installed). Backend running in foreground..."
    wait $BACKEND_PID
fi
