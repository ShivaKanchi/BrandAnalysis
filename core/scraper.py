import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

try:
    from config.settings import settings
    from core.models import ProfileData
except (ImportError, ValueError):
    from ..config.settings import settings
    from .models import ProfileData

logger = logging.getLogger("BrandAnalysis.Scraper")

class LoginBarrierException(Exception):
    """Raised when Instagram blocks public access with a login barrier."""
    pass

class InstagramScraper:
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sessionid: Optional[str] = None,
        headless: bool = True
    ):
        self.username = username or settings.INSTAGRAM_USERNAME
        self.password = password or settings.INSTAGRAM_PASSWORD
        self.sessionid = sessionid or settings.INSTAGRAM_SESSIONID
        self.headless = headless if headless is not None else settings.HEADLESS_BROWSER
        self.cookies_file = settings.OUTPUT_DIR / "instagram_cookies.json"

    def scrape_profile(self, target_username: str, max_posts: int = 12) -> ProfileData:
        """
        Main entry point to fetch an Instagram profile.
        Tries Playwright first (with session / login if provided), then falls back to public mirrors.
        """
        target_username = target_username.strip().lstrip("@").lower()
        logger.info(f"Initiating scrape for target profile: @{target_username}")

        # Try Playwright with session / headless browser
        try:
            profile_data = self._scrape_with_playwright(target_username, max_posts=max_posts)
            if profile_data and (profile_data.biography or profile_data.posts):
                return profile_data
        except LoginBarrierException as e:
            logger.warning(f"Login barrier encountered: {e}")
            # If user provided credentials in call or env, try logging in
            if self.username and self.password:
                logger.info("Attempting automated login with provided credentials...")
                try:
                    self._login_with_playwright()
                    return self._scrape_with_playwright(target_username, max_posts=max_posts)
                except Exception as login_err:
                    logger.error(f"Automated login failed: {login_err}")
            raise e
        except Exception as e:
            logger.warning(f"Playwright scraping encountered issue: {e}. Trying fallback public extraction...")

        # Fallback to public mirror / HTTP OpenGraph inspection
        fallback_data = self._scrape_public_mirror_or_og(target_username)
        if fallback_data:
            return fallback_data

        raise RuntimeError(
            f"Could not retrieve profile for @{target_username}. "
            f"Instagram may require authentication. Provide credentials or session ID."
        )

    def _scrape_with_playwright(self, target_username: str, max_posts: int = 12) -> ProfileData:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )

            # Load saved cookies if present
            self._load_cookies(context)

            page = context.new_page()
            url = f"https://www.instagram.com/{target_username}/"
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=settings.REQUEST_TIMEOUT_SECONDS * 1000)

            time.sleep(3)  # Allow dynamic client-side hydration

            # Check for login barrier
            if "accounts/login" in page.url or page.locator("text='Log In'").count() > 3 and page.locator("header").count() == 0:
                # Check if we are stuck on a login wall
                login_heading = page.locator("text='Log in to Instagram'").count()
                if login_heading > 0:
                    browser.close()
                    raise LoginBarrierException("Instagram requires login to view this profile.")

            # Dismiss generic popups like "Save your login info?" or cookie banners
            try:
                cookie_btn = page.locator("button:has-text('Allow all cookies'), button:has-text('Decline optional cookies'), button:has-text('Only allow essential cookies')")
                if cookie_btn.count() > 0:
                    cookie_btn.first.click()
                    time.sleep(1)
            except Exception:
                pass

            # Extract Profile Header Information
            full_name = ""
            bio = ""
            external_url = ""
            followers_count = ""
            following_count = ""
            posts_count = ""
            is_verified = False

            try:
                # Name & Bio
                header_elem = page.locator("header")
                if header_elem.count() > 0:
                    # Verified badge check
                    if header_elem.locator("svg[aria-label='Verified']").count() > 0:
                        is_verified = True

                    # Full name
                    name_candidates = header_elem.locator("span, h1, h2").all_inner_texts()
                    for t in name_candidates:
                        t_clean = t.strip()
                        if t_clean and t_clean != target_username and len(t_clean) < 60 and not full_name:
                            full_name = t_clean

                    # Bio text
                    bio_candidates = header_elem.locator("h1 + div, div > span > div").all_inner_texts()
                    if bio_candidates:
                        bio = "\n".join(b.strip() for b in bio_candidates if b.strip())

                    # External link
                    links = header_elem.locator("a[rel*='nofollow'], a[target='_blank']").all()
                    for link in links:
                        href = link.get_attribute("href")
                        if href and "instagram.com" not in href:
                            external_url = href
                            break

                # Followers & Following
                stats = page.locator("header ul li").all_inner_texts()
                for stat in stats:
                    stat_lower = stat.lower()
                    if "post" in stat_lower:
                        posts_count = stat.split()[0]
                    elif "follower" in stat_lower:
                        followers_count = stat.split()[0]
                    elif "following" in stat_lower:
                        following_count = stat.split()[0]

            except Exception as e:
                logger.warning(f"Error extracting header metadata: {e}")

            # Fallback if bio is still empty: parse meta description tags
            if not bio or not followers_count:
                meta_desc = page.locator("meta[property='og:description']").get_attribute("content")
                if meta_desc:
                    # Format: "X Followers, Y Following, Z Posts - See Instagram photos and videos from Name (@username)"
                    parts = meta_desc.split(" - ")
                    if len(parts) >= 1 and not followers_count:
                        sub_parts = parts[0].split(",")
                        for sp in sub_parts:
                            if "follower" in sp.lower():
                                followers_count = sp.strip().split()[0]
                            elif "following" in sp.lower():
                                following_count = sp.strip().split()[0]
                            elif "post" in sp.lower():
                                posts_count = sp.strip().split()[0]

            # Extract recent post captions with progressive scrolling
            posts: List[Dict[str, Any]] = []
            seen_codes = set()
            try:
                max_scroll_attempts = max(1, (max_posts + 11) // 12) + 2
                for attempt in range(max_scroll_attempts):
                    page.mouse.wheel(0, 1000)
                    time.sleep(1.5)

                    post_anchors = page.locator("a[href*='/p/'], a[href*='/reel/']").all()
                    prev_count = len(posts)

                    for anchor in post_anchors:
                        if len(posts) >= max_posts:
                            break
                        href = anchor.get_attribute("href") or ""
                        code_match = re.search(r"/(?:p|reel)/([^/]+)/", href)
                        if not code_match:
                            continue
                        code = code_match.group(1)
                        if code in seen_codes:
                            continue
                        seen_codes.add(code)

                        img = anchor.locator("img").first
                        alt_text = ""
                        if img.count() > 0:
                            alt_text = img.get_attribute("alt") or ""

                        posts.append({
                            "post_index": len(posts) + 1,
                            "code": code,
                            "url": f"https://www.instagram.com{href}" if href.startswith("/") else href,
                            "caption": alt_text,
                            "alt_text": alt_text,
                            "hashtags": re.findall(r"#\w+", alt_text)
                        })

                    if len(posts) >= max_posts:
                        break
                    if len(posts) == prev_count and attempt >= 2:
                        break

            except Exception as e:
                logger.warning(f"Error collecting posts: {e}")

            browser.close()

            return ProfileData(
                username=target_username,
                full_name=full_name,
                biography=bio,
                external_url=external_url,
                followers_count=followers_count,
                following_count=following_count,
                posts_count=posts_count,
                is_verified=is_verified,
                posts=posts
            )

    def _login_with_playwright(self):
        """Logs into Instagram using provided credentials and saves cookies for reuse."""
        if not self.username or not self.password:
            raise ValueError("Username and password must be provided for login.")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
            time.sleep(3)

            # Fill username and password
            page.locator("input[name='username']").fill(self.username)
            time.sleep(1)
            page.locator("input[name='password']").fill(self.password)
            time.sleep(1)
            page.locator("button[type='submit']").click()

            # Wait for navigation or verification prompt
            page.wait_for_timeout(6000)

            # Check if login succeeded
            if "login" not in page.url:
                cookies = context.cookies()
                self._save_cookies(cookies)
                logger.info("Successfully logged into Instagram and stored session cookies.")
            else:
                logger.warning("Instagram login might require 2FA/challenge verification.")

            browser.close()

    def _load_cookies(self, context: BrowserContext):
        if self.sessionid:
            context.add_cookies([{
                "name": "sessionid",
                "value": self.sessionid,
                "domain": ".instagram.com",
                "path": "/"
            }])
            return

        if self.cookies_file.exists():
            try:
                cookies = json.loads(self.cookies_file.read_text(encoding="utf-8"))
                context.add_cookies(cookies)
                logger.info("Loaded cached session cookies.")
            except Exception as e:
                logger.warning(f"Could not load cookies from file: {e}")

    def _save_cookies(self, cookies: List[Dict[str, Any]]):
        try:
            self.cookies_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not save cookies: {e}")

    def _scrape_public_mirror_or_og(self, target_username: str) -> Optional[ProfileData]:
        """Fallback to OpenGraph meta tags on public Instagram URL or public mirror."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9"
            }
            resp = requests.get(f"https://www.instagram.com/{target_username}/", headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.find("meta", property="og:title")
                title_content = title["content"] if title else ""
                desc = soup.find("meta", property="og:description")
                desc_content = desc["content"] if desc else ""

                full_name = ""
                if "(" in title_content and ")" in title_content:
                    full_name = title_content.split("(")[0].strip()

                followers = ""
                following = ""
                posts_cnt = ""
                if desc_content:
                    parts = desc_content.split(" - ")
                    if len(parts) >= 1:
                        for sp in parts[0].split(","):
                            if "follower" in sp.lower():
                                followers = sp.strip().split()[0]
                            elif "following" in sp.lower():
                                following = sp.strip().split()[0]
                            elif "post" in sp.lower():
                                posts_cnt = sp.strip().split()[0]

                return ProfileData(
                    username=target_username,
                    full_name=full_name,
                    biography=desc_content,
                    followers_count=followers,
                    following_count=following,
                    posts_count=posts_cnt,
                    posts=[]
                )
        except Exception as e:
            logger.warning(f"OpenGraph scrape failed: {e}")
        return None

    @staticmethod
    def parse_manual_input(username: str, raw_text: str, external_url: str = "") -> ProfileData:
        """Helper to create a ProfileData object from user/agent provided profile text or dump."""
        posts = []
        # Try to parse individual post chunks if marked by '---' or 'Post'
        chunks = re.split(r"\n\s*(?=(?:Post\s*#?\d+|---+))", raw_text, flags=re.IGNORECASE)
        bio = ""
        if len(chunks) > 1:
            bio = chunks[0].strip()
            for idx, c in enumerate(chunks[1:], start=1):
                clean_chunk = c.strip()
                if clean_chunk:
                    posts.append({
                        "post_index": idx,
                        "caption": clean_chunk,
                        "hashtags": re.findall(r"#\w+", clean_chunk)
                    })
        elif chunks:
            bio = chunks[0].strip()

        return ProfileData(
            username=username.strip().lstrip("@").lower(),
            biography=bio,
            external_url=external_url,
            posts=posts
        )
