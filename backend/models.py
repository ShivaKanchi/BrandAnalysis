"""
backend/models.py
Core Pydantic data models for:
- Shopify Store Auditing, Prospecting, and Lead Qualification (New Automation)
- Personal Brand Reverse-Engineering & Micro-SaaS Recommendations (Preserved)
- Google Maps Lead Discovery (Preserved)
- Competitor Intelligence (Preserved)
- Software Engineer Problem & Micro-SaaS Radar (Preserved)
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field

# ==============================================================================
# 1. NEW AUTOMATION: SHOPIFY REVAMP & STORE AUDITING SCHEMAS
# ==============================================================================

class ShopifyStoreLead(BaseModel):
    """
    Data model representing a discovered or audited Shopify store lead.
    Tracks technical audits, UX evaluations, social presence, and outreach copy.
    """
    domain: str = Field(..., description="Root domain or URL of the Shopify store (e.g. brand.com)")
    store_name: Optional[str] = Field(None, description="Display name of the store or brand")
    platform: str = Field(default="shopify", description="Platform identifier (default 'shopify')")
    is_shopify: bool = Field(default=True, description="Whether the store was verified as a Shopify instance")
    
    # Social & Audience Metrics
    followers: Optional[int] = Field(default=0, description="Follower count across primary social channels (e.g. Instagram/TikTok)")
    engagement_rate: Optional[float] = Field(default=0.0, description="Estimated engagement rate percentage (e.g. 2.4%)")
    social_handle: Optional[str] = Field(None, description="Primary social handle (e.g. @brand)")
    social_platform: Optional[str] = Field(None, description="Primary social platform (Instagram, TikTok, etc.)")
    social_url: Optional[str] = Field(None, description="Direct URL to social profile")
    
    # Technical & Performance Audits
    lighthouse_performance: Optional[float] = Field(None, description="Lighthouse mobile performance score (0-100)")
    lighthouse_seo: Optional[float] = Field(None, description="Lighthouse SEO score (0-100)")
    lighthouse_accessibility: Optional[float] = Field(None, description="Lighthouse Accessibility score (0-100)")
    lighthouse_best_practices: Optional[float] = Field(None, description="Lighthouse Best Practices score (0-100)")
    
    # Console & Runtime Errors
    console_errors_count: int = Field(default=0, description="Count of JavaScript errors and uncaught exceptions")
    console_error_logs: List[str] = Field(default_factory=list, description="Extracted console error messages & 404 assets")
    
    # Visual & UX Evaluation
    vision_score: Optional[int] = Field(None, description="Visual design & UX rating scored 1-100")
    vision_critique: Optional[str] = Field(None, description="Narrative critique detailing UI friction points")
    vision_bad_patterns: List[str] = Field(default_factory=list, description="List of detected outdated or anti-pattern UI elements")
    vision_revamp_suggestions: List[str] = Field(default_factory=list, description="Top 3 recommended revamp design improvements")
    desktop_screenshot_path: Optional[str] = Field(None, description="Path or URL to desktop full-page screenshot")
    mobile_screenshot_path: Optional[str] = Field(None, description="Path or URL to mobile viewport screenshot")
    
    # AI Outreach & Revamp Proposal
    pitch_email: Optional[str] = Field(None, description="Personalized high-conversion cold outreach email")
    pitch_dm: Optional[str] = Field(None, description="Short, punchy direct message for Instagram/LinkedIn")
    redesign_blueprint: List[str] = Field(default_factory=list, description="3-point modernization blueprint tailored to niche")
    
    # Qualification Status
    qualified_for_revamp: bool = Field(default=False, description="Whether store meets revamping qualification criteria")
    qualification_reasons: List[str] = Field(default_factory=list, description="Reasons for qualification or disqualification")
    
    # Metadata
    niche: Optional[str] = Field(None, description="E-commerce niche/category (e.g. Fashion, Skincare, Coffee)")
    contact_email: Optional[str] = Field(None, description="Public store contact or support email")
    phone: Optional[str] = Field(None, description="Phone number if discovered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary additional metadata")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditThresholds(BaseModel):
    """
    Configurable qualification thresholds for identifying high-leverage revamp prospects.
    Stores with large audiences but poor performance/errors are prime candidates for revamp pitches.
    """
    min_followers: int = Field(default=2500, description="Minimum social followers to indicate commercial traction")
    max_lighthouse_score: float = Field(default=60.0, description="Maximum Lighthouse speed score to qualify as needing revamp")
    min_console_errors: int = Field(default=1, description="Minimum console errors required to demonstrate technical issues")
    max_vision_score: int = Field(default=75, description="Maximum vision score to trigger visual UX revamp")

    def evaluate(self, lead: ShopifyStoreLead) -> bool:
        """
        Evaluate if a given lead meets the qualification criteria for a redesign revamp.
        Returns True if qualified and updates lead.qualified_for_revamp and lead.qualification_reasons.
        """
        reasons: List[str] = []
        is_qualified = False

        if not lead.is_shopify:
            lead.qualified_for_revamp = False
            lead.qualification_reasons = ["Not a verified Shopify store."]
            return False

        has_traction = (lead.followers or 0) >= self.min_followers
        if has_traction:
            reasons.append(f"Strong audience traction ({lead.followers:,} followers >= {self.min_followers:,}).")

        has_speed_issue = (
            lead.lighthouse_performance is not None
            and lead.lighthouse_performance <= self.max_lighthouse_score
        )
        if has_speed_issue:
            reasons.append(f"Poor speed/performance score ({lead.lighthouse_performance:.0f}/100 <= {self.max_lighthouse_score:.0f}).")

        has_errors = lead.console_errors_count >= self.min_console_errors
        if has_errors:
            reasons.append(f"Active runtime console errors ({lead.console_errors_count} errors >= {self.min_console_errors}).")

        has_ux_issue = (
            lead.vision_score is not None
            and lead.vision_score <= self.max_vision_score
        )
        if has_ux_issue:
            reasons.append(f"Sub-optimal UI/UX rating ({lead.vision_score}/100 <= {self.max_vision_score}).")

        if has_traction and (has_speed_issue or has_errors or has_ux_issue):
            is_qualified = True
        elif not has_traction and (has_speed_issue and has_errors and has_ux_issue):
            is_qualified = True
            reasons.append("Extreme technical & UX debt across all audit vectors.")
        else:
            if not has_traction:
                reasons.append(f"Audience below minimum threshold ({lead.followers or 0} < {self.min_followers}).")
            if not (has_speed_issue or has_errors or has_ux_issue):
                reasons.append("Store performance, console, and UX metrics are above thresholds (no revamp needed).")

        lead.qualified_for_revamp = is_qualified
        lead.qualification_reasons = reasons
        return is_qualified


class WorkflowNodeState(BaseModel):
    """
    Represents the runtime state of a specific node or step in the workflow graph.
    Used for telemetry, streaming progress, and UI visualization.
    """
    id: str = Field(..., description="Unique node or stage identifier (e.g. 'detect_shopify', 'audit_speed')")
    label: str = Field(..., description="Human-readable node label (e.g. 'Shopify Detection')")
    status: Literal["idle", "running", "completed", "error"] = Field(
        default="idle", description="Current node execution status"
    )
    duration_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")
    data: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary output payload from the node")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ShopifyDetectionResult(BaseModel):
    is_shopify: bool = Field(..., description="Whether the site is powered by Shopify")
    confidence: float = Field(default=0.0, description="Detection confidence 0.0 - 1.0")
    signals: List[str] = Field(default_factory=list, description="List of positive detection signals observed")
    theme_hints: Dict[str, Any] = Field(default_factory=dict, description="Extracted theme info (name, id, CDN links)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="HTTP status, redirects, headers")


class ConsoleAuditResult(BaseModel):
    console_errors_count: int = Field(default=0)
    console_warnings_count: int = Field(default=0)
    uncaught_exceptions_count: int = Field(default=0)
    failed_requests_count: int = Field(default=0)
    console_error_logs: List[str] = Field(default_factory=list)
    failed_request_urls: List[str] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)


class LighthouseAuditResult(BaseModel):
    performance: float = Field(default=0.0)
    accessibility: float = Field(default=0.0)
    best_practices: float = Field(default=0.0)
    seo: float = Field(default=0.0)
    first_contentful_paint: Optional[str] = None
    largest_contentful_paint: Optional[str] = None
    cumulative_layout_shift: Optional[float] = None
    total_blocking_time: Optional[str] = None
    speed_index: Optional[str] = None
    audit_source: Literal["google_pagespeed_api", "local_lighthouse_cli", "playwright_synthetic"] = "google_pagespeed_api"
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)


class VisionAuditResult(BaseModel):
    vision_score: int = Field(default=50, description="1-100 visual quality score")
    vision_critique: str = Field(default="", description="Qualitative critique of store UI")
    bad_patterns: List[str] = Field(default_factory=list)
    revamp_improvements: List[str] = Field(default_factory=list)
    desktop_screenshot_path: Optional[str] = None
    mobile_screenshot_path: Optional[str] = None
    model_used: str = Field(default="heuristic_fallback")


class PitchResult(BaseModel):
    pitch_email: str = Field(..., description="Complete personalized email")
    pitch_dm: str = Field(..., description="Short DM for IG/LinkedIn")
    subject_line: str = Field(..., description="Email subject line")
    redesign_blueprint: List[str] = Field(default_factory=list, description="3-point modernization recommendations")
    qualifying_reasons: List[str] = Field(default_factory=list)


# ==============================================================================
# 2. PRESERVED LEGACY SCHEMAS (Brand Analysis, Prospector, Radar)
# ==============================================================================

class Citation(BaseModel):
    source_type: Literal["bio", "post_caption", "reel", "highlight", "external_link", "general_profile", "social_link"] = Field(
        ..., description="Where this evidence was extracted from"
    )
    content_excerpt: str = Field(
        ..., description="Exact quote, snippet, or phrase from the profile as evidence"
    )
    post_index: Optional[int] = Field(
        None, description="Index or number of the post (e.g., 1 for most recent)"
    )
    date_or_context: Optional[str] = Field(
        None, description="Context or approximate date/timeframe if available"
    )

class InterestItem(BaseModel):
    topic: str = Field(..., description="Specific interest, hobby, or domain passion")
    category: str = Field(..., description="High-level category (e.g., Fitness, Tech, Business, Lifestyle, Art)")
    citations: List[Citation] = Field(..., description="List of concrete citations and quotes supporting this interest")
    confidence: Literal["High", "Medium", "Low"] = Field(
        ..., description="Confidence level based on depth and directness of evidence"
    )
    confidence_reasoning: str = Field(
        ..., description="Explanation of why this confidence level was assigned"
    )

class PersonalBrandProfile(BaseModel):
    brand_archetype: str = Field(..., description="Archetype (e.g. The Scientific Educator, The Solopreneur)")
    primary_niche: str = Field(..., description="Main domain or focus area")
    secondary_niches: List[str] = Field(default_factory=list, description="Supporting or adjacent niches")
    target_audience: str = Field(..., description="Demographics, mindset, and pain points of their followers")
    content_pillars: List[str] = Field(..., description="Key recurring themes in their content")
    tone_and_voice: str = Field(..., description="Voice style")
    visual_aesthetic: Optional[str] = Field(None, description="Visual tone or aesthetic style")
    current_monetization_methods: List[str] = Field(
        default_factory=list, description="Observed current monetization"
    )

class LocationInfo(BaseModel):
    detected_location: str = Field("Global / Not Specified", description="City, region, or country of the brand")
    source: Literal["Instagram Bio", "Instagram Captions", "Google Search", "User Specified", "Inferred"] = "Inferred"
    confidence: Literal["High", "Medium", "Low"] = "Medium"
    details: Optional[str] = Field(None, description="Context or explanation of how location was identified")

class SocialLinkItem(BaseModel):
    platform: str = Field(..., description="Name of platform (YouTube, Twitter/X, TikTok, LinkedIn, Website, etc.)")
    url: str = Field(..., description="Full URL of the profile or resource")
    handle_or_title: Optional[str] = Field(None, description="Account handle or page title")
    status_notes: Optional[str] = Field(None, description="Observations regarding activity or funnel role")

class SocialStatusAnalysis(BaseModel):
    linked_socials: List[SocialLinkItem] = Field(default_factory=list, description="All discovered external social channels")
    cross_platform_presence_score: Literal["Strong Multi-Platform", "Moderate", "Single-Platform Dependent"] = Field(
        ..., description="Evaluation of their reach beyond Instagram"
    )
    social_ecosystem_overview: str = Field(
        ..., description="How their audience funnel flows between Instagram and external touchpoints"
    )
    strengths: List[str] = Field(default_factory=list, description="Current strengths in their social setup")
    vulnerabilities: List[str] = Field(default_factory=list, description="Weaknesses, dead ends, or missed traffic funnels")

class BrandImprovementPlan(BaseModel):
    funnel_and_conversion_improvements: List[str] = Field(..., description="Specific optimizations for bio, CTAs, lead magnets")
    content_and_messaging_improvements: List[str] = Field(..., description="Enhancements for post positioning and hooks")
    cross_platform_growth_improvements: List[str] = Field(..., description="Recommendations for repurposing content")
    quick_wins_under_30_days: List[str] = Field(..., description="High-impact actions executable in under 30 days")

class CompetitorItem(BaseModel):
    name: str = Field(..., description="Name of the competing brand, creator, studio, or business")
    competitor_type: Literal["Local Competitor", "Direct Domain Rival", "Indirect / Alternative"] = Field(...)
    location: str = Field(..., description="City/locality of the competitor, or 'Global / Online'")
    url_or_handle: Optional[str] = Field(None, description="Instagram handle, website, or Google Maps listing")
    market_standing: Literal["Market Leader", "Established", "Emerging / Challenger", "Niche Player"] = Field(...)
    estimated_pricing: Optional[str] = Field(None)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    ratings_or_reviews: Optional[str] = Field(None)
    differentiator_vs_target: str = Field(..., description="How target contrasts with or outpositions competitor")

class MarketAnalysis(BaseModel):
    market_saturation: Literal["Low", "Medium", "High", "Saturated"] = Field(...)
    market_trend: Literal["Rapidly Growing", "Steady Growth", "Mature / Flat", "Declining / Disrupted"] = Field(...)
    locality_market_dynamics: str = Field(...)
    domain_market_dynamics: str = Field(...)
    untapped_market_opportunities: List[str] = Field(default_factory=list)
    strategic_threats: List[str] = Field(default_factory=list)

class SoftwareProductRecommendation(BaseModel):
    product_name: str = Field(...)
    product_type: str = Field(...)
    core_value_proposition: str = Field(...)
    problem_it_solves: str = Field(...)
    target_buyers: str = Field(...)
    suggested_monetization_model: str = Field(...)
    mvp_features: List[str] = Field(...)
    feasibility_effort: Literal["Low", "Medium", "High"] = Field(...)

class SoftwareProductOpportunity(BaseModel):
    needs_software_product: bool = Field(...)
    confidence_in_verdict: Literal["High", "Medium", "Low"] = Field(...)
    verdict_summary: str = Field(...)
    recommended_product_ideas: List[SoftwareProductRecommendation] = Field(default_factory=list)
    why_not_reasons: List[str] = Field(default_factory=list)
    existing_software_gaps: List[str] = Field(default_factory=list)

class ProfileData(BaseModel):
    username: str
    full_name: Optional[str] = ""
    biography: str = ""
    external_url: Optional[str] = ""
    followers_count: Optional[str] = ""
    following_count: Optional[str] = ""
    posts_count: Optional[str] = ""
    is_verified: Optional[bool] = False
    location_info: Optional[LocationInfo] = None
    social_links: List[SocialLinkItem] = Field(default_factory=list)
    posts: List[Dict[str, Any]] = Field(default_factory=list)

class WebsiteAuditAndOpportunity(BaseModel):
    has_website: bool = Field(...)
    existing_url: Optional[str] = None
    audit_verdict: str = Field(...)
    lead_leakage_analysis: str = Field(...)
    recommended_website_type: str = Field(...)
    core_lead_magnets: List[str] = Field(default_factory=list)
    essential_pages_and_sections: List[str] = Field(default_factory=list)
    local_seo_traffic_playbook: str = Field(...)
    estimated_lead_increase: str = Field(...)

class BrandingAnalysisReport(BaseModel):
    profile: ProfileData
    location: LocationInfo
    social_status: SocialStatusAnalysis
    interests: List[InterestItem]
    brand_profile: PersonalBrandProfile
    brand_improvements: BrandImprovementPlan
    competitors: List[CompetitorItem] = Field(default_factory=list)
    market_analysis: MarketAnalysis
    website_opportunity: WebsiteAuditAndOpportunity
    software_opportunity: SoftwareProductOpportunity
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    analyzed_by_model: str = "ollama"

class DiscoveredLeadItem(BaseModel):
    business_name: str = Field(..., description="Name of the business or place")
    category: Optional[str] = Field(None, description="Category or industry type")
    address_or_location: Optional[str] = Field(None, description="Physical address or neighborhood")
    website: Optional[str] = Field(None, description="Official website URL if discovered")
    instagram_handle: Optional[str] = Field(None, description="Extracted Instagram handle")
    instagram_url: Optional[str] = Field(None, description="Full URL to Instagram profile")
    maps_url: Optional[str] = Field(None, description="Google Maps listing link")
    rating: Optional[str] = Field(None, description="Google Maps rating")
    review_count: Optional[str] = Field(None, description="Total review count")
    phone: Optional[str] = Field(None, description="Business phone number")
    lead_status: Literal["Instagram Verified", "Website Only (No IG)", "Maps Only"] = "Instagram Verified"

class LeadProspectingReport(BaseModel):
    search_query: str = Field(..., description="Original search query used")
    target_locality: str = Field(..., description="City or neighborhood searched")
    total_places_scanned: int = Field(0)
    leads_with_instagram: int = Field(0)
    leads: List[DiscoveredLeadItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class MicroSaaSBlueprint(BaseModel):
    product_name_concept: str = Field(...)
    core_value_proposition: str = Field(...)
    mvp_features: List[str] = Field(default_factory=list)
    target_icp: str = Field(...)
    monetization_model: str = Field(...)
    estimated_tam_or_urgency: str = Field(...)

class SoftwareEngineerProblemItem(BaseModel):
    problem_title: str = Field(...)
    category: str = Field(...)
    frequency_velocity: Literal["Rising this week", "Consistent Pain Point", "Spike/Heated Debate", "Emerging Trend"] = Field(...)
    severity_score: int = Field(...)
    summary_and_quotes: str = Field(...)
    root_cause_analysis: str = Field(...)
    sources_cited: List[Dict[str, str]] = Field(default_factory=list)
    recommended_microsaas: MicroSaaSBlueprint = Field(...)

class SoftwareProblemRadarReport(BaseModel):
    report_title: str = Field("Weekly Software Engineer Problem & Micro-SaaS Radar")
    timeframe: str = Field(...)
    data_sources_ingested: List[str] = Field(default_factory=list)
    total_discussions_analyzed: int = Field(...)
    macro_trend_summary: str = Field(...)
    top_problems: List[SoftwareEngineerProblemItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    analyzed_by_model: str = "ollama"

class CompetitorComparisonReport(BaseModel):
    target_brand: str
    target_niche: str
    target_location: str
    competitors: List[CompetitorItem] = Field(default_factory=list)
    market_analysis: Optional[MarketAnalysis] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
