from .base_workflow import BaseWorkflow
from .shopify_revamp_workflow import ShopifyRevampWorkflow
from .lead_harvester_workflow import LeadHarvesterWorkflow
from .brand_audit_workflow import BrandAuditWorkflow
from .competitor_matrix_workflow import CompetitorMatrixWorkflow
from .problem_radar_workflow import ProblemRadarWorkflow

WORKFLOW_REGISTRY = {
    "shopify_revamp": ShopifyRevampWorkflow,
    "lead_harvester": LeadHarvesterWorkflow,
    "brand_audit": BrandAuditWorkflow,
    "competitor_matrix": CompetitorMatrixWorkflow,
    "problem_radar": ProblemRadarWorkflow,
}

def get_workflow(workflow_id: str) -> BaseWorkflow:
    cls = WORKFLOW_REGISTRY.get(workflow_id)
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
