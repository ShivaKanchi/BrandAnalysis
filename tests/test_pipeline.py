import pytest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.models import (
    Citation,
    InterestItem,
    PersonalBrandProfile,
    BrandImprovementPlan,
    SocialStatusAnalysis,
    SocialLinkItem,
    LocationInfo,
    CompetitorItem,
    MarketAnalysis,
    WebsiteAuditAndOpportunity,
    SoftwareProductOpportunity,
    SoftwareProductRecommendation,
    ProfileData,
    BrandingAnalysisReport
)
from core.scraper import InstagramScraper
from core.social_scraper import SocialAndLocationScraper
from core.report_generator import ReportGenerator
from core.analyzer import BrandAnalyzer

def test_models_and_master_schema():
    cite = Citation(
        source_type="bio",
        content_excerpt="Host of @hubermanlab podcast. Neurobiology professor at Stanford.",
        post_index=None
    )
    interest = InterestItem(
        topic="Circadian Biology & Sleep Optimization",
        category="Health & Neuroscience",
        citations=[cite],
        confidence="High",
        confidence_reasoning="Stated directly in bio and referenced continuously in educational reels."
    )
    brand = PersonalBrandProfile(
        brand_archetype="The Scientific Educator",
        primary_niche="Neuroscience & Human Performance",
        secondary_niches=["Sleep Science", "Physical Fitness"],
        target_audience="High-performers, biohackers, and everyday individuals seeking protocol-based wellness.",
        content_pillars=["Morning sunlight protocols", "Cold exposure", "Dopamine regulation"],
        tone_and_voice="Authoritative, peer-reviewed, calm, pragmatic.",
        current_monetization_methods=["Podcast sponsorships", "Live events", "Newsletter"]
    )
    improvements = BrandImprovementPlan(
        funnel_and_conversion_improvements=["Add automated quiz funnel in bio"],
        content_and_messaging_improvements=["Create 60-second summary reels"],
        cross_platform_growth_improvements=["Scale YouTube clips"],
        quick_wins_under_30_days=["Revamp link-in-bio page"]
    )
    social_status = SocialStatusAnalysis(
        linked_socials=[SocialLinkItem(platform="YouTube", url="https://youtube.com/@hubermanlab")],
        cross_platform_presence_score="Strong Multi-Platform",
        social_ecosystem_overview="Massive YouTube and podcast syndication funneling into Instagram.",
        strengths=["Top 1% podcast reach"],
        vulnerabilities=["No owned community platform"]
    )
    location = LocationInfo(
        detected_location="Stanford, CA",
        source="Instagram Bio",
        confidence="High",
        details="Mentioned Stanford affiliation in bio"
    )
    comp = CompetitorItem(
        name="Peter Attia",
        competitor_type="Direct Domain Rival",
        location="Austin, TX",
        market_standing="Market Leader",
        estimated_pricing="$19/mo premium podcast",
        strengths=["Clinical depth", "Longevity authority"],
        weaknesses=["High paywall barrier"],
        ratings_or_reviews="High trust among medical peers",
        differentiator_vs_target="Huberman offers free access protocols while Attia focuses on clinical diagnostics."
    )
    mkt = MarketAnalysis(
        market_saturation="Medium",
        market_trend="Rapidly Growing",
        locality_market_dynamics="Strong wellness density in coastal hubs.",
        domain_market_dynamics="Preventative healthcare content is booming.",
        untapped_market_opportunities=["Interactive protocol app", "Biometric tracking integration"],
        strategic_threats=["Generic summary channels"]
    )
    rec = SoftwareProductRecommendation(
        product_name="ProtocolStack AI",
        product_type="Audience Utility / Micro-SaaS",
        core_value_proposition="Personalized daily circadian & habit tracking aligned with scientific protocols.",
        problem_it_solves="Listeners struggle to turn long episodes into daily routines.",
        target_buyers="Wellness enthusiasts.",
        suggested_monetization_model="$9.99/mo subscription",
        mvp_features=["Circadian timer", "Sunlight tracker", "Cold plunge logger"],
        feasibility_effort="Low"
    )
    so = SoftwareProductOpportunity(
        needs_software_product=True,
        confidence_in_verdict="High",
        verdict_summary="High-intent audience with complex daily routines that need tracking software.",
        recommended_product_ideas=[rec],
        why_not_reasons=[],
        existing_software_gaps=["No automated way to track protocols discussed on the show"]
    )

    prof = ProfileData(
        username="hubermanlab",
        full_name="Andrew Huberman",
        biography="Stanford Neurobiology professor. Host of Huberman Lab Podcast.",
        followers_count="6.2M",
        location_info=location,
        posts=[]
    )

    web = WebsiteAuditAndOpportunity(
        has_website=True,
        existing_url="https://hubermanlab.com",
        audit_verdict="Active Domain with High Conversion Potential",
        lead_leakage_analysis="Brand has website but lacks interactive habit calculator.",
        recommended_website_type="Science Education & Protocol Hub",
        core_lead_magnets=["Free Neural Sleep Guide"],
        essential_pages_and_sections=["Protocols", "Episodes", "Newsletter"],
        local_seo_traffic_playbook="Rank for neuroscience protocols.",
        estimated_lead_increase="+40% newsletter subscribers"
    )

    report = BrandingAnalysisReport(
        profile=prof,
        location=location,
        social_status=social_status,
        interests=[interest],
        brand_profile=brand,
        brand_improvements=improvements,
        competitors=[comp],
        market_analysis=mkt,
        website_opportunity=web,
        software_opportunity=so,
        analyzed_by_model="test-model"
    )

    assert report.profile.username == "hubermanlab"
    assert report.location.detected_location == "Stanford, CA"
    assert report.website_opportunity.has_website is True
    assert len(report.competitors) == 1
    assert report.competitors[0].name == "Peter Attia"
    assert len(report.brand_improvements.quick_wins_under_30_days) == 1

    # Test Markdown generation
    md = ReportGenerator.generate_markdown(report)
    assert "Master Personal Branding, Competitor & Software Intelligence" in md
    assert "Peter Attia" in md
    assert "Stanford, CA" in md

    # Test Single Master JSON serialization
    json_str = report.model_dump_json()
    assert "Peter Attia" in json_str
    assert "ProtocolStack AI" in json_str
    assert "funnel_and_conversion_improvements" in json_str

def test_location_resolution():
    scraper = SocialAndLocationScraper()
    # Test Bio detection
    loc1 = scraper.resolve_location("trainer_mike", biography="Private gym owner in Austin, TX 📍")
    assert "Austin" in loc1.detected_location
    assert loc1.source == "Instagram Bio"

    # Test User Override
    loc2 = scraper.resolve_location("digital_nomad", biography="Traveling the world", user_override="London, UK")
    assert loc2.detected_location == "London, UK"
    assert loc2.source == "User Specified"

def is_ollama_running():
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

@pytest.mark.skipif(not is_ollama_running(), reason="Ollama is not running on localhost:11434")
def test_live_ollama_analysis_with_improvements():
    """Live integration test against Ollama server with full pipeline."""
    analyzer = BrandAnalyzer()
    profile = ProfileData(
        username="austin_coffee_roaster",
        full_name="Craft Roasters Austin",
        biography="Specialty coffee roasting lab in Austin, TX. Single-origin beans and barista workshops. 📍 East Austin",
        external_url="https://linktr.ee/austincoffee",
        followers_count="24.5K",
        posts=[
            {
                "post_index": 1,
                "caption": "Fresh Ethiopia Yirgacheffe batch just dropped! Tasting notes of bergamot & jasmine. Grab a bag at our East Austin roastery. #specialtycoffee #austincoffee",
                "hashtags": ["#specialtycoffee", "#austincoffee"]
            }
        ]
    )

    report = analyzer.analyze_profile(profile, enable_competitor_research=True)
    assert report.profile.username == "austin_coffee_roaster"
    assert "Austin" in report.location.detected_location
    assert len(report.interests) > 0
    assert len(report.brand_improvements.quick_wins_under_30_days) > 0
    assert isinstance(report.competitors, list)
    assert report.market_analysis.market_saturation in ("Low", "Medium", "High", "Saturated")
    assert isinstance(report.software_opportunity.needs_software_product, bool)

    # Verify single master JSON dumps cleanly
    master_json = report.model_dump_json()
    assert "austin_coffee_roaster" in master_json
    assert "quick_wins_under_30_days" in master_json
