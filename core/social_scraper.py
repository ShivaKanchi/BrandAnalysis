import re
import logging
from typing import List, Optional, Tuple
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup

try:
    from core.models import LocationInfo, SocialLinkItem
except (ImportError, ValueError):
    from .models import LocationInfo, SocialLinkItem

logger = logging.getLogger("BrandAnalysis.SocialScraper")

KNOWN_PLATFORMS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "twitter.com": "Twitter/X",
    "x.com": "Twitter/X",
    "linkedin.com": "LinkedIn",
    "tiktok.com": "TikTok",
    "github.com": "GitHub",
    "spotify.com": "Spotify Podcast",
    "apple.com": "Apple Podcast",
    "substack.com": "Substack",
    "beehiiv.com": "Beehiiv Newsletter",
    "medium.com": "Medium",
    "threads.net": "Threads",
    "facebook.com": "Facebook",
    "twitch.tv": "Twitch",
    "discord.gg": "Discord Community",
    "discord.com": "Discord Community",
    "skool.com": "Skool Community",
    "gumroad.com": "Gumroad Store",
    "patreon.com": "Patreon",
    "stan.store": "Stan Store",
    "beacons.ai": "Beacons Hub",
    "linktr.ee": "Linktree Hub"
}

LOCATION_REGEX = re.compile(
    r"(?:📍|based in|living in|from|located in|headquartered in|hq:?)\s*([A-Za-z\s,.-]{3,35})",
    re.IGNORECASE
)

# Common city/state patterns
COMMON_LOCATIONS = [
    "New York", "NYC", "Los Angeles", "LA", "San Francisco", "SF", "Austin", "Miami",
    "London", "Paris", "Berlin", "Dubai", "Toronto", "Vancouver", "Sydney", "Melbourne",
    "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Singapore", "Tokyo", "Amsterdam",
    "Chicago", "Seattle", "Atlanta", "Denver", "Boston", "San Diego", "Dallas", "Houston"
]

class SocialAndLocationScraper:
    def __init__(self, request_timeout: int = 12):
        self.timeout = request_timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }

    def resolve_location(
        self,
        username: str,
        full_name: str = "",
        biography: str = "",
        posts_captions: Optional[List[str]] = None,
        user_override: Optional[str] = None
    ) -> LocationInfo:
        """
        Determines the brand's locality/city.
        Priority:
        1. User override (if provided)
        2. Instagram bio or post captions
        3. Web search query (Google/Search snippet parsing)
        4. Fallback to Global/Online
        """
        if user_override and user_override.strip():
            return LocationInfo(
                detected_location=user_override.strip(),
                source="User Specified",
                confidence="High",
                details="Manually specified by the user."
            )

        # Step 1: Check Instagram bio
        loc_match = LOCATION_REGEX.search(biography)
        if loc_match:
            raw_loc = loc_match.group(1).strip()
            # Strip common marketing prefixes like 'Serving - ', 'Available in '
            cleaned_loc = re.sub(r"^(?:serving\s*[-:]?\s*|available in\s*|operating in\s*|based in\s*)", "", raw_loc, flags=re.IGNORECASE).strip(" .,-")
            cleaned_loc = re.sub(r"\s*,\s*", ", ", cleaned_loc)
            loc_candidate = cleaned_loc.title()
            if len(loc_candidate) > 2:
                return LocationInfo(
                    detected_location=loc_candidate,
                    source="Instagram Bio",
                    confidence="High",
                    details=f"Extracted from bio: '{loc_match.group(0)}'"
                )

        # Check for standalone well-known city in bio
        for city in COMMON_LOCATIONS:
            if re.search(rf"\b{re.escape(city)}\b", biography, re.IGNORECASE):
                return LocationInfo(
                    detected_location=city,
                    source="Instagram Bio",
                    confidence="High",
                    details=f"Detected primary city in bio: '{city}'"
                )

        # Step 2: Check recent captions if available
        if posts_captions:
            for cap in posts_captions[:6]:
                for city in COMMON_LOCATIONS:
                    if re.search(rf"\b{re.escape(city)}\b", cap, re.IGNORECASE):
                        return LocationInfo(
                            detected_location=city,
                            source="Instagram Captions",
                            confidence="Medium",
                            details=f"Found city mentioned in recent post: '{city}'"
                        )

        # Step 3: Check Google Search / Web Search
        logger.info(f"Location not in bio. Querying web search for @{username} location...")
        search_location = self._search_web_for_location(username, full_name)
        if search_location:
            return search_location

        return LocationInfo(
            detected_location="Global / Online",
            source="Inferred",
            confidence="Low",
            details="No specific physical locality found; brand operates primarily globally or digitally."
        )

    def _search_web_for_location(self, username: str, full_name: str) -> Optional[LocationInfo]:
        query_name = full_name if full_name and len(full_name) > 3 else username
        search_query = f"{query_name} instagram location based in city"
        
        try:
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code in (200, 202):
                soup = BeautifulSoup(resp.text, "html.parser")
                snippets = [a.get_text() for a in soup.select(".result__snippet")]
                text_corpus = " ".join(snippets)

                # Check regex in snippets
                match = LOCATION_REGEX.search(text_corpus)
                if match:
                    candidate = match.group(1).strip(" .,")
                    if len(candidate) > 2 and len(candidate) < 30:
                        return LocationInfo(
                            detected_location=candidate.title(),
                            source="Google Search",
                            confidence="Medium",
                            details=f"Extracted from web search snippet: '{candidate}'"
                        )

                # Check city occurrences in snippets
                for city in COMMON_LOCATIONS:
                    if re.search(rf"\b{re.escape(city)}\b", text_corpus, re.IGNORECASE):
                        return LocationInfo(
                            detected_location=city,
                            source="Google Search",
                            confidence="Medium",
                            details=f"Web search snippets associated {query_name} with '{city}'"
                        )
        except Exception as e:
            logger.warning(f"Web search for location failed: {e}")

        return None

    def scrape_social_links(self, external_url: Optional[str]) -> List[SocialLinkItem]:
        """
        Inspects the external URL from Instagram bio.
        If it's a link-in-bio aggregator (Linktree, Beacons, etc.) or personal site,
        fetches and extracts all outbound social profiles.
        """
        if not external_url:
            return []

        discovered_links: List[SocialLinkItem] = []
        seen_urls = set()

        # Add the primary external link itself
        primary_platform = self._identify_platform(external_url)
        discovered_links.append(SocialLinkItem(
            platform=primary_platform,
            url=external_url,
            status_notes="Primary external link in Instagram bio"
        ))
        seen_urls.add(external_url)

        # If it's a website or link aggregator, scrape outbound links
        try:
            resp = requests.get(external_url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                anchors = soup.find_all("a", href=True)

                for a in anchors:
                    href = a["href"].strip()
                    if not href.startswith("http"):
                        continue

                    # Unquote redirect parameters like linktree/?u=https%3A...
                    if "u=" in href:
                        try:
                            href = unquote(href.split("u=")[-1].split("&")[0])
                        except Exception:
                            pass

                    parsed = urlparse(href)
                    domain = parsed.netloc.lower().replace("www.", "")

                    for known_domain, plat_name in KNOWN_PLATFORMS.items():
                        if known_domain in domain:
                            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                            if clean_url not in seen_urls and len(parsed.path) > 1:
                                seen_urls.add(clean_url)
                                discovered_links.append(SocialLinkItem(
                                    platform=plat_name,
                                    url=clean_url,
                                    handle_or_title=a.get_text().strip() or None,
                                    status_notes=f"Linked from {primary_platform} landing page"
                                ))
                            break
        except Exception as e:
            logger.warning(f"Could not scrape outbound links from {external_url}: {e}")

        return discovered_links

    def _identify_platform(self, url: str) -> str:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        for known_domain, plat_name in KNOWN_PLATFORMS.items():
            if known_domain in domain:
                return plat_name
        return "Official Website"
