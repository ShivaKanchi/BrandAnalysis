from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

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
        ..., description="Explanation of why this confidence level was assigned (e.g. repeated in 5 posts and bio)"
    )

class PersonalBrandProfile(BaseModel):
    brand_archetype: str = Field(..., description="Archetype (e.g. The Scientific Educator, The Solopreneur, The Lifestyle Curator)")
    primary_niche: str = Field(..., description="Main domain or focus area")
    secondary_niches: List[str] = Field(default_factory=list, description="Supporting or adjacent niches")
    target_audience: str = Field(..., description="Demographics, mindset, and pain points of their followers")
    content_pillars: List[str] = Field(..., description="Key recurring themes in their content")
    tone_and_voice: str = Field(..., description="Voice style (e.g., Authoritative, empathetic, provocative, playful)")
    visual_aesthetic: Optional[str] = Field(None, description="Visual tone or aesthetic style")
    current_monetization_methods: List[str] = Field(
        default_factory=list, description="Observed current monetization (sponsorships, courses, consulting, merchandise, etc.)"
    )

class LocationInfo(BaseModel):
    detected_location: str = Field("Global / Not Specified", description="City, region, or country of the brand")
    source: Literal["Instagram Bio", "Instagram Captions", "Google Search", "User Specified", "Inferred"] = "Inferred"
    confidence: Literal["High", "Medium", "Low"] = "Medium"
    details: Optional[str] = Field(None, description="Context or explanation of how location was identified")

class SocialLinkItem(BaseModel):
    platform: str = Field(..., description="Name of platform (YouTube, Twitter/X, TikTok, LinkedIn, Website, Podcast, etc.)")
    url: str = Field(..., description="Full URL of the profile or resource")
    handle_or_title: Optional[str] = Field(None, description="Account handle or page title")
    status_notes: Optional[str] = Field(None, description="Observations regarding activity, consistency, or funnel role")

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
    funnel_and_conversion_improvements: List[str] = Field(
        ..., description="Specific optimizations for bio, call-to-actions, lead magnets, and link-in-bio"
    )
    content_and_messaging_improvements: List[str] = Field(
        ..., description="Enhancements for post positioning, recurring series, hook structures, and authority"
    )
    cross_platform_growth_improvements: List[str] = Field(
        ..., description="Recommendations for repurposing content and establishing secondary platforms"
    )
    quick_wins_under_30_days: List[str] = Field(
        ..., description="High-impact actions that can be executed in under 30 days"
    )

class CompetitorItem(BaseModel):
    name: str = Field(..., description="Name of the competing brand, creator, studio, or business")
    competitor_type: Literal["Local Competitor", "Direct Domain Rival", "Indirect / Alternative"] = Field(
        ..., description="Whether this is a local geo competitor or a global niche rival"
    )
    location: str = Field(..., description="City/locality of the competitor, or 'Global / Online'")
    url_or_handle: Optional[str] = Field(None, description="Instagram handle, website, or Google Maps listing")
    market_standing: Literal["Market Leader", "Established", "Emerging / Challenger", "Niche Player"] = Field(
        ..., description="Market position"
    )
    estimated_pricing: Optional[str] = Field(None, description="Known or estimated pricing/monetization strategy")
    strengths: List[str] = Field(default_factory=list, description="Key competitor strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Key competitor flaws or gaps")
    ratings_or_reviews: Optional[str] = Field(None, description="Public sentiment, Google reviews, or reputation notes")
    differentiator_vs_target: str = Field(
        ..., description="How our target brand contrasts with or outpositions this competitor"
    )

class MarketAnalysis(BaseModel):
    market_saturation: Literal["Low", "Medium", "High", "Saturated"] = Field(
        ..., description="Degree of competition and saturation in this niche"
    )
    market_trend: Literal["Rapidly Growing", "Steady Growth", "Mature / Flat", "Declining / Disrupted"] = Field(
        ..., description="Overall industry market trajectory"
    )
    locality_market_dynamics: str = Field(
        ..., description="Analysis of local demand, density of alternatives, and city-level opportunities"
    )
    domain_market_dynamics: str = Field(
        ..., description="Macro industry trends, audience purchasing patterns, and monetization shifts"
    )
    untapped_market_opportunities: List[str] = Field(
        default_factory=list, description="Gaps left open by competitors that this brand can dominate"
    )
    strategic_threats: List[str] = Field(
        default_factory=list, description="Competitive risks or emerging headwinds to defend against"
    )

class SoftwareProductRecommendation(BaseModel):
    product_name: str = Field(..., description="Catchy conceptual name for the software product")
    product_type: str = Field(
        ..., description="Type of software (e.g., Micro-SaaS, Lead-Gen Tool, Workflow Automation, Client Portal, Community OS)"
    )
    core_value_proposition: str = Field(..., description="One-line elevator pitch of what the product does")
    problem_it_solves: str = Field(..., description="The bottleneck or friction it solves for the creator or their audience")
    target_buyers: str = Field(..., description="Who pays for it (the creator's audience, agency clients, B2B peers)")
    suggested_monetization_model: str = Field(..., description="Pricing model (e.g. $29/mo SaaS, $49 one-off, freemium)")
    mvp_features: List[str] = Field(..., description="Top 3-4 features for the first version")
    feasibility_effort: Literal["Low", "Medium", "High"] = Field(..., description="Effort to build MVP")

class SoftwareProductOpportunity(BaseModel):
    needs_software_product: bool = Field(..., description="Whether this creator/brand genuinely needs or benefits from a software product")
    confidence_in_verdict: Literal["High", "Medium", "Low"] = Field(..., description="Confidence in this recommendation")
    verdict_summary: str = Field(..., description="Direct rationale for why they do or do not need a software product")
    recommended_product_ideas: List[SoftwareProductRecommendation] = Field(
        default_factory=list, description="Tailored software product concepts if applicable"
    )
    why_not_reasons: List[str] = Field(
        default_factory=list, description="Reasons against building custom software (if not recommended or alternative advice)"
    )
    existing_software_gaps: List[str] = Field(
        default_factory=list, description="Observed operational bottlenecks or missed revenue opportunities"
    )

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
    has_website: bool = Field(..., description="Whether the brand currently has a dedicated, official website")
    existing_url: Optional[str] = Field(None, description="Current website URL if present")
    audit_verdict: str = Field(..., description="Summary of status, e.g. 'No Website (Critical Lead Leakage)' or 'Active Website'")
    lead_leakage_analysis: str = Field(..., description="Explanation of leads and traffic lost by relying exclusively on Instagram")
    recommended_website_type: str = Field(..., description="Type of website to build (e.g., On-Demand Booking Funnel, Local Service Portal)")
    core_lead_magnets: List[str] = Field(default_factory=list, description="Immediate lead capture mechanisms (e.g. Instant Quote, WhatsApp Widget, First Order Discount)")
    essential_pages_and_sections: List[str] = Field(default_factory=list, description="Must-have website sections to maximize conversion rate")
    local_seo_traffic_playbook: str = Field(..., description="Strategy to capture high-intent Google Search and Maps traffic in their locality")
    estimated_lead_increase: str = Field(..., description="Projected increase in inbound inquiries and customer bookings")

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


# ==========================================
# AUTO-PROSPECTING & LOCAL LEAD SCHEMAS
# ==========================================

class DiscoveredLeadItem(BaseModel):
    business_name: str = Field(..., description="Name of the business or place")
    category: Optional[str] = Field(None, description="Category or industry type")
    address_or_location: Optional[str] = Field(None, description="Physical address or neighborhood")
    website: Optional[str] = Field(None, description="Official website URL if discovered")
    instagram_handle: Optional[str] = Field(None, description="Extracted Instagram handle (e.g. 'aurum.bangalore')")
    instagram_url: Optional[str] = Field(None, description="Full URL to Instagram profile")
    maps_url: Optional[str] = Field(None, description="Google Maps listing link")
    rating: Optional[str] = Field(None, description="Google Maps rating (e.g. '4.8')")
    review_count: Optional[str] = Field(None, description="Total review count")
    phone: Optional[str] = Field(None, description="Business phone number if visible")
    lead_status: Literal["Instagram Verified", "Website Only (No IG)", "Maps Only", "Locality Verified"] = "Instagram Verified"
    lead_intent_score: Literal["High Intent", "Promising", "Low Intent / Ghost"] = Field("Promising", description="Intent rating based on verified customer activity and digital assets")
    authenticity_signals: List[str] = Field(default_factory=list, description="Concrete proof points (reviews, verified domain, phone, etc.)")
    opportunity_angle: Optional[str] = Field(None, description="Recommended outreach pitch angle based on funnel gaps")
    is_fresh_lead: bool = Field(True, description="Whether this lead is freshly discovered vs previously seen")
    first_discovered_at: Optional[str] = Field(None, description="Timestamp when lead was first recorded")


class LeadProspectingReport(BaseModel):
    search_query: str = Field(..., description="Original search query used")
    target_locality: str = Field(..., description="City or neighborhood searched")
    total_places_scanned: int = Field(0, description="Total Google Maps places evaluated")
    leads_with_instagram: int = Field(0, description="Leads where an Instagram handle was extracted")
    fresh_leads_count: int = Field(0, description="Count of newly discovered leads not previously in registry")
    recycled_leads_skipped: int = Field(0, description="Count of previously seen leads skipped to ensure fresh results")
    high_intent_count: int = Field(0, description="Count of leads qualified as high intent")
    total_registry_leads: int = Field(0, description="Total leads tracked in the historical registry")
    leads: List[DiscoveredLeadItem] = Field(default_factory=list, description="List of discovered business leads")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ==========================================
# SOFTWARE ENGINEER PROBLEM RADAR SCHEMAS
# ==========================================

class MicroSaaSBlueprint(BaseModel):
    product_name_concept: str = Field(..., description="Catchy, descriptive working name")
    core_value_proposition: str = Field(..., description="The high-impact one-liner solving the pain point")
    mvp_features: List[str] = Field(default_factory=list, description="Top 3 essential features for the initial launch")
    target_icp: str = Field(..., description="Ideal Customer Profile (e.g. Senior Frontend Devs, Staff SREs, DevRel teams)")
    monetization_model: str = Field(..., description="Pricing model, e.g. $29/seat/mo SaaS, usage-based CLI, open-core")
    estimated_tam_or_urgency: str = Field(..., description="Market size or urgency level (High, Niche, Urgent)")


class SoftwareEngineerProblemItem(BaseModel):
    problem_title: str = Field(..., description="Clear, punchy title of the recurring developer pain point")
    category: str = Field(..., description="Domain (e.g. AI-Assisted Burnout, Cloud/K8s Complexity, Legacy Migrations, Interview Fatigue, Testing/CI Bottlenecks)")
    frequency_velocity: Literal["Rising this week", "Consistent Pain Point", "Spike/Heated Debate", "Emerging Trend"] = Field(
        ..., description="Trend velocity and volume indicator"
    )
    severity_score: int = Field(..., description="1-10 severity or developer frustration score")
    summary_and_quotes: str = Field(..., description="Detailed synthesis of developer complaints with sample quotes/posts")
    root_cause_analysis: str = Field(..., description="Why current tools and industry practices fail to solve this")
    sources_cited: List[Dict[str, str]] = Field(default_factory=list, description="Platforms and discussions cited (HN, Reddit, News, Dev.to)")
    recommended_microsaas: MicroSaaSBlueprint = Field(..., description="Direct actionable software product concept to monetize this problem")


class SoftwareProblemRadarReport(BaseModel):
    report_title: str = Field("Weekly Software Engineer Problem & Micro-SaaS Radar", description="Report title")
    timeframe: str = Field(..., description="Time window covered (e.g., 'This Week vs Last Week')")
    data_sources_ingested: List[str] = Field(default_factory=list, description="List of sources queried (Hacker News, Reddit, Dev.to, Google Tech News)")
    total_discussions_analyzed: int = Field(..., description="Total posts/items evaluated")
    macro_trend_summary: str = Field(..., description="High-level narrative of developer sentiment and major shifts this week")
    top_problems: List[SoftwareEngineerProblemItem] = Field(default_factory=list, description="Top trending problems ranked by urgency")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    analyzed_by_model: str = "ollama"

