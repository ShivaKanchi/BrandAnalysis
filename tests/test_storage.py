import json
import pytest
from pathlib import Path
from core.models import (
    Citation, ProfileData, LocationInfo, SocialStatusAnalysis, InterestItem,
    PersonalBrandProfile, BrandImprovementPlan, CompetitorItem, MarketAnalysis,
    WebsiteAuditAndOpportunity, SoftwareProductOpportunity, SoftwareProductRecommendation,
    BrandingAnalysisReport
)
from core.storage import StorageManager

@pytest.fixture
def sample_report():
    loc = LocationInfo(detected_location="Austin, TX", source="Instagram Bio", confidence="High")
    prof = ProfileData(
        username="test_coffee_guru",
        full_name="Austin Coffee Guru",
        biography="Specialty coffee in Austin, TX.",
        followers_count="15.2K",
        location_info=loc,
        posts=[]
    )
    brand = PersonalBrandProfile(
        brand_archetype="The Specialized Expert",
        primary_niche="Specialty Coffee & Brewing Science",
        target_audience="Coffee enthusiasts, home baristas, and specialty coffee lovers",
        content_pillars=["Pour over guides", "Bean roasting", "Espresso dialing"],
        tone_and_voice="Educational, accessible, passion-driven",
        current_monetization_methods=["Course sales", "Coffee beans"]
    )
    so = SoftwareProductOpportunity(
        needs_software_product=True,
        confidence_in_verdict="High",
        verdict_summary="Audience needs brew timer and bean tasting diary.",
        recommended_product_ideas=[
            SoftwareProductRecommendation(
                product_name="BrewLog AI",
                product_type="Micro-SaaS",
                core_value_proposition="Smart recipe timer & roast logger.",
                problem_it_solves="Dialing in espresso grind settings.",
                target_buyers="Home baristas",
                suggested_monetization_model="$4.99/mo",
                mvp_features=["Recipe calculator", "Extraction timer"],
                feasibility_effort="Low"
            )
        ]
    )
    web = WebsiteAuditAndOpportunity(
        has_website=False,
        audit_verdict="Missing Website",
        lead_leakage_analysis="Losing potential leads without an owned website.",
        recommended_website_type="Coffee Academy & Lead Engine",
        core_lead_magnets=["Free Grind Size Chart"],
        essential_pages_and_sections=["Brew Guides", "Shop"],
        local_seo_traffic_playbook="Rank for best coffee Austin",
        estimated_lead_increase="+50% leads"
    )
    return BrandingAnalysisReport(
        profile=prof,
        location=loc,
        social_status=SocialStatusAnalysis(
            cross_platform_presence_score="Moderate",
            social_ecosystem_overview="Instagram focused."
        ),
        interests=[
            InterestItem(
                topic="Espresso Extraction",
                category="Coffee",
                citations=[Citation(source_type="bio", content_excerpt="Specialty coffee in Austin, TX.")],
                confidence="High",
                confidence_reasoning="Directly stated in bio"
            )
        ],
        brand_profile=brand,
        brand_improvements=BrandImprovementPlan(
            funnel_and_conversion_improvements=["Add automated quiz funnel in bio"],
            content_and_messaging_improvements=["Create brew guides"],
            cross_platform_growth_improvements=["Scale YouTube shorts"],
            quick_wins_under_30_days=["Launch website"]
        ),
        competitors=[],
        market_analysis=MarketAnalysis(
            market_saturation="Medium",
            market_trend="Rapidly Growing",
            locality_market_dynamics="High density of specialty coffee roasters.",
            domain_market_dynamics="Home brewing popularity is surging.",
            untapped_market_opportunities=["Smart brew timer"],
            strategic_threats=["Commercial chains"]
        ),
        website_opportunity=web,
        software_opportunity=so,
        analyzed_by_model="test-gemma"
    )

def test_storage_manager_auto_save_and_retrieve(sample_report, tmp_path, monkeypatch):
    # Route storage to temporary directory
    monkeypatch.setattr(StorageManager, "get_reports_dir", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(StorageManager, "get_index_path", classmethod(lambda cls: tmp_path / "intelligence_index.json"))

    # 1. Auto save report
    paths = StorageManager.auto_save_report(sample_report)
    assert paths["json"].exists()
    assert paths["markdown"].exists()

    # 2. Verify index file was created
    index_path = tmp_path / "intelligence_index.json"
    assert index_path.exists()
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    assert "test_coffee_guru" in index_data
    assert index_data["test_coffee_guru"]["latest_analysis"]["locality"] == "Austin, TX"

    # 3. List saved profiles
    saved = StorageManager.list_saved_profiles()
    assert len(saved) == 1
    assert saved[0]["username"] == "test_coffee_guru"
    assert saved[0]["locality"] == "Austin, TX"

    # 4. Load report by path
    loaded = StorageManager.load_report_by_path(str(paths["json"]))
    assert loaded is not None
    assert loaded.profile.username == "test_coffee_guru"
    assert loaded.website_opportunity.has_website is False

    # 5. Load latest report
    latest_loaded = StorageManager.load_latest_report("test_coffee_guru")
    assert latest_loaded is not None
    assert latest_loaded.software_opportunity.recommended_product_ideas[0].product_name == "BrewLog AI"
