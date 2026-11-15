"""
backend/tools/scrapers/shopify_detector.py
Verifies whether a given store URL is powered by Shopify.
Detects:
- cdn.shopify.com in HTML / scripts / stylesheet links
- window.Shopify / Shopify.theme in JavaScript
- /cart.json endpoint response signatures
- myshopify.com HTTP redirects or headers
- generator meta tags matching Shopify
Returns:
- is_shopify: bool
- theme_hints: Dict[str, Any]
- metadata: Dict[str, Any]
"""

import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse, urljoin

try:
    import httpx
except ImportError:
    httpx = None

try:
    import requests
except ImportError:
    requests = None

from backend.models import ShopifyDetectionResult

logger = logging.getLogger("BrandAnalysis.ShopifyDetector")

# Regular expressions for detection
CDN_REGEX = re.compile(r"cdn\.shopify\.com", re.IGNORECASE)
WINDOW_SHOPIFY_REGEX = re.compile(r"(?:window\.)?Shopify\s*=\s*\{|var\s+Shopify\s*=|Shopify\.theme\s*=", re.IGNORECASE)
THEME_NAME_REGEX = re.compile(r'["\']name["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
THEME_ID_REGEX = re.compile(r'["\']theme_store_id["\']\s*:\s*(\d+)|["\']id["\']\s*:\s*(\d{8,})', re.IGNORECASE)
META_GENERATOR_REGEX = re.compile(r'<meta[^>]*name=["\']generator["\'][^>]*content=["\']([^"\']*shopify[^"\']*)["\']', re.IGNORECASE)
BOOMR_REGEX = re.compile(r"shopify-boomerang|cdn\.shopify\.com\/shopifycloud", re.IGNORECASE)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _normalize_url(url: str) -> str:
    """Ensure URL has https:// protocol and standard format."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def detect_shopify_from_html(html: str, base_url: str = "") -> ShopifyDetectionResult:
    """
    Synchronously evaluate raw HTML for Shopify fingerprints.
    Useful for offline testing, mocked tests, or when HTML was already scraped.
    """
    signals: List[str] = []
    theme_hints: Dict[str, Any] = {}
    confidence = 0.0

    if not html:
        return ShopifyDetectionResult(is_shopify=False, confidence=0.0, signals=[], theme_hints={}, metadata={})

    # 1. Meta generator tag
    meta_match = META_GENERATOR_REGEX.search(html)
    if meta_match:
        signals.append("meta_generator_shopify")
        confidence += 0.4
        theme_hints["generator"] = meta_match.group(1).strip()

    # 2. cdn.shopify.com references
    cdn_matches = len(CDN_REGEX.findall(html))
    if cdn_matches > 0:
        signals.append(f"cdn_shopify_assets_found({cdn_matches}_references)")
        confidence += min(0.4, 0.1 * cdn_matches)

    # 3. window.Shopify script object
    if WINDOW_SHOPIFY_REGEX.search(html):
        signals.append("window.Shopify_object_detected")
        confidence += 0.4

    # 4. Boomerang / analytics
    if BOOMR_REGEX.search(html):
        signals.append("shopify_cloud_telemetry")
        confidence += 0.2

    # 5. Extract Theme Hints
    # Look for Shopify.theme = {"name":"...","id":...} or theme: {"name":"...","id":...}
    theme_block_match = re.search(r"(?:Shopify\.theme\s*=\s*|theme\s*:\s*)(\{[^;}]+\})", html)
    if theme_block_match:
        try:
            theme_json_str = theme_block_match.group(1)
            theme_hints["raw_theme_js"] = theme_json_str[:200]
            name_m = THEME_NAME_REGEX.search(theme_json_str)
            if name_m:
                theme_hints["theme_name"] = name_m.group(1)
            id_m = THEME_ID_REGEX.search(theme_json_str)
            if id_m:
                theme_hints["theme_id"] = id_m.group(1) or id_m.group(2)
        except Exception:
            pass

    if "theme_name" not in theme_hints:
        theme_name_loose = re.search(r'["\']theme["\']\s*:\s*\{[^}]*["\']name["\']\s*:\s*["\']([^"\']+)["\']', html)
        if theme_name_loose:
            theme_hints["theme_name"] = theme_name_loose.group(1)

    # Look for theme asset paths like /cdn/shop/t/12/assets/
    asset_theme_match = re.search(r"\/cdn\/shop\/t\/(\d+)\/assets\/", html)
    if asset_theme_match:
        theme_hints["theme_version_id"] = asset_theme_match.group(1)
        signals.append("shopify_cdn_theme_asset_structure")
        confidence += 0.2

    confidence = min(1.0, confidence)
    is_shopify = confidence >= 0.4 or len(signals) >= 2 or "window.Shopify_object_detected" in signals

    return ShopifyDetectionResult(
        is_shopify=is_shopify,
        confidence=round(confidence, 2),
        signals=signals,
        theme_hints=theme_hints,
        metadata={"base_url": base_url, "html_length": len(html)}
    )


def detect_shopify(url: str, timeout: int = 4) -> ShopifyDetectionResult:
    """
    Synchronously verify if a URL is a Shopify store.
    Probes root HTML, HTTP headers, redirects, and /cart.json endpoint.
    """
    norm_url = _normalize_url(url)
    signals: List[str] = []
    theme_hints: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {"requested_url": norm_url}
    confidence = 0.0

    parsed = urlparse(norm_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Probe the main store URL
    try:
        resp = None
        if requests is not None:
            resp = requests.get(norm_url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
            status_code = resp.status_code
            headers = dict(resp.headers)
            final_url = str(resp.url)
            text = resp.text
        elif httpx is not None:
            with httpx.Client(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as client:
                resp = client.get(norm_url)
                status_code = resp.status_code
                headers = dict(resp.headers)
                final_url = str(resp.url)
                text = resp.text
        else:
            import urllib.request
            req = urllib.request.Request(norm_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.status
                headers = dict(response.headers)
                final_url = response.geturl()
                text = response.read().decode("utf-8", errors="ignore")

        metadata["final_url"] = final_url
        metadata["status_code"] = status_code

        # Check for myshopify.com in redirects
        if ".myshopify.com" in final_url.lower():
            signals.append("redirect_to_myshopify_domain")
            confidence += 0.6
            theme_hints["myshopify_domain"] = final_url

        # Check Shopify specific HTTP response headers
        header_keys = [k.lower() for k in headers.keys()]
        if any("shopify" in k or k in ("x-shopid", "x-sorting-hat-shopid", "x-storefront-renderer-rendered") for k in header_keys):
            signals.append("shopify_http_headers_present")
            confidence += 0.5
            for k, v in headers.items():
                if "shopify" in k.lower() or "shopid" in k.lower():
                    metadata[f"header_{k}"] = v

        # Parse HTML signals
        html_result = detect_shopify_from_html(text, base_url=norm_url)
        signals.extend(html_result.signals)
        theme_hints.update(html_result.theme_hints)
        confidence += html_result.confidence

    except Exception as e:
        logger.warning(f"Failed to fetch {norm_url}: {e}")
        metadata["fetch_error"] = str(e)

    # 2. Probe /cart.json endpoint (Distinctive Shopify standard JSON API)
    cart_url = urljoin(base_domain, "/cart.json")
    try:
        cart_resp = None
        if requests is not None:
            cart_resp = requests.get(cart_url, headers=DEFAULT_HEADERS, timeout=min(8, timeout), allow_redirects=True)
            cart_status = cart_resp.status_code
            cart_text = cart_resp.text
        elif httpx is not None:
            with httpx.Client(headers=DEFAULT_HEADERS, timeout=min(8, timeout), follow_redirects=True) as client:
                cart_resp = client.get(cart_url)
                cart_status = cart_resp.status_code
                cart_text = cart_resp.text
        else:
            cart_status = 0
            cart_text = ""

        if cart_status == 200:
            try:
                cart_data = json.loads(cart_text)
                if isinstance(cart_data, dict) and ("token" in cart_data or "item_count" in cart_data or "items" in cart_data):
                    signals.append("cart_json_endpoint_confirmed")
                    confidence += 0.6
                    metadata["cart_item_count"] = cart_data.get("item_count")
                    metadata["cart_currency"] = cart_data.get("currency")
                    if cart_data.get("currency"):
                        theme_hints["currency"] = cart_data.get("currency")
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Cart probe error: {e}")

    confidence = min(1.0, confidence)
    is_shopify = confidence >= 0.4 or "cart_json_endpoint_confirmed" in signals or "redirect_to_myshopify_domain" in signals or len(signals) >= 2

    return ShopifyDetectionResult(
        is_shopify=is_shopify,
        confidence=round(confidence, 2),
        signals=list(set(signals)),
        theme_hints=theme_hints,
        metadata=metadata
    )


async def detect_shopify_async(url: str, timeout: int = 15) -> ShopifyDetectionResult:
    """
    Asynchronously verify if a URL is a Shopify store using httpx.
    Falls back to synchronous detect_shopify if httpx async is not active.
    """
    if httpx is None:
        return detect_shopify(url, timeout=timeout)

    norm_url = _normalize_url(url)
    signals: List[str] = []
    theme_hints: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {"requested_url": norm_url}
    confidence = 0.0

    parsed = urlparse(norm_url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"

    try:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(norm_url)
            final_url = str(resp.url)
            metadata["final_url"] = final_url
            metadata["status_code"] = resp.status_code

            if ".myshopify.com" in final_url.lower():
                signals.append("redirect_to_myshopify_domain")
                confidence += 0.6
                theme_hints["myshopify_domain"] = final_url

            header_keys = [k.lower() for k in resp.headers.keys()]
            if any("shopify" in k or k in ("x-shopid", "x-sorting-hat-shopid") for k in header_keys):
                signals.append("shopify_http_headers_present")
                confidence += 0.5

            html_result = detect_shopify_from_html(resp.text, base_url=norm_url)
            signals.extend(html_result.signals)
            theme_hints.update(html_result.theme_hints)
            confidence += html_result.confidence

            # Probe cart.json
            try:
                cart_url = urljoin(base_domain, "/cart.json")
                cart_resp = await client.get(cart_url)
                if cart_resp.status_code == 200:
                    cart_data = cart_resp.json()
                    if isinstance(cart_data, dict) and ("token" in cart_data or "items" in cart_data):
                        signals.append("cart_json_endpoint_confirmed")
                        confidence += 0.6
                        if cart_data.get("currency"):
                            theme_hints["currency"] = cart_data.get("currency")
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"Async fetch failed for {norm_url}: {e}")
        # Try synchronous fallback
        return detect_shopify(url, timeout=timeout)

    confidence = min(1.0, confidence)
    is_shopify = confidence >= 0.4 or "cart_json_endpoint_confirmed" in signals or len(signals) >= 2

    return ShopifyDetectionResult(
        is_shopify=is_shopify,
        confidence=round(confidence, 2),
        signals=list(set(signals)),
        theme_hints=theme_hints,
        metadata=metadata
    )
