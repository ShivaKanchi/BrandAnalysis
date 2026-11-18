from typing import Any, Dict

from .base_workflow import BaseWorkflow


class InfluencerDiscoveryWorkflow(BaseWorkflow):
    """Reusable discovery and review queue for youth-gaming influencer campaigns."""

    def __init__(self):
        super().__init__(
            id="influencer_discovery",
            name="Youth Gaming Influencer Discovery",
            description="Ranks a configurable creator catalogue, deduplicates prior runs, and creates a review-ready outreach queue.",
        )
        self._build_dag()

    def _build_dag(self):
        self.add_node("audience_brief", "Audience & niche brief", "Validates the campaign's niche and age-band filters", {"x": 60, "y": 200}, self._brief)
        self.add_node("catalog_discovery", "Creator catalogue discovery", "Retrieves matching candidates without fabricating private audience data", {"x": 350, "y": 200}, self._discover)
        self.add_node("fit_scoring", "Explainable fit scoring", "Scores creator-to-campaign relevance from category and age-band overlap", {"x": 650, "y": 200}, self._score)
        self.add_node("review_queue", "Human review queue", "Persists candidates for activity, safety, and audience verification", {"x": 940, "y": 200}, self._queue)
        self.add_edge("audience_brief", "catalog_discovery")
        self.add_edge("catalog_discovery", "fit_scoring")
        self.add_edge("fit_scoring", "review_queue")

    async def _brief(self, context: Dict[str, Any], log):
        niches = context.get("niches") or context.get("niche") or "all gaming categories"
        bands = context.get("audience_bands") or "10-13,13-17,16-22"
        await log(f"Targeting niches: {niches}; audience bands: {bands}.", "info")
        return {"niches": niches, "audience_bands": bands, "limit": int(context.get("limit") or 100), "fresh_only": bool(context.get("fresh_only", False))}

    async def _discover(self, context: Dict[str, Any], log):
        from core.influencer_discovery import InfluencerDiscovery
        niches = [item.strip() for item in context["niches"].split(",") if item.strip()] if isinstance(context["niches"], str) and context["niches"] != "all gaming categories" else None
        bands = [item.strip() for item in context["audience_bands"].split(",") if item.strip()] if isinstance(context["audience_bands"], str) else context["audience_bands"]
        result = InfluencerDiscovery().discover(niches=niches, audience_bands=bands, limit=context["limit"], fresh_only=context["fresh_only"])
        await log(f"Found {result['count']} matching creators; {result['skipped_previously_seen']} previously seen candidates skipped.", "info")
        return {"discovery_result": result}

    async def _score(self, context: Dict[str, Any], log):
        creators = context["discovery_result"]["influencers"]
        await log(f"Applied category and audience-band relevance scoring to {len(creators)} creators.", "info")
        return {"ranked_influencers": creators}

    async def _queue(self, context: Dict[str, Any], log):
        creators = context["ranked_influencers"]
        await log(f"Saved {len(creators)} candidates to the review queue. Human verification is required before outreach.", "info")
        return {"influencers": creators, "count": len(creators)}
