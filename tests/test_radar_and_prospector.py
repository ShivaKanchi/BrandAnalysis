import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.models import DiscoveredLeadItem, LeadProspectingReport, SoftwareProblemRadarReport
from core.problem_radar import SoftwareProblemRadar
from core.auto_prospector import AutoProspector

def test_problem_radar_data_fetching():
    radar = SoftwareProblemRadar()
    hn_items = radar._fetch_hacker_news(limit=3)
    devto_items = radar._fetch_devto(limit=3)
    news_items = radar._fetch_tech_news(limit=3)
    reddit_items = radar._fetch_reddit_discussions(limit=3)

    assert isinstance(hn_items, list)
    assert len(hn_items) > 0, "Hacker News Algolia API should return items"
    assert isinstance(devto_items, list)
    assert len(devto_items) > 0, "Dev.to API should return items"
    assert isinstance(news_items, list)
    assert len(news_items) > 0, "Google News RSS should return items"
    assert isinstance(reddit_items, list)
    assert len(reddit_items) > 0, "Reddit items via news aggregator should return items"

def test_problem_radar_synthesis():
    radar = SoftwareProblemRadar()
    report = radar.run_radar_analysis(max_items_per_source=2)
    assert isinstance(report, SoftwareProblemRadarReport)
    assert len(report.top_problems) > 0
    first_prob = report.top_problems[0]
    assert first_prob.problem_title
    assert first_prob.category
    assert first_prob.recommended_microsaas.product_name_concept
    assert len(first_prob.recommended_microsaas.mvp_features) > 0

from unittest.mock import patch, MagicMock
from core.storage import StorageManager

def test_auto_prospector_intent_evaluation():
    prospector = AutoProspector(headless=True)
    
    # 1. High-Intent Lead with real customer foot traffic
    high_lead = {
        "name": "Apex Fitness Hub",
        "rating": "4.8",
        "reviews": "142",
        "phone": "+1 555-1234",
        "address": "Downtown"
    }
    intent, signals, angle = prospector._evaluate_lead_intent(
        place=high_lead,
        ig_handle="apexfitness",
        website="https://apexfitness.com"
    )
    assert intent == "High Intent"
    assert any("High Foot Traffic" in s for s in signals)
    assert any("Dedicated Domain Funnel" in s for s in signals)

    # 2. Promising Lead with missing custom website funnel (linktree / wa.me)
    promising_lead = {
        "name": "Urban Yoga Loft",
        "rating": "4.5",
        "reviews": "28",
        "phone": "+1 555-5678"
    }
    intent2, signals2, angle2 = prospector._evaluate_lead_intent(
        place=promising_lead,
        ig_handle="urbanyoga",
        website="https://linktr.ee/urbanyoga"
    )
    assert intent2 == "Promising"
    assert any("Missing Custom Website" in s for s in signals2)
    assert "booking funnel" in angle2.lower()

    # 3. Ghost / Fake profile risk (0 reviews, no website, unverified)
    ghost_lead = {
        "name": "Phantom Gym",
        "rating": None,
        "reviews": "0"
    }
    intent3, signals3, angle3 = prospector._evaluate_lead_intent(
        place=ghost_lead,
        ig_handle=None,
        website=None
    )
    assert intent3 == "Low Intent / Ghost"
    assert any("Low/Zero Reviews" in s for s in signals3)

def test_lead_registry_deduplication():
    # Clear registry for clean test isolation
    StorageManager.clear_leads_registry()
    test_leads = [
        DiscoveredLeadItem(
            business_name="Test Apex Gym",
            address_or_location="Kandivali, Mumbai",
            website="https://testapexgym.com",
            instagram_handle="testapexgym",
            rating="4.8",
            review_count="95",
            lead_intent_score="High Intent"
        )
    ]
    saved_count = StorageManager.save_leads_batch(test_leads, query="Gyms in Kandivali", location="Kandivali")
    assert saved_count >= 1

    # Check that lead is recognized as registered
    assert StorageManager.is_lead_registered("Test Apex Gym", location="Kandivali")
    assert StorageManager.is_lead_registered("Test Apex Gym")
    assert StorageManager.is_lead_registered("Other Name", ig_handle="testapexgym")
    StorageManager.clear_leads_registry()

def test_query_variant_generation():
    prospector = AutoProspector(headless=True)
    variants = prospector._generate_query_variants("Gyms", "Kandivali, Mumbai")
    assert len(variants) >= 4
    assert any("West" in v for v in variants)
    assert any("Fitness" in v or "Training" in v or "CrossFit" in v for v in variants)

def test_auto_prospector_instagram_extraction():
    prospector = AutoProspector(headless=True)
    mock_html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@context": "https://schema.org", "sameAs": ["https://www.instagram.com/mockbrand_official/"]}
        </script>
      </head>
      <body>
        <a href="https://www.instagram.com/mockbrand_official/">Follow us on IG</a>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = mock_html

    with patch("requests.get", return_value=mock_resp):
        handle = prospector._extract_instagram_from_website("https://mockbrand.com")
        assert handle == "mockbrand_official"

