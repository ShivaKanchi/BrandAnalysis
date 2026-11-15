from .base_workflow import BaseWorkflow
from .shopify_revamp_workflow import ShopifyRevampWorkflow
from .lead_harvester_workflow import LeadHarvesterWorkflow
from .brand_audit_workflow import BrandAuditWorkflow
from .competitor_matrix_workflow import CompetitorMatrixWorkflow
from .problem_radar_workflow import ProblemRadarWorkflow

WORKFLOW_REGISTRY = {
    "shopify_revamp": ShopifyRevampWorkflow,
    "shopify-revamp": ShopifyRevampWorkflow,
    "lead_harvester": LeadHarvesterWorkflow,
    "lead-harvester": LeadHarvesterWorkflow,
    "brand_audit": BrandAuditWorkflow,
    "brand-audit": BrandAuditWorkflow,
    "competitor_matrix": CompetitorMatrixWorkflow,
    "competitor-matrix": CompetitorMatrixWorkflow,
    "problem_radar": ProblemRadarWorkflow,
    "problem-radar": ProblemRadarWorkflow,
}

def get_workflow(workflow_id: str) -> BaseWorkflow:
    normalized = (workflow_id or "").strip().lower().replace("-", "_")
    cls = WORKFLOW_REGISTRY.get(workflow_id) or WORKFLOW_REGISTRY.get(normalized)
    if not cls:
        raise ValueError(f"Unknown workflow id: {workflow_id}. Available: {list(WORKFLOW_REGISTRY.keys())}")
    return cls()

__all__ = [
    "BaseWorkflow",
    "ShopifyRevampWorkflow",
    "LeadHarvesterWorkflow",
    "BrandAuditWorkflow",
    "CompetitorMatrixWorkflow",
    "ProblemRadarWorkflow",
    "WORKFLOW_REGISTRY",
    "get_workflow",
]
