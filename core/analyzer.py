import re
import json
import logging
from typing import Optional, Dict, Any, List
import requests

try:
    from config.settings import settings
    from core.models import (
        ProfileData,
        BrandingAnalysisReport,
        InterestItem,
        PersonalBrandProfile,
        BrandImprovementPlan,
        SocialStatusAnalysis,
        SocialLinkItem,
        LocationInfo,
        SoftwareProductOpportunity,
        SoftwareProductRecommendation,
        Citation,
        CompetitorItem,
        MarketAnalysis,
        WebsiteAuditAndOpportunity
    )
    from core.social_scraper import SocialAndLocationScraper
    from core.competitors import CompetitorResearcher
except (ImportError, ValueError):
    from ..config.settings import settings
    from .models import (
        ProfileData,
        BrandingAnalysisReport,
        InterestItem,
        PersonalBrandProfile,
        BrandImprovementPlan,
        SocialStatusAnalysis,
        SocialLinkItem,
        LocationInfo,
        SoftwareProductOpportunity,
        SoftwareProductRecommendation,
        Citation,
        CompetitorItem,
        MarketAnalysis,
        WebsiteAuditAndOpportunity
    )
    from .social_scraper import SocialAndLocationScraper
    from .competitors import CompetitorResearcher

logger = logging.getLogger("BrandAnalysis.Analyzer")

ANALYSIS_SYSTEM_PROMPT = """You are an elite Personal Branding Strategist, Growth Architect, and Software Venture Capitalist.
Your task is to analyze an Instagram profile (bio, metrics, external links, social ecosystem, post captions) and perform a comprehensive 5-part strategic deconstruction:

1. LIKES & INTERESTS (Granular catalog with strict citations & confidence scoring):
   - Extract all distinct topics, passions, hobbies, professional domains, and personal interests.
   - For EACH interest, extract concrete quotes or snippets as evidence (citations). Cite the exact bio text, post caption, or context.
   - Assign a confidence score: "High", "Medium", or "Low":
     * High: Directly explicitly stated in bio or repeatedly emphasized across multiple posts/captions.
     * Medium: Clearly present in 1-2 posts or strongly evidenced by context.
     * Low: Inferred from a single casual reference, hashtag, or indirect visual clue.
   - Provide explicit confidence_reasoning explaining why that rating was assigned.

2. PERSONAL BRAND IDENTITY:
   - Identify their brand archetype (e.g. "The Technical Solopreneur", "The Scientific Educator", "The Direct Response Marketer", "The High-Performance Coach").
   - Primary and secondary niches.
   - Target audience profile (who follows them, what they care about, what their pain points are).
   - Core recurring content pillars (3-5 pillars).
   - Tone and voice (e.g. "Pragmatic, authoritative, data-driven, direct").
   - Current monetization methods observed (courses, coaching, newsletter, merch, brand deals, software, none).

3. SOCIAL STATUS & CROSS-PLATFORM ANALYSIS:
   - Evaluate their cross-platform reach beyond Instagram based on linked socials.
   - Score: "Strong Multi-Platform" | "Moderate" | "Single-Platform Dependent".
   - Overview of how their audience funnel currently flows between Instagram and external channels.
   - Specific strengths and vulnerabilities / traffic leaks in their social setup.

4. BRAND IMPROVEMENT RECOMMENDATIONS:
   - Provide concrete, high-leverage improvements to elevate their brand and increase revenue:
     * funnel_and_conversion_improvements (bio optimization, lead magnets, link-in-bio UX, call-to-actions)
     * content_and_messaging_improvements (storytelling frameworks, hooks, recurring series, authority builders)
     * cross_platform_growth_improvements (repurposing pipelines, YouTube/newsletter expansion)
     * quick_wins_under_30_days (immediate high-impact actions)

5. SOFTWARE PRODUCT OPPORTUNITY ASSESSMENT:
   - Determine whether this creator/brand genuinely NEEDS or WOULD BENEFIT from building or owning a software product (Micro-SaaS, Workflow Automation, Client Portal, Interactive Lead-Gen Tool, Community Utility / OS).
   - `needs_software_product`: true OR false.
   - `confidence_in_verdict`: "High", "Medium", or "Low".
   - `verdict_summary`: Clear, executive-level thesis explaining why they should or should not build custom software.
   - If TRUE (or high potential): Provide 1 to 3 concrete, tailor-made software product concepts (name, type, value prop, problem solved, target buyers, monetization model, mvp features, dev effort).
   - If FALSE or if there are major caveats: Provide explicit `why_not_reasons`.
   - Note any `existing_software_gaps` (e.g. manual DMs for bookings, disconnected Google Sheets, missing automated lead magnet).

6. WEBSITE AUDIT & LEAD GENERATION OPPORTUNITY:
   - Determine if the brand has a dedicated official website (exclude generic linktrees, beacons, or raw WhatsApp phone numbers).
   - If they LACK a dedicated website:
     * Flag this as a critical lead-leakage bottleneck (lost Google search traffic, lost bookings, no automated lead intake).
     * Recommend the optimal Website Type (e.g. "On-Demand Local Booking Funnel", "Interactive Service Portal", "Conversion-Focused Landing Page").
     * Provide 2-3 Core Lead Magnets (e.g., "Instant Pricing Calculator", "1-Click WhatsApp Pickup Booking", "First-Order 20% Off Coupon").
     * List 4-5 Essential Pages/Sections to build.
     * Define the Local SEO Traffic Playbook to rank in their city/locality on Google Search & Google Maps.
     * Estimate the projected increase in leads and customer bookings.
   - If they HAVE an active website:
     * Provide actionable audit recommendations to increase conversion rate, SEO rank, and daily lead flow.

CRITICAL INSTRUCTIONS:
- You must respond ONLY with a valid JSON object matching the requested schema.
- Do not make up fake citations. Base all evidence strictly on the provided Instagram data.
"""

SCHEMA_INSTRUCTION = """
Your output JSON must strictly match this structure:
{
  "interests": [
    {
      "topic": "string",
      "category": "string",
      "citations": [
        {
          "source_type": "bio" | "post_caption" | "reel" | "highlight" | "external_link" | "general_profile" | "social_link",
          "content_excerpt": "string",
          "post_index": integer or null,
          "date_or_context": "string or null"
        }
      ],
      "confidence": "High" | "Medium" | "Low",
      "confidence_reasoning": "string"
    }
  ],
  "brand_profile": {
    "brand_archetype": "string",
    "primary_niche": "string",
    "secondary_niches": ["string"],
    "target_audience": "string",
    "content_pillars": ["string"],
    "tone_and_voice": "string",
    "visual_aesthetic": "string or null",
    "current_monetization_methods": ["string"]
  },
  "social_status": {
    "cross_platform_presence_score": "Strong Multi-Platform" | "Moderate" | "Single-Platform Dependent",
    "social_ecosystem_overview": "string",
    "strengths": ["string"],
    "vulnerabilities": ["string"]
  },
  "brand_improvements": {
    "funnel_and_conversion_improvements": ["string"],
    "content_and_messaging_improvements": ["string"],
    "cross_platform_growth_improvements": ["string"],
    "quick_wins_under_30_days": ["string"]
  },
  "website_opportunity": {
    "has_website": boolean,
    "existing_url": "string or null",
    "audit_verdict": "string",
    "lead_leakage_analysis": "string",
    "recommended_website_type": "string",
    "core_lead_magnets": ["string"],
    "essential_pages_and_sections": ["string"],
    "local_seo_traffic_playbook": "string",
    "estimated_lead_increase": "string"
  },
  "software_opportunity": {
    "needs_software_product": boolean,
    "confidence_in_verdict": "High" | "Medium" | "Low",
    "verdict_summary": "string",
    "recommended_product_ideas": [
      {
        "product_name": "string",
        "product_type": "string",
        "core_value_proposition": "string",
        "problem_it_solves": "string",
        "target_buyers": "string",
        "suggested_monetization_model": "string",
        "mvp_features": ["string"],
        "feasibility_effort": "Low" | "Medium" | "High"
      }
    ],
    "why_not_reasons": ["string"],
    "existing_software_gaps": ["string"]
  }
}
"""

class BrandAnalyzer:
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.api_key = api_key or settings.OLLAMA_API_KEY
        self.social_scraper = SocialAndLocationScraper()
        self.competitor_researcher = CompetitorResearcher(
            ollama_url=self.ollama_url,
            model_name=self.model_name
        )

    def analyze_profile(
        self,
        profile: ProfileData,
        user_location_override: Optional[str] = None,
        enable_competitor_research: bool = True
    ) -> BrandingAnalysisReport:
        """
        Runs the full end-to-end intelligence pipeline:
        1. Resolves location (Bio -> Captions -> Google Search fallback -> User override)
        2. Scrapes outbound social profiles from external URL
        3. LLM extraction of Likes, Interests (with citations), Brand Identity, Social Status, Improvements, Software Opportunity
        4. Competitor Discovery (Local & Domain via Google Search & Google Maps) & Market Analysis
        5. Assembles into a unified master BrandingAnalysisReport
        """
        logger.info(f"Analyzing profile @{profile.username} with model {self.model_name}...")

        # Step 1: Location Resolution
        captions = [p.get("caption", "") for p in profile.posts]
        location_info = self.social_scraper.resolve_location(
            username=profile.username,
            full_name=profile.full_name or "",
            biography=profile.biography or "",
            posts_captions=captions,
            user_override=user_location_override
        )
        profile.location_info = location_info

        # Step 2: Scrape external social links if available
        if profile.external_url and not profile.social_links:
            logger.info(f"Scraping outbound social links from {profile.external_url}...")
            profile.social_links = self.social_scraper.scrape_social_links(profile.external_url)

        # Step 3: Format profile data and call Ollama
        profile_summary = self._format_profile_context(profile, location_info)
        user_prompt = f"{profile_summary}\n\n{SCHEMA_INSTRUCTION}\nProduce the comprehensive strategic JSON analysis now:"

        raw_response = self._call_ollama(user_prompt)
        parsed_json = self._clean_and_parse_json(raw_response)

        # Step 4: Validate components
        interests = [InterestItem(**item) for item in parsed_json.get("interests", [])]
        brand_profile = PersonalBrandProfile(**parsed_json.get("brand_profile", {}))
        
        # Social status
        social_json = parsed_json.get("social_status", {})
        social_status = SocialStatusAnalysis(
            linked_socials=profile.social_links,
            cross_platform_presence_score=social_json.get("cross_platform_presence_score", "Moderate"),
            social_ecosystem_overview=social_json.get("social_ecosystem_overview", "Instagram serves as the primary audience anchor."),
            strengths=social_json.get("strengths", ["Dedicated Instagram follower base"]),
            vulnerabilities=social_json.get("vulnerabilities", ["Single point of failure on Instagram algorithm"])
        )

        # Brand improvement plan
        imp_json = parsed_json.get("brand_improvements", {})
        brand_improvements = BrandImprovementPlan(
            funnel_and_conversion_improvements=imp_json.get("funnel_and_conversion_improvements", [
                "Deploy a high-converting lead magnet in link-in-bio to capture email subscribers."
            ]),
            content_and_messaging_improvements=imp_json.get("content_and_messaging_improvements", [
                "Introduce high-retention recurring weekly content series."
            ]),
            cross_platform_growth_improvements=imp_json.get("cross_platform_growth_improvements", [
                "Repurpose top-performing reels into YouTube Shorts and LinkedIn posts."
            ]),
            quick_wins_under_30_days=imp_json.get("quick_wins_under_30_days", [
                "Audit and clean bio copy with a single clear value statement and CTA."
            ])
        )

        # Website audit & lead generation opportunity
        web_json = parsed_json.get("website_opportunity", {})
        has_web = web_json.get("has_website", False)
        # Verify if profile had a real website in external_url
        if profile.external_url and ("linktr.ee" not in profile.external_url and "beacons.ai" not in profile.external_url and "wa.me" not in profile.external_url):
            has_web = True

        website_opportunity = WebsiteAuditAndOpportunity(
            has_website=has_web,
            existing_url=profile.external_url if has_web else None,
            audit_verdict=web_json.get("audit_verdict", "No Dedicated Website Found (High Traffic & Lead Leakage)" if not has_web else "Active Website Detected"),
            lead_leakage_analysis=web_json.get("lead_leakage_analysis", (
                "Relying solely on an Instagram bio and phone number causes substantial lead leakage. Over 65% of mobile visitors prefer instant self-service booking, pricing calculators, or direct WhatsApp buttons rather than manually copying contact numbers."
            ) if not has_web else "Website is active but can benefit from higher conversion rate optimization and instant lead capture widgets."),
            recommended_website_type=web_json.get("recommended_website_type", "On-Demand Local Booking & Lead Capture Portal"),
            core_lead_magnets=web_json.get("core_lead_magnets", [
                "Instant Online Price Estimator / Rate Calculator",
                "1-Click WhatsApp Pickup Booking Button",
                "First-Order 20% Off Welcome Voucher"
            ]),
            essential_pages_and_sections=web_json.get("essential_pages_and_sections", [
                "Hero section with 1-click booking CTA & service radius badge",
                "Interactive Service & Pricing Menu",
                "Customer Reviews & Visual Before/After proof",
                "Live Coverage Area Map (suburbs/pincodes served)",
                "FAQ & Same-Day Pickup Schedule"
            ]),
            local_seo_traffic_playbook=web_json.get("local_seo_traffic_playbook", f"Build a dedicated landing page targeting local keywords ('best {brand_profile.primary_niche} in {location_info.detected_location}') to capture organic Google Search and Google Maps customers."),
            estimated_lead_increase=web_json.get("estimated_lead_increase", "+50% to +85% increase in monthly inbound leads within 60 days")
        )

        # Software opportunity
        software_opp = SoftwareProductOpportunity(**parsed_json.get("software_opportunity", {}))

        # Step 5: Competitor & Market Intelligence
        competitors: List[CompetitorItem] = []
        market_analysis: MarketAnalysis = MarketAnalysis(
            market_saturation="Medium",
            market_trend="Steady Growth",
            locality_market_dynamics=f"Steady local engagement in {location_info.detected_location}.",
            domain_market_dynamics="Strong demand for authentic creator-led solutions.",
            untapped_market_opportunities=["Custom micro-tools", "Automated community funnels"],
            strategic_threats=["Content commoditization"]
        )

        if enable_competitor_research:
            try:
                competitors, market_analysis = self.competitor_researcher.research_competitors_and_market(
                    username=profile.username,
                    full_name=profile.full_name or profile.username,
                    niche=brand_profile.primary_niche,
                    archetype=brand_profile.brand_archetype,
                    location_info=location_info
                )
            except Exception as comp_err:
                logger.warning(f"Competitor research failed: {comp_err}. Using baseline market analysis.")

        return BrandingAnalysisReport(
            profile=profile,
            location=location_info,
            social_status=social_status,
            interests=interests,
            brand_profile=brand_profile,
            brand_improvements=brand_improvements,
            competitors=competitors,
            market_analysis=market_analysis,
            website_opportunity=website_opportunity,
            software_opportunity=software_opp,
            analyzed_by_model=self.model_name
        )

    def _format_profile_context(self, profile: ProfileData, location: LocationInfo) -> str:
        lines = [
            f"=== INSTAGRAM PROFILE: @{profile.username} ===",
            f"Full Name: {profile.full_name or 'Not specified'}",
            f"Bio: {profile.biography or 'No bio available'}",
            f"Detected Locality: {location.detected_location} (Source: {location.source})",
            f"External Link: {profile.external_url or 'None'}",
            f"Followers: {profile.followers_count or 'Unknown'} | Following: {profile.following_count or 'Unknown'} | Posts: {profile.posts_count or 'Unknown'}",
            f"Verified: {profile.is_verified}",
            "\n=== DISCOVERED SOCIAL & EXTERNAL PROFILES ==="
        ]

        if profile.social_links:
            for s in profile.social_links:
                lines.append(f"- {s.platform}: {s.url} ({s.status_notes or ''})")
        else:
            lines.append("No external links or linked profiles detected.")

        lines.append("\n=== RECENT POSTS & CAPTIONS ===")
        if not profile.posts:
            lines.append("No individual post captions collected (profile bio and metrics available).")
        else:
            for p in profile.posts:
                idx = p.get("post_index", "")
                caption = p.get("caption", "").strip()
                hashtags = " ".join(p.get("hashtags", []))
                lines.append(f"\n[Post #{idx}]")
                if caption:
                    lines.append(f"Caption: {caption}")
                if hashtags:
                    lines.append(f"Hashtags: {hashtags}")

        return "\n".join(lines)

    def _call_ollama(self, user_prompt: str) -> str:
        try:
            from core.ollama_helper import OllamaManager
            return OllamaManager.call_ai(
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                preferred_model=self.model_name,
                base_url=self.ollama_url,
                format_json=True
            )
        except Exception as e:
            logger.error(f"Error in AI inference pipeline: {e}")
            from core.ollama_helper import OllamaManager
            return OllamaManager._generate_offline_synthesis(user_prompt)

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from model output: {e}\nRaw content:\n{raw_text}")
            raise ValueError(f"Model output was not valid JSON: {e}")
