import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from backend.workflows import WORKFLOW_REGISTRY, get_workflow
from backend.storage import StorageManager

logger = logging.getLogger("BrandAnalysis.API")

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Workflows & Visual DAG Graph Endpoints
# ---------------------------------------------------------------------------

@router.get("/workflows")
def list_workflows():
    """Returns list of all available automation workflows with their initial React Flow DAG graph."""
    graphs = []
    for wid in WORKFLOW_REGISTRY.keys():
        try:
            wf = get_workflow(wid)
            graphs.append(wf.get_graph())
        except Exception as e:
            logger.error(f"Error loading workflow {wid}: {e}")
    return graphs


@router.get("/workflows/{workflow_id}")
def get_workflow_by_id(workflow_id: str):
    """Returns the visual DAG node & edge structure for a single automation."""
    try:
        wf = get_workflow(workflow_id)
        return wf.get_graph()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/workflows/{workflow_id}/run")
async def run_workflow_stream(
    workflow_id: str,
    url: Optional[str] = Query(None, description="Target Shopify or webstore URL"),
    query: Optional[str] = Query(None, description="Search query or brand name"),
    niche: Optional[str] = Query(None, description="E-commerce or business vertical"),
    location: Optional[str] = Query(None, description="City / locality for Maps harvester"),
    username: Optional[str] = Query(None, description="Social handle for Brand Audit"),
    target: Optional[str] = Query(None, description="Target for Competitor Matrix"),
    min_followers: Optional[int] = Query(None, description="Minimum social followers threshold"),
    max_lighthouse_score: Optional[float] = Query(None, description="Maximum speed threshold to qualify"),
    min_console_errors: Optional[int] = Query(None, description="Minimum JavaScript errors required"),
):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Runs the selected workflow DAG in real-time, yielding node status, execution logs,
    and output artifacts for interactive React Flow visualization.
    """
    try:
        wf = get_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    context: Dict[str, Any] = {
        "url": url,
        "query": query,
        "niche": niche,
        "location": location,
        "username": username,
        "target": target,
        "min_followers": min_followers,
        "max_lighthouse_score": max_lighthouse_score,
        "min_console_errors": min_console_errors,
    }
    # Filter out None values
    context = {k: v for k, v in context.items() if v is not None}

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
    }

    return StreamingResponse(
        wf.stream_events(context),
        media_type="text/event-stream",
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Leads Management & Export Endpoints
# ---------------------------------------------------------------------------

@router.get("/leads")
def get_leads(
    status: Optional[str] = Query(None, description="Filter by status: Qualified, Pending, Rejected, Non-Shopify"),
    query: Optional[str] = Query(None, description="Search query matching domain, name, or niche"),
):
    """Returns stored Shopify revamp leads matching optional status and query filters."""
    return StorageManager.get_leads(status=status, query=query)


@router.post("/leads")
def create_or_update_lead(lead: Dict[str, Any]):
    """Saves or updates a lead record in the persistent index."""
    if not lead:
        raise HTTPException(status_code=400, detail="Empty lead payload")
    saved = StorageManager.upsert_lead(lead)
    return saved


@router.get("/leads/{lead_id}")
def get_lead_detail(lead_id: str):
    """Retrieves full audit metrics and pitch kit for a specific lead."""
    lead = StorageManager.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return lead


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: str):
    """Removes a lead record from storage."""
    success = StorageManager.delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return {"deleted": True, "lead_id": lead_id}


@router.get("/leads/export/csv")
def export_leads_csv():
    """Generates and downloads a clean CSV file containing all audited Shopify revamp leads."""
    csv_data = StorageManager.export_leads_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="shopify_revamp_leads.csv"',
            "Content-Type": "text/csv; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ---------------------------------------------------------------------------
# Application Settings & Thresholds Endpoints
# ---------------------------------------------------------------------------

@router.get("/settings")
def get_settings():
    """Retrieves current audit thresholds and AI model configurations."""
    return StorageManager.get_settings()


@router.post("/settings")
def update_settings(payload: Dict[str, Any]):
    """Updates global audit thresholds (followers, speed, errors) and credentials."""
    updated = StorageManager.update_settings(payload)
    return updated


# ---------------------------------------------------------------------------
# Saved Reports & Health Check
# ---------------------------------------------------------------------------

@router.get("/reports")
def get_saved_reports():
    """Retrieves list of saved BrandAnalysis intelligence reports."""
    return StorageManager.get_legacy_reports_index()


@router.get("/health")
def health_check():
    """Service health probe."""
    return {
        "status": "healthy",
        "service": "BrandAnalysis Workflow Engine",
        "version": "2.0.0",
        "active_workflows": list(WORKFLOW_REGISTRY.keys()),
    }
