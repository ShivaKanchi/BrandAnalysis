import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.models import (
    ShopifyStoreLead,
    AuditThresholds,
    ShopifyDetectionResult,
    ConsoleAuditResult,
    LighthouseAuditResult,
    PitchResult,
)
from backend.tools.scrapers.shopify_detector import (
    detect_shopify_from_html,
    detect_shopify,
)
from backend.tools.auditors.lighthouse_auditor import LighthouseAuditor
from backend.tools.scrapers.console_listener import ConsoleListener
from backend.tools.analyzers.pitch_generator import PitchGenerator


# ==============================================================================
# 1. Shopify Detection Heuristics Tests
# ==============================================================================

def test_shopify_detection_heuristics_positive():
    """Test HTML containing standard Shopify CDN, scripts, meta tags, and theme signatures."""
    # Snippet with CDN references and window.Shopify
    html_sample_1 = """
    <!DOCTYPE html>
    <html class="no-js" lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="generator" content="Shopify 2024">
        <link rel="stylesheet" href="https://cdn.shopify.com/s/files/1/0000/0001/t/12/assets/theme.css">
        <script>
            window.Shopify = { shop: "cool-brand.myshopify.com", currency: "USD" };
            Shopify.theme = {"name":"Dawn","id":133456789,"theme_store_id":887};
        </script>
        <script src="https://cdn.shopify.com/shopifycloud/boomerang/boomerang.min.js"></script>
    </head>
    <body>
        <h1>Welcome to Cool Brand</h1>
        <div id="shopify-section-header"></div>
    </body>
    </html>
    """
    res = detect_shopify_from_html(html_sample_1, base_url="https://coolbrand.com")
    assert res.is_shopify is True
    assert res.confidence >= 0.7
    assert any("cdn_shopify" in s for s in res.signals)
    assert "window.Shopify_object_detected" in res.signals
    assert "meta_generator_shopify" in res.signals
    assert res.theme_hints.get("theme_name") == "Dawn"
    assert res.theme_hints.get("theme_id") == "133456789"


def test_shopify_detection_heuristics_negative():
    """Test non-Shopify HTML (e.g. WooCommerce or generic Next.js application)."""
    generic_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="generator" content="WordPress 6.4.2; WooCommerce 8.5.1">
        <link rel="stylesheet" href="https://example.com/wp-content/themes/store/style.css">
        <script src="https://example.com/wp-includes/js/jquery/jquery.min.js"></script>
    </head>
    <body>
        <h1>Independent Boutique</h1>
    </body>
    </html>
    """
    res = detect_shopify_from_html(generic_html, base_url="https://example.com")
    assert res.is_shopify is False
    assert res.confidence < 0.4
    assert len(res.signals) == 0


def test_shopify_detection_network_probes_cart_json():
    """Test detect_shopify when /cart.json endpoint confirms Shopify backend."""
    mock_store_html = "<html><head><title>Minimal Store</title></head><body><h1>Hello</h1></body></html>"
    mock_cart_data = {"token": "a1b2c3d4", "item_count": 0, "currency": "USD", "items": []}

    with patch("requests.get") as mock_get:
        # First call: root URL returns bare HTML; Second call: /cart.json returns 200 with cart json
        resp_root = MagicMock()
        resp_root.status_code = 200
        resp_root.text = mock_store_html
        resp_root.url = "https://minimal-brand.com"
        resp_root.headers = {}

        resp_cart = MagicMock()
        resp_cart.status_code = 200
        resp_cart.text = '{"token": "a1b2c3d4", "item_count": 0, "currency": "USD", "items": []}'
        resp_cart.headers = {}

        mock_get.side_effect = [resp_root, resp_cart]

        result = detect_shopify("https://minimal-brand.com")
        assert result.is_shopify is True
        assert "cart_json_endpoint_confirmed" in result.signals
        assert result.metadata.get("cart_currency") == "USD"


def test_shopify_detection_network_probes_redirect_and_headers():
    """Test detect_shopify via myshopify.com redirect and custom Shopify headers."""
    with patch("requests.get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html><body>Redirected</body></html>"
        resp.url = "https://brand-store.myshopify.com"
        resp.headers = {
            "x-shopid": "12345678",
            "x-storefront-renderer-rendered": "1",
        }

        resp_cart = MagicMock()
        resp_cart.status_code = 404
        resp_cart.text = ""

        mock_get.side_effect = [resp, resp_cart]

        result = detect_shopify("https://brand-store.com")
        assert result.is_shopify is True
        assert "redirect_to_myshopify_domain" in result.signals
        assert "shopify_http_headers_present" in result.signals


# ==============================================================================
# 2. Audit Thresholds & Qualification Logic Tests
# ==============================================================================

def test_audit_thresholds_qualified_candidate():
    """Test a store with strong audience but slow speed and JS errors qualifies for revamp."""
    thresholds = AuditThresholds(
        min_followers=2500,
        max_lighthouse_score=60.0,
        min_console_errors=1,
    )

    lead = ShopifyStoreLead(
        domain="lagomskin.com",
        store_name="Lagom Skin",
        platform="shopify",
        is_shopify=True,
        followers=8400,
        lighthouse_performance=38.0,
        lighthouse_seo=75.0,
        console_errors_count=4,
        console_error_logs=["[Console Error]: Uncaught TypeError in bundle.js", "[404]: /assets/banner.jpg"],
        vision_score=52,
    )

    is_qualified = thresholds.evaluate(lead)
    assert is_qualified is True
    assert lead.qualified_for_revamp is True
    assert len(lead.qualification_reasons) >= 2
    assert any("followers" in r for r in lead.qualification_reasons)
    assert any("speed" in r or "performance" in r for r in lead.qualification_reasons)


def test_audit_thresholds_rejected_low_audience():
    """Test a store that is too small (e.g. 150 followers) with decent performance is disqualified."""
    thresholds = AuditThresholds(
        min_followers=2500,
        max_lighthouse_score=60.0,
        min_console_errors=1,
    )

    lead = ShopifyStoreLead(
        domain="newstore.com",
        store_name="New Store",
        platform="shopify",
        is_shopify=True,
        followers=200,
        lighthouse_performance=82.0,
        console_errors_count=0,
        vision_score=85,
    )

    is_qualified = thresholds.evaluate(lead)
    assert is_qualified is False
    assert lead.qualified_for_revamp is False


def test_audit_thresholds_disqualify_non_shopify():
    """Test a non-Shopify store is disqualified even with massive audience and speed debt."""
    thresholds = AuditThresholds()
    lead = ShopifyStoreLead(
        domain="bigbrand.org",
        store_name="Big Brand",
        platform="magento",
        is_shopify=False,
        followers=50000,
        lighthouse_performance=22.0,
        console_errors_count=8,
    )

    is_qualified = thresholds.evaluate(lead)
    assert is_qualified is False
    assert lead.qualified_for_revamp is False
    assert "Not a verified Shopify store." in lead.qualification_reasons


# ==============================================================================
# 3. Dual-Mode Lighthouse Auditor Tests
# ==============================================================================

def test_lighthouse_pagespeed_api_success():
    """Test Lighthouse auditor successfully parses Google PageSpeed API response."""
    auditor = LighthouseAuditor(api_key="test_dummy_key")

    mock_pagespeed_response = {
        "lighthouseResult": {
            "fetchTime": "2026-11-15T00:00:00Z",
            "categories": {
                "performance": {"score": 0.44},
                "accessibility": {"score": 0.88},
                "best-practices": {"score": 0.92},
                "seo": {"score": 0.90},
            },
            "audits": {
                "first-contentful-paint": {"displayValue": "2.8 s", "numericValue": 2800},
                "largest-contentful-paint": {"displayValue": "5.6 s", "numericValue": 5600},
                "cumulative-layout-shift": {"displayValue": "0.18", "numericValue": 0.182},
                "total-blocking-time": {"displayValue": "420 ms", "numericValue": 420},
                "speed-index": {"displayValue": "4.9 s", "numericValue": 4900},
            },
        }
    }

    with patch.object(auditor, "_query_pagespeed_api", return_value=LighthouseAuditResult(
        performance=44.0,
        accessibility=88.0,
        best_practices=92.0,
        seo=90.0,
        first_contentful_paint="2.8 s",
        largest_contentful_paint="5.6 s",
        cumulative_layout_shift=0.182,
        total_blocking_time="420 ms",
        speed_index="4.9 s",
        audit_source="google_pagespeed_api"
    )):
        result = auditor.audit("https://target-store.com")
        assert isinstance(result, LighthouseAuditResult)
        assert result.performance == 44.0
        assert result.accessibility == 88.0
        assert result.seo == 90.0
        assert result.largest_contentful_paint == "5.6 s"
        assert result.audit_source == "google_pagespeed_api"


def test_lighthouse_fallback_on_api_failure():
    """Test Lighthouse auditor falls back to synthetic Playwright metrics when PageSpeed API throws an error."""
    auditor = LighthouseAuditor(api_key="invalid_key")

    # Mock _query_pagespeed_api raising network error or returning None
    with patch.object(auditor, "_query_pagespeed_api", side_effect=Exception("Network timeout")):
        with patch.object(auditor, "_run_local_lighthouse_cli", return_value=None):
            result = auditor.audit("data:text/html,<html><head><title>Target Store</title></head><body><h1>Store</h1></body></html>")
            assert isinstance(result, LighthouseAuditResult)
            assert result.audit_source == "playwright_synthetic"
            assert result.performance >= 0.0
            assert result.seo >= 0.0
            assert result.first_contentful_paint is not None


# ==============================================================================
# 4. Playwright Console Listener Tests
# ==============================================================================

def test_console_listener_error_interception():
    """
    Test that ConsoleListener captures console.error, console.warn,
    uncaught exceptions, and 404 network responses.
    """
    import asyncio
    async def _run():
        listener = ConsoleListener(headless=True)
        data_html = (
            "data:text/html,<html><head><script>"
            "console.error('Triggered intentional test error: Cart script failed');"
            "console.warn('Triggered intentional test warning');"
            "setTimeout(() => { try { nonExistentFunction(); } catch(e) { console.error('Caught: ' + e.message); } }, 10);"
            "</script></head><body><h1>Playwright Test Store</h1></body></html>"
        )
        return await listener.audit_url(data_html, timeout_seconds=10)

    result = asyncio.run(_run())
    assert isinstance(result, ConsoleAuditResult)
    assert result.console_errors_count >= 1
    assert any("Triggered intentional test error" in log for log in result.console_error_logs)


def test_console_listener_invalid_url_graceful_handling():
    """Test ConsoleListener handles unreachable or malformed URLs gracefully without crashing."""
    import asyncio
    listener = ConsoleListener(headless=True)
    result = asyncio.run(listener.audit_url("http://non-existent-domain-xyz-12345.org", timeout_seconds=5))
    assert isinstance(result, ConsoleAuditResult)
    assert isinstance(result.console_errors_count, int)


# ==============================================================================
# 5. Pitch Generator Copy & Modernization Blueprint Tests
# ==============================================================================

def test_pitch_generator_template_output():
    """Test pitch generator creates formatted cold email, DM, and 3-point blueprint."""
    generator = PitchGenerator()
    lead = ShopifyStoreLead(
        domain="artisanleather.com",
        store_name="Artisan Leather Co.",
        platform="shopify",
        is_shopify=True,
        followers=14200,
        lighthouse_performance=41.0,
        console_errors_count=3,
        console_error_logs=["Uncaught TypeError: jQuery(...).slick is not a function", "404 Not Found: /cdn/app.min.js"],
        vision_critique="Outdated hero layout and low-contrast checkout buttons.",
        niche="Handmade Leather Goods",
    )

    pitch = generator.generate(lead)
    assert isinstance(pitch, PitchResult)
    assert pitch.subject_line
    assert len(pitch.subject_line) > 5

    # Verify cold email references exact metrics
    assert "artisanleather.com" in pitch.pitch_email or "Artisan Leather" in pitch.pitch_email
    assert "41" in pitch.pitch_email or "performance" in pitch.pitch_email.lower()

    # Verify Instagram / LinkedIn DM is punchy
    assert len(pitch.pitch_dm.split()) <= 150
    assert len(pitch.redesign_blueprint) == 3
