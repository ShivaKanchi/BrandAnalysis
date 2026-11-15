"""
tests/test_tools.py
Comprehensive unit tests for backend models and segregated tools:
- ShopifyStoreLead, AuditThresholds, WorkflowNodeState
- shopify_detector (HTML detection, theme hints, confidence score)
- social_scraper (link extraction, metric parsing)
- maps_harvester
- console_listener
- lighthouse_auditor (synthetic metrics fallback)
- vision_ux_auditor (heuristic UX audit)
- pitch_generator (personalized email, short DM, 3-point blueprint)
- brand_analyzer (heuristic analysis)
- competitor_analyzer
- problem_radar
- lead_store (persistence and CSV export)
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.models import (
    ShopifyStoreLead,
    AuditThresholds,
    WorkflowNodeState,
    ShopifyDetectionResult,
    ConsoleAuditResult,
    LighthouseAuditResult,
    VisionAuditResult,
    PitchResult
)
from backend.tools.scrapers.shopify_detector import detect_shopify_from_html
from backend.tools.scrapers.social_scraper import extract_social_links, _parse_count_str
from backend.tools.scrapers.console_listener import ConsoleListener
from backend.tools.auditors.lighthouse_auditor import LighthouseAuditor
from backend.tools.auditors.vision_ux_auditor import VisionUXAuditor
from backend.tools.analyzers.pitch_generator import generate_revamp_pitch, PitchGenerator
from backend.tools.analyzers.brand_analyzer import BrandAnalyzer
from backend.tools.analyzers.competitor_analyzer import CompetitorAnalyzer
from backend.tools.analyzers.problem_radar import SoftwareProblemRadar
from backend.tools.storage.lead_store import LeadStore


class TestBackendModels(unittest.TestCase):
    def test_shopify_store_lead_defaults(self):
        lead = ShopifyStoreLead(domain="teststore.com")
        self.assertEqual(lead.domain, "teststore.com")
        self.assertEqual(lead.platform, "shopify")
        self.assertTrue(lead.is_shopify)
        self.assertEqual(lead.console_errors_count, 0)
        self.assertFalse(lead.qualified_for_revamp)

    def test_audit_thresholds_qualification(self):
        thresholds = AuditThresholds(min_followers=2500, max_lighthouse_score=60.0, min_console_errors=1)

        # Qualified Lead: high followers, low lighthouse, active console errors
        qualified_lead = ShopifyStoreLead(
            domain="brandco.com",
            followers=12000,
            lighthouse_performance=42.0,
            console_errors_count=3,
            console_error_logs=["Uncaught ReferenceError: jQuery is not defined"]
        )
        is_qual = thresholds.evaluate(qualified_lead)
        self.assertTrue(is_qual)
        self.assertTrue(qualified_lead.qualified_for_revamp)
        self.assertTrue(any("audience" in r.lower() for r in qualified_lead.qualification_reasons))

        # Unqualified Lead: high performance, no errors
        unqualified_lead = ShopifyStoreLead(
            domain="perfectstore.com",
            followers=5000,
            lighthouse_performance=95.0,
            console_errors_count=0
        )
        is_qual_2 = thresholds.evaluate(unqualified_lead)
        self.assertFalse(is_qual_2)
        self.assertFalse(unqualified_lead.qualified_for_revamp)

    def test_workflow_node_state(self):
        node = WorkflowNodeState(
            id="detect_shopify",
            label="Shopify Detection",
            status="running",
            duration_ms=120.5,
            data={"is_shopify": True}
        )
        self.assertEqual(node.status, "running")
        self.assertEqual(node.data["is_shopify"], True)


class TestShopifyDetector(unittest.TestCase):
    def test_detect_shopify_positive(self):
        shopify_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Shopify 2.0">
            <script>window.Shopify = {shop: "test.myshopify.com", theme: {"name": "Dawn", "id": 12345678}};</script>
            <link rel="stylesheet" href="https://cdn.shopify.com/s/files/1/0000/assets/theme.css">
        </head>
        <body><h1>Shopify Store</h1></body>
        </html>
        """
        result = detect_shopify_from_html(shopify_html, base_url="https://test.com")
        self.assertTrue(result.is_shopify)
        self.assertGreaterEqual(result.confidence, 0.5)
        self.assertIn("meta_generator_shopify", result.signals)
        self.assertIn("window.Shopify_object_detected", result.signals)
        self.assertEqual(result.theme_hints.get("theme_name"), "Dawn")

    def test_detect_shopify_negative(self):
        wordpress_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="WordPress 6.4">
        </head>
        <body><h1>Personal Blog</h1></body>
        </html>
        """
        result = detect_shopify_from_html(wordpress_html, base_url="https://blog.com")
        self.assertFalse(result.is_shopify)
        self.assertLess(result.confidence, 0.4)


class TestSocialScraper(unittest.TestCase):
    def test_parse_count_str(self):
        self.assertEqual(_parse_count_str("1.5K"), 1500)
        self.assertEqual(_parse_count_str("2M"), 2_000_000)
        self.assertEqual(_parse_count_str("450"), 450)
        self.assertEqual(_parse_count_str("12,300"), 12300)

    def test_extract_social_links(self):
        html = """
        <footer>
            <a href="https://instagram.com/mybrand">Follow us on IG</a>
            <a href="https://tiktok.com/@mybrand_tiktok">TikTok</a>
            <a href="https://youtube.com/c/mybrand">YouTube</a>
        </footer>
        """
        links = extract_social_links(html)
        platforms = [l["platform"] for l in links]
        self.assertIn("Instagram", platforms)
        self.assertIn("TikTok", platforms)
        self.assertIn("YouTube", platforms)


class TestConsoleListener(unittest.TestCase):
    def test_http_fallback_audit(self):
        listener = ConsoleListener()
        res = listener._http_fallback_audit("https://example.com")
        self.assertIsInstance(res, ConsoleAuditResult)
        self.assertIsInstance(res.console_error_logs, list)


class TestLighthouseAuditor(unittest.TestCase):
    def test_synthetic_metrics(self):
        auditor = LighthouseAuditor()
        res = auditor._run_synthetic_metrics("https://example.com")
        self.assertIsInstance(res, LighthouseAuditResult)
        self.assertGreater(res.performance, 0.0)
        self.assertGreater(res.seo, 0.0)
        self.assertEqual(res.audit_source, "playwright_synthetic")


class TestVisionUXAuditor(unittest.TestCase):
    def test_heuristic_ux_audit(self):
        auditor = VisionUXAuditor()
        res = auditor._heuristic_ux_audit("https://example.com")
        self.assertIsInstance(res, VisionAuditResult)
        self.assertGreaterEqual(res.vision_score, 30)
        self.assertLessEqual(res.vision_score, 100)
        self.assertGreaterEqual(len(res.bad_patterns), 1)
        self.assertGreaterEqual(len(res.revamp_improvements), 1)


class TestPitchGenerator(unittest.TestCase):
    def test_pitch_generator(self):
        lead = ShopifyStoreLead(
            domain="modernapparel.com",
            store_name="Modern Apparel",
            niche="Streetwear",
            followers=25000,
            lighthouse_performance=35.0,
            console_errors_count=2,
            console_error_logs=["Failed to load resource: 404 /assets/drawer.js"]
        )
        pitch = generate_revamp_pitch(lead)
        self.assertIsInstance(pitch, PitchResult)
        self.assertIn("modernapparel.com", pitch.subject_line)
        self.assertIn("35", pitch.pitch_email)
        self.assertIn("Modern Apparel", pitch.pitch_dm)
        self.assertEqual(len(pitch.redesign_blueprint), 3)


class TestBrandAnalyzer(unittest.TestCase):
    def test_heuristic_brand_analysis(self):
        from backend.models import ProfileData
        analyzer = BrandAnalyzer()
        profile = ProfileData(
            username="fitbrand",
            full_name="Fit Brand Official",
            biography="Premium athletic apparel designed for everyday performance.",
            external_url="https://fitbrand.com",
            followers_count="54000"
        )
        report = analyzer.analyze_profile(profile)
        self.assertEqual(report.profile.username, "fitbrand")
        self.assertTrue(report.website_opportunity.has_website)
        self.assertTrue(report.software_opportunity.needs_software_product)
        self.assertGreaterEqual(len(report.brand_improvements.quick_wins_under_30_days), 1)


class TestCompetitorAndProblemRadar(unittest.TestCase):
    def test_competitor_analyzer(self):
        ca = CompetitorAnalyzer()
        res = ca.analyze("GlowSkin", "Organic Skincare", "Miami")
        self.assertEqual(res.target_brand, "GlowSkin")
        self.assertGreaterEqual(len(res.competitors), 1)

    def test_problem_radar(self):
        radar = SoftwareProblemRadar()
        report = radar.run_radar()
        self.assertIn("Problem & Micro-SaaS Radar", report.report_title)
        self.assertGreaterEqual(len(report.top_problems), 1)
        self.assertTrue(report.top_problems[0].recommended_microsaas.product_name_concept)


class TestLeadStore(unittest.TestCase):
    def test_save_and_export_csv(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(storage_dir=Path(tmpdir))
            lead = ShopifyStoreLead(
                domain="shoestore.com",
                store_name="Shoe Store",
                followers=8000,
                lighthouse_performance=48.0,
                console_errors_count=1,
                qualified_for_revamp=True,
                pitch_email="Hello Team...",
                pitch_dm="Hey Shoe Store!"
            )
            store.save_lead(lead)

            retrieved = store.get_lead("shoestore.com")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.domain, "shoestore.com")
            self.assertTrue(retrieved.qualified_for_revamp)

            csv_data = store.export_csv()
            self.assertIn("shoestore.com", csv_data)
            self.assertIn("Shoe Store", csv_data)


if __name__ == "__main__":
    unittest.main()
