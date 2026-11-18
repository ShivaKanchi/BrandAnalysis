import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure root workspace is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.api.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BrandAnalysis.Server")

app = FastAPI(
    title="BrandAnalysis Lead Generation & Intelligence API",
    description="High-intent lead harvesting, local prospecting, store lead farming, and client acquisition.",
    version="1.0.0",
)

# Enable CORS for Next.js frontend (port 3000) and all client origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "BrandAnalysis AI Workflow Engine API is running",
        "docs_url": "/docs",
        "endpoints": {
            "workflows": "/api/workflows",
            "stream_run": "/api/workflows/{workflow_id}/run",
            "leads": "/api/leads",
            "influencer_discovery": "/api/influencers/discover",
            "export_csv": "/api/leads/export/csv",
            "settings": "/api/settings",
            "health": "/api/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting BrandAnalysis FastAPI server on http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
