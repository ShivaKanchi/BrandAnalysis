"""
backend/tools
Unified atomic tools registry for:
- Platform Detection & Web Scraping
- Technical, Speed, & Visual UX Auditing
- AI Outreach, Positioning, & Strategy Synthesis
- Persistent Storage & Reporting
"""

from backend.tools.scrapers.shopify_detector import (
    detect_shopify,
    detect_shopify_async,
    detect_shopify_from_html
)
from backend.tools.scrapers.social_scraper import (
    extract_social_links,
    scrape_instagram_metrics,
    scrape_tiktok_metrics,
    resolve_social_presence
)
from backend.tools.scrapers.maps_harvester import (
    MapsHarvester,
    harvest_niche_leads
)
from backend.tools.scrapers.console_listener import (
    ConsoleListener,
    capture_console_errors,
    capture_console_errors_sync
)
from backend.tools.scrapers.instagram_profile_scraper import (
    InstagramProfileScraper
)
from backend.tools.auditors.lighthouse_auditor import (
    LighthouseAuditor,
    audit_lighthouse
)
from backend.tools.auditors.vision_ux_auditor import (
    VisionUXAuditor,
    audit_vision_ux
)
from backend.tools.analyzers.brand_analyzer import (
    BrandAnalyzer
)
from backend.tools.analyzers.pitch_generator import (
    PitchGenerator,
    generate_revamp_pitch
)
from backend.tools.analyzers.competitor_analyzer import (
    CompetitorAnalyzer
)
from backend.tools.analyzers.problem_radar import (
    SoftwareProblemRadar,
    run_problem_radar
)
from backend.tools.storage.lead_store import (
    LeadStore,
    lead_store
)
from backend.tools.storage.report_generator import (
    ReportGenerator
)

__all__ = [
    # Scrapers
    "detect_shopify",
    "detect_shopify_async",
    "detect_shopify_from_html",
    "extract_social_links",
    "scrape_instagram_metrics",
    "scrape_tiktok_metrics",
    "resolve_social_presence",
    "MapsHarvester",
    "harvest_niche_leads",
    "ConsoleListener",
    "capture_console_errors",
    "capture_console_errors_sync",
    "InstagramProfileScraper",
    # Auditors
    "LighthouseAuditor",
    "audit_lighthouse",
    "VisionUXAuditor",
    "audit_vision_ux",
    # Analyzers
    "BrandAnalyzer",
    "PitchGenerator",
    "generate_revamp_pitch",
    "CompetitorAnalyzer",
    "SoftwareProblemRadar",
    "run_problem_radar",
    # Storage
    "LeadStore",
    "lead_store",
    "ReportGenerator"
]
