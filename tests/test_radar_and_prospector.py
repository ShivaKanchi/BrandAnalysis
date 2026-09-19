import pytest
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

def test_auto_prospector_instagram_extraction():
    prospector = AutoProspector(headless=True)
    # Test website social link extraction
    # aurum.fit was previously verified to have aurum.bangalore
    handle = prospector._extract_instagram_from_website("https://aurum.fit/")
    assert handle == "aurum.bangalore"
