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
    seen = set()
    for wid in WORKFLOW_REGISTRY.keys():
        clean_id = wid.replace("-", "_")
        if clean_id in seen:
            continue
        seen.add(clean_id)
        try:
            wf = get_workflow(clean_id)
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
    audience_bands: Optional[str] = Query(None, description="Comma-separated audience bands, e.g. 10-13,13-17"),
    fresh_only: Optional[bool] = Query(None, description="Exclude influencers returned by earlier runs"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Maximum workflow results"),
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
        "audience_bands": audience_bands,
        "fresh_only": fresh_only,
        "limit": limit,
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
# Influencer Discovery & Review Queue
# ---------------------------------------------------------------------------

@router.get("/influencers/discover")
@router.post("/influencers/discover")
def discover_influencers(
    niches: Optional[str] = Query(None, description="Optional comma-separated campaign niches; omit for the full catalogue"),
    audience_bands: str = Query("10-13,13-17,16-22", description="Comma-separated target age bands"),
    country: Optional[str] = Query(None, description="Optional creator country, e.g. India"),
    min_followers: Optional[int] = Query(None, ge=0, description="Optional minimum public follower count"),
    max_followers: Optional[int] = Query(None, ge=0, description="Optional maximum public follower count"),
    limit: int = Query(100, ge=1, le=500),
    fresh_only: bool = Query(False, description="Exclude influencers returned by prior runs"),
):
    """Builds a deduplicated, review-ready influencer shortlist from the configurable catalogue."""
    from core.influencer_discovery import InfluencerDiscovery
    try:
        discovery = InfluencerDiscovery()
        result = discovery.discover(
            niches=[item.strip() for item in niches.split(",") if item.strip()] if niches else None,
            audience_bands=[item.strip() for item in audience_bands.split(",") if item.strip()],
            country=country,
            min_followers=min_followers,
            max_followers=max_followers,
            limit=limit,
            fresh_only=fresh_only,
        )
        country_slug = (country or "all").strip().lower().replace(" ", "_")
        follower_suffix = f"_{min_followers or 0}_{max_followers or 'plus'}" if min_followers is not None or max_followers is not None else ""
        csv_path = discovery.write_shortlist_csv(result["influencers"], f"influencer_shortlist_{country_slug}{follower_suffix}")
        result["csv_path"] = str(csv_path)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/influencers/export/csv")
def export_influencers_csv():
    """Exports the persistent influencer review queue as a spreadsheet-friendly CSV."""
    from core.influencer_discovery import InfluencerDiscovery
    return Response(
        content=InfluencerDiscovery().export_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="influencer_review_queue.csv"'},
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
# Direct Lead Harvesting Endpoint (Powers Next.js & UI Prospectors)
# ---------------------------------------------------------------------------

@router.get("/harvest")
@router.post("/harvest")
async def harvest_leads(
    niche: str = Query("Gyms", description="Business category or vertical"),
    location: str = Query("Austin, TX", description="City, locality, or postal code"),
    limit: int = Query(6, ge=1, le=30, description="Max fresh leads to discover"),
    fresh_only: bool = Query(True, description="Filter out previously harvested leads"),
    auto_expand: bool = Query(True, description="Rotate sub-neighborhoods if top results are saturated"),
):
    """
    Harvests fresh, high-intent business leads.
    Automatically de-duplicates against the persistent registry and guarantees new leads on every call.
    """
    try:
        from core.auto_prospector import AutoProspector
        prospector = AutoProspector(headless=True)
        report = prospector.discover_leads(
            niche_or_query=niche,
            location=location,
            limit=limit,
            exclude_previously_seen=fresh_only,
            auto_expand=auto_expand,
        )
        leads_list = [lead.model_dump() for lead in report.leads]
        return {
            "success": True,
            "target_query": report.search_query,
            "locality": report.target_locality,
            "total_places_scanned": report.total_places_scanned,
            "fresh_leads_count": report.fresh_leads_count,
            "recycled_leads_skipped": report.recycled_leads_skipped,
            "high_intent_count": report.high_intent_count,
            "total_registry_leads": report.total_registry_leads,
            "leads": leads_list,
        }
    except Exception as e:
        logger.error(f"Error harvesting leads: {e}")
        return {
            "success": False,
            "error": str(e),
            "leads": [],
            "fresh_leads_count": 0,
        }


# ---------------------------------------------------------------------------
# Ollama AI Connectivity & Model Discovery
# ---------------------------------------------------------------------------

@router.get("/ollama/status")
def get_ollama_status():
    """Returns local Ollama health status, available models, and setup recommendations."""
    try:
        from core.ollama_helper import OllamaManager
        return OllamaManager.check_status()
    except Exception as e:
        return {
            "online": False,
            "error": str(e),
            "status_message": "Could not check Ollama status."
        }


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
        "service": "BrandAnalysis Lead Generation Engine",
        "version": "1.0.0",
        "active_workflows": list(WORKFLOW_REGISTRY.keys()),
    }
