"""
backend/tools/scrapers/console_listener.py
Playwright Async Console & Network Error Listener.
Loads target storefronts and intercepts:
- page.on('console'): JavaScript warnings, syntax errors, and runtime console.error calls
- page.on('pageerror'): Uncaught JavaScript exceptions and unhandled promise rejections
- page.on('response'): HTTP 4xx/5xx responses (especially 404 broken script/asset requests)
- page.on('requestfailed'): Failed network requests (CORS blocks, aborts, missing assets)
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin

try:
    import requests
except ImportError:
    requests = None

from backend.models import ConsoleAuditResult

logger = logging.getLogger("BrandAnalysis.ConsoleListener")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class ConsoleListener:
    """
    Playwright-based runtime listener for monitoring storefront frontend errors.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def audit_url(self, url: str, timeout_seconds: int = 25) -> ConsoleAuditResult:
        """
        Loads the store in headless Chromium, intercepts runtime JS logs & network 404s,
        and returns a structured ConsoleAuditResult.
        """
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("data:") or url.startswith("file://")):
            url = "https://" + url

        try:
            import playwright
        except ImportError:
            return self._http_fallback_audit(url)

        try:
            return await asyncio.to_thread(self._run_sync_playwright_audit, url, timeout_seconds)
        except Exception as e:
            logger.warning(f"Playwright execution failed or timed out: {e}. Executing HTTP fallback auditor...")
            return self._http_fallback_audit(url)

    def _run_sync_playwright_audit(self, url: str, timeout_seconds: int = 25) -> ConsoleAuditResult:
        error_logs: List[str] = []
        warning_logs: List[str] = []
        uncaught_exceptions: List[str] = []
        failed_requests: List[str] = []
        detailed_events: List[Dict[str, Any]] = []

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-software-rasterizer"
                ]
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1440, "height": 900},
                ignore_https_errors=True
            )
            page = context.new_page()

            # 1. Listen for console events
            def on_console(msg):
                msg_type = msg.type
                text = msg.text
                location = msg.location
                loc_str = f" ({location.get('url', '')}:{location.get('lineNumber', '')})" if location else ""

                if msg_type in ("error", "assert"):
                    clean_msg = f"[Console Error]{loc_str}: {text}"
                    error_logs.append(clean_msg)
                    detailed_events.append({"type": "console_error", "text": text, "location": location})
                elif msg_type == "warning":
                    clean_msg = f"[Console Warning]{loc_str}: {text}"
                    warning_logs.append(clean_msg)
                    detailed_events.append({"type": "console_warning", "text": text, "location": location})

            page.on("console", on_console)

            # 2. Listen for uncaught page exceptions
            def on_page_error(err):
                err_msg = f"[Uncaught Exception]: {str(err)}"
                uncaught_exceptions.append(err_msg)
                error_logs.append(err_msg)
                detailed_events.append({"type": "uncaught_exception", "text": str(err)})

            page.on("pageerror", on_page_error)

            # 3. Listen for failed responses (404 Not Found, 500 Internal Error)
            def on_response(response):
                if response.status >= 400:
                    resp_url = response.url
                    status = response.status
                    status_text = response.status_text
                    entry = f"[HTTP {status} {status_text}]: {resp_url}"
                    failed_requests.append(entry)
                    if status == 404:
                        error_logs.append(f"[404 Asset Not Found]: {resp_url}")
                    detailed_events.append({
                        "type": "http_error",
                        "status": status,
                        "status_text": status_text,
                        "url": resp_url
                    })

            page.on("response", on_response)

            # 4. Listen for network request failures (aborted, CORS, connection refused)
            def on_request_failed(request):
                failure = request.failure
                failure_text = failure if failure else "Unknown Network Failure"
                entry = f"[Request Failed]: {request.url} ({failure_text})"
                failed_requests.append(entry)
                detailed_events.append({"type": "request_failed", "url": request.url, "reason": str(failure_text)})

            page.on("requestfailed", on_request_failed)

            # Navigate to the target webstore URL
            logger.info(f"ConsoleListener loading {url} (timeout={timeout_seconds}s)")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_seconds * 1000)
            except Exception as nav_ex:
                logger.warning(f"Initial navigation event timed out or redirected: {nav_ex}")

            try:
                page.wait_for_timeout(1000)
            except Exception:
                pass

            browser.close()

            return ConsoleAuditResult(
                console_errors_count=len(error_logs),
                console_warnings_count=len(warning_logs),
                uncaught_exceptions_count=len(uncaught_exceptions),
                failed_requests_count=len(failed_requests),
                console_error_logs=error_logs,
                failed_request_urls=failed_requests,
                details=detailed_events
            )

    def _http_fallback_audit(self, url: str) -> ConsoleAuditResult:
        """
        Lightweight fallback for environments where full Playwright Chromium is not launched.
        Scans page for broken scripts, missing stylesheets, and malformed inline JS tags.
        """
        error_logs: List[str] = []
        warning_logs: List[str] = []
        failed_requests: List[str] = []
        detailed_events: List[Dict[str, Any]] = []

        html = ""
        if url.startswith("data:"):
            if "," in url:
                from urllib.parse import unquote
                html = unquote(url.split(",", 1)[1])
        elif requests is not None:
            try:
                resp = requests.get(url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=4)
                html = resp.text
            except Exception as ex:
                logger.debug(f"HTTP fallback fetch error: {ex}")

        if html:
            # Check for explicit console.error and console.warn calls in inline scripts
            for m in re.finditer(r'console\.error\([\'"]([^\'"]+)[\'"]\)', html):
                msg = f"[Console Error]: {m.group(1)}"
                error_logs.append(msg)
                detailed_events.append({"type": "console_error", "text": m.group(1)})
            for m in re.finditer(r'console\.warn\([\'"]([^\'"]+)[\'"]\)', html):
                msg = f"[Console Warning]: {m.group(1)}"
                warning_logs.append(msg)
                detailed_events.append({"type": "console_warning", "text": m.group(1)})

            # Check for broken external script tags
            if requests is not None and not url.startswith("data:"):
                script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
                for src in script_srcs[:8]:
                    full_src = urljoin(url, src)
                    try:
                        head_res = requests.head(full_src, timeout=3)
                        if head_res.status_code == 404:
                            msg = f"[404 Asset Not Found]: {full_src}"
                            error_logs.append(msg)
                            failed_requests.append(msg)
                            detailed_events.append({"type": "404_script", "url": full_src})
                    except Exception:
                        pass

            # Detect obvious syntax or liquid template error leaks in HTML
            liquid_errors = re.findall(r'Liquid error:[^\n<]+', html)
            for le in liquid_errors:
                msg = f"[Shopify Liquid Syntax Error]: {le.strip()}"
                error_logs.append(msg)
                detailed_events.append({"type": "liquid_error", "text": le.strip()})

        return ConsoleAuditResult(
            console_errors_count=len(error_logs),
            console_warnings_count=len(warning_logs),
            uncaught_exceptions_count=0,
            failed_requests_count=len(failed_requests),
            console_error_logs=error_logs,
            failed_request_urls=failed_requests,
            details=detailed_events
        )


async def capture_console_errors(url: str, timeout_seconds: int = 25, headless: bool = True) -> ConsoleAuditResult:
    """Async convenience wrapper for capturing console errors."""
    listener = ConsoleListener(headless=headless)
    return await listener.audit_url(url, timeout_seconds=timeout_seconds)


def capture_console_errors_sync(url: str, timeout_seconds: int = 25, headless: bool = True) -> ConsoleAuditResult:
    """Synchronous helper for calling console error listener from non-async contexts."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(capture_console_errors(url, timeout_seconds, headless))
        else:
            return loop.run_until_complete(capture_console_errors(url, timeout_seconds, headless))
    except Exception:
        return asyncio.run(capture_console_errors(url, timeout_seconds, headless))
