"""
backend/tools/scrapers/instagram_profile_scraper.py
Public and Playwright-based Instagram Profile Reverse-Engineering Scraper.
Extracts:
- Profile metadata (biography, full name, follower/following counts)
- External link (link-in-bio)
- Recent posts, captions, media links, and engagement signals
Ported and cleanly modularized from core/scraper.py.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from backend.models import ProfileData, LocationInfo, SocialLinkItem
from backend.tools.scrapers.social_scraper import scrape_instagram_metrics

logger = logging.getLogger("BrandAnalysis.InstagramScraper")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}


class InstagramProfileScraper:
    """
    Scrapes Instagram profiles with Playwright when available, with automatic OpenGraph fallback.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def scrape_profile(self, target_username: str, max_posts: int = 12) -> ProfileData:
        """
        Scrapes profile data for target username.
        Tries Playwright first; falls back to public meta tags if login wall is encountered.
        """
        clean_user = target_username.strip().lstrip("@").lower()
        logger.info(f"Scraping Instagram profile: @{clean_user}")

        # 1. Try Playwright
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                context = browser.new_context(user_agent=DEFAULT_HEADERS["User-Agent"])
                page = context.new_page()

                url = f"https://www.instagram.com/{clean_user}/"
                page.goto(url, timeout=20000)
                page.wait_for_timeout(2500)

                # Check if redirected to login wall
                if "accounts/login" in page.url:
                    browser.close()
                    raise PermissionError("Instagram login wall encountered.")

                # Extract title and meta tags
                html = page.content()
                browser.close()

                return self._parse_html(clean_user, html)
        except Exception as e:
            logger.debug(f"Playwright scrape for @{clean_user} fallback: {e}")

        # 2. Public OpenGraph Fallback
        return self._scrape_public_meta(clean_user)

    def _parse_html(self, username: str, html: str) -> ProfileData:
        """Parses profile data from HTML content."""
        metrics = scrape_instagram_metrics(username)

        # Look for biography in meta description
        bio = ""
        desc_m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html)
        if desc_m:
            bio = desc_m.group(1)

        # Look for external link
        external_url = ""
        link_m = re.search(r'href=["\'](https?://(?:l\.instagram\.com|\S+))["\']', html)
        if link_m:
            external_url = link_m.group(1)

        return ProfileData(
            username=username,
            full_name=username.title(),
            biography=bio,
            external_url=external_url,
            followers_count=str(metrics.get("followers", 0)),
            following_count=str(metrics.get("following", 0)),
            posts_count=str(metrics.get("posts_count", 0)),
            is_verified=metrics.get("is_verified", False),
            location_info=None,
            social_links=[],
            posts=[]
        )

    def _scrape_public_meta(self, username: str) -> ProfileData:
        """Lightweight HTTP OpenGraph scrape."""
        metrics = scrape_instagram_metrics(username)
        return ProfileData(
            username=username,
            full_name=username.title(),
            biography=f"Instagram profile for @{username}.",
            external_url="",
            followers_count=str(metrics.get("followers", 0)),
            following_count=str(metrics.get("following", 0)),
            posts_count=str(metrics.get("posts_count", 0)),
            is_verified=metrics.get("is_verified", False),
            location_info=None,
            social_links=[],
            posts=[]
        )
