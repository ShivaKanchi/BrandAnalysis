import pytest
import json
import csv
import io
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.main import app
from backend.workflows import WORKFLOW_REGISTRY, get_workflow
from backend.workflows.base_workflow import BaseWorkflow
from backend.workflows.shopify_revamp_workflow import ShopifyRevampWorkflow
from backend.storage import StorageManager


client = TestClient(app)


# ==============================================================================
# 1. Workflow DAG Structure Validation Tests
# ==============================================================================

def test_workflow_registry_and_initialization():
    """Verify all 5 core workflows are registered and instantiate valid BaseWorkflow graphs."""
    expected_workflows = [
        "shopify_revamp",
        "lead_harvester",
        "brand_audit",
        "competitor_matrix",
        "problem_radar",
    ]

    for wid in expected_workflows:
        assert wid in WORKFLOW_REGISTRY, f"Workflow '{wid}' missing from WORKFLOW_REGISTRY"
        wf = get_workflow(wid)
        assert isinstance(wf, BaseWorkflow)
        graph = wf.get_graph()

        # Check React Flow Graph Schema
        assert "id" in graph
        assert "name" in graph
        assert "nodes" in graph
        assert "edges" in graph
        assert isinstance(graph["nodes"], list)
        assert isinstance(graph["edges"], list)
        assert len(graph["nodes"]) > 0, f"Workflow '{wid}' has no nodes defined"
        assert len(graph["edges"]) > 0, f"Workflow '{wid}' has no edges defined"

        # Validate React Flow Node Properties
        for node in graph["nodes"]:
            assert "id" in node
            assert "type" in node
            assert "position" in node
            assert "x" in node["position"] and "y" in node["position"]
            assert "data" in node
            data = node["data"]
            assert "label" in data
            assert data["status"] == "idle"
            assert "logs" in data
            assert "output" in data

        # Validate React Flow Edge Properties
        for edge in graph["edges"]:
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert any(n["id"] == edge["source"] for n in graph["nodes"]), f"Edge source '{edge['source']}' not found in nodes"
            assert any(n["id"] == edge["target"] for n in graph["nodes"]), f"Edge target '{edge['target']}' not found in nodes"


def test_shopify_revamp_dag_architecture():
    """Verify Shopify Revamp Harvester DAG node composition and edge connectivity."""
    wf = ShopifyRevampWorkflow()
    graph = wf.get_graph()
    node_ids = [n["id"] for n in graph["nodes"]]

    expected_nodes = [
        "node_input",
        "node_shopify_check",
        "node_social_reach",
        "node_lighthouse",
        "node_console_errors",
        "node_vision_ux",
        "node_qualification",
        "node_pitch_generation",
        "node_save_lead",
    ]

    for expected_id in expected_nodes:
        assert expected_id in node_ids, f"Expected node '{expected_id}' not found in Shopify Revamp DAG"

    # Verify key convergence and sequential edges
    edge_tuples = [(e["source"], e["target"]) for e in graph["edges"]]
    assert ("node_input", "node_shopify_check") in edge_tuples
    assert ("node_shopify_check", "node_social_reach") in edge_tuples
    assert ("node_social_reach", "node_lighthouse") in edge_tuples
    assert ("node_social_reach", "node_console_errors") in edge_tuples
    assert ("node_social_reach", "node_vision_ux") in edge_tuples
    assert ("node_lighthouse", "node_qualification") in edge_tuples
    assert ("node_console_errors", "node_qualification") in edge_tuples
    assert ("node_vision_ux", "node_qualification") in edge_tuples
    assert ("node_qualification", "node_pitch_generation") in edge_tuples
    assert ("node_pitch_generation", "node_save_lead") in edge_tuples


# ==============================================================================
# 2. Server-Sent Events (SSE) Emission Tests
# ==============================================================================

def test_workflow_sse_event_emission():
    """Verify that stream_events generates valid SSE event streams and JSON payloads."""
    import asyncio
    async def _run():
        test_wf = BaseWorkflow(id="test_stream", name="Test Stream", description="Test")

        async def step1(context, log):
            await log("Step 1 executing...", "info")
            return {"step1_result": "ok"}

        async def step2(context, log):
            await log("Step 2 executing...", "info")
            return {"step2_result": "done"}

        test_wf.add_node("s1", "Step 1", handler=step1)
        test_wf.add_node("s2", "Step 2", handler=step2)
        test_wf.add_edge("s1", "s2")

        events = []
        async for raw_sse in test_wf.stream_events(context={"param": "value"}):
            assert raw_sse.startswith("data: ")
            assert raw_sse.endswith("\n\n")
            json_payload = raw_sse[len("data: ") : -2].strip()
            parsed = json.loads(json_payload)
            events.append(parsed)
        return events

    events = asyncio.run(_run())

    event_types = [e.get("event") for e in events]
    assert "workflow_start" in event_types
    assert "node_start" in event_types
    assert "node_log" in event_types
    assert "node_complete" in event_types
    assert "workflow_complete" in event_types

    # Verify workflow_complete telemetry
    wf_complete = next(e for e in events if e.get("event") == "workflow_complete")
    assert wf_complete["status"] == "completed"
    assert wf_complete["summary"]["nodes_completed"] == 2


# ==============================================================================
# 3. FastAPI Endpoints & Workflows API Tests
# ==============================================================================

def test_api_health_and_root():
    """Test health check and root landing endpoints."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "BrandAnalysis" in resp_root.json()["message"]

    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    health_data = resp_health.json()
    assert health_data["status"] == "healthy"
    assert "shopify_revamp" in health_data["active_workflows"]


def test_api_workflows_listing_and_retrieval():
    """Test GET /api/workflows and GET /api/workflows/{id} endpoints."""
    resp = client.get("/api/workflows")
    assert resp.status_code == 200
    workflows = resp.json()
    assert isinstance(workflows, list)
    assert len(workflows) >= 5

    # Retrieve shopify_revamp DAG
    resp_single = client.get("/api/workflows/shopify_revamp")
    assert resp_single.status_code == 200
    single = resp_single.json()
    assert single["id"] == "shopify_revamp"
    assert len(single["nodes"]) == 9

    # Test 404 for unknown workflow
    resp_404 = client.get("/api/workflows/non_existent_wf")
    assert resp_404.status_code == 404


def test_api_settings_crud():
    """Test GET and POST /api/settings for qualification thresholds."""
    # Get current settings
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    settings = resp.json()
    assert "min_followers" in settings
    assert "max_lighthouse_score" in settings
    assert "min_console_errors" in settings

    # Update settings
    update_payload = {
        "min_followers": 3000,
        "max_lighthouse_score": 55,
        "min_console_errors": 2,
    }
    resp_post = client.post("/api/settings", json=update_payload)
    assert resp_post.status_code == 200
    updated = resp_post.json()
    assert updated["min_followers"] == 3000
    assert updated["max_lighthouse_score"] == 55
    assert updated["min_console_errors"] == 2

    # Reset back to default
    client.post("/api/settings", json={"min_followers": 2500, "max_lighthouse_score": 60, "min_console_errors": 1})


# ==============================================================================
# 4. Leads Management & CSV Export Endpoint Tests
# ==============================================================================

def test_api_leads_crud_and_csv_export():
    """
    Test full lead lifecycle:
    1. POST /api/leads (create lead)
    2. GET /api/leads (verify in list)
    3. GET /api/leads/{id} (verify detail)
    4. GET /api/leads/export/csv (verify CSV structure & field mapping)
    5. DELETE /api/leads/{id} (cleanup)
    """
    test_lead = {
        "id": "test_verification_store_123",
        "domain": "verificationteststore.com",
        "store_name": "Verification Store",
        "platform": "shopify",
        "is_shopify": True,
        "followers": 12500,
        "engagement_rate": 3.8,
        "lighthouse_performance": 45.0,
        "lighthouse_seo": 88.0,
        "lighthouse_accessibility": 92.0,
        "console_errors_count": 3,
        "vision_score": 58,
        "qualified_for_revamp": True,
        "status": "Qualified",
        "pitch_email": "Hi Team, noticed 3 console errors causing friction on verificationteststore.com...",
        "pitch_dm": "Quick heads up on verificationteststore.com mobile speed!",
    }

    # 1. Create lead
    resp_create = client.post("/api/leads", json=test_lead)
    assert resp_create.status_code == 200
    created_data = resp_create.json()
    assert created_data["id"] == "test_verification_store_123"

    # 2. Retrieve in list with filter
    resp_list = client.get("/api/leads?query=verificationteststore")
    assert resp_list.status_code == 200
    leads = resp_list.json()
    assert len(leads) >= 1
    assert any(l["id"] == "test_verification_store_123" for l in leads)

    # 3. Retrieve detail
    resp_detail = client.get("/api/leads/test_verification_store_123")
    assert resp_detail.status_code == 200
    assert resp_detail.json()["domain"] == "verificationteststore.com"

    # 4. Test CSV Export Format and Field Mapping
    resp_csv = client.get("/api/leads/export/csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers.get("content-type", "")
    assert 'filename="shopify_revamp_leads.csv"' in resp_csv.headers.get("content-disposition", "")

    csv_text = resp_csv.text
    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = reader.fieldnames

    # Check required field columns
    required_cols = [
        "id",
        "domain",
        "store_name",
        "platform",
        "is_shopify",
        "followers",
        "engagement_rate",
        "lighthouse_performance",
        "lighthouse_seo",
        "lighthouse_accessibility",
        "console_errors_count",
        "vision_score",
        "qualified_for_revamp",
        "status",
        "pitch_email",
        "pitch_dm",
        "created_at",
    ]
    for col in required_cols:
        assert col in fieldnames, f"Column '{col}' missing from CSV export"

    # Verify our created lead is present and correctly mapped
    rows = list(reader)
    matched_row = next((r for r in rows if r["id"] == "test_verification_store_123"), None)
    assert matched_row is not None, "Created lead not found in CSV output rows"
    assert matched_row["domain"] == "verificationteststore.com"
    assert matched_row["store_name"] == "Verification Store"
    assert matched_row["platform"] == "shopify"
    assert matched_row["is_shopify"] in ("True", "true")
    assert matched_row["followers"] == "12500"
    assert matched_row["lighthouse_performance"] in ("45.0", "45")
    assert matched_row["console_errors_count"] == "3"
    assert matched_row["qualified_for_revamp"] in ("True", "true")
    assert matched_row["status"] == "Qualified"

    # 5. Cleanup
    resp_del = client.delete("/api/leads/test_verification_store_123")
    assert resp_del.status_code == 200
    assert resp_del.json()["deleted"] is True


def test_api_legacy_reports():
    """Verify that legacy reports index endpoint /api/reports responds cleanly."""
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
