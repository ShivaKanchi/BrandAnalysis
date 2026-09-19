import re
import logging
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

try:
    from core.models import DiscoveredLeadItem, LeadProspectingReport
except (ImportError, ValueError):
    from .models import DiscoveredLeadItem, LeadProspectingReport

logger = logging.getLogger("BrandAnalysis.AutoProspector")

class AutoProspector:
    """
    Automated Local Business & Instagram Lead Harvester.
    Searches Google Maps for businesses in any niche and locality,
    scrapes business profiles, extracts website/phone/ratings,
    and resolves official Instagram handles for direct BrandIntel analysis.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }

    def discover_leads(
        self,
        niche_or_query: str,
        location: str,
        limit: int = 8
    ) -> LeadProspectingReport:
        """
        Main pipeline:
        1. Formulate Maps query.
        2. Scrape place listings from Google Maps.
        3. For each place with a website, fetch the home page and resolve Instagram handle.
        4. Return structured LeadProspectingReport.
        """
        combined_query = f"{niche_or_query} in {location}".strip()
        logger.info(f"Starting lead prospecting for query: '{combined_query}' (limit={limit})")

        scraped_places = self._scrape_maps_places(combined_query, limit=limit)
        leads: List[DiscoveredLeadItem] = []

        for place in scraped_places:
            website = place.get("website")
            ig_handle = None
            lead_status = "Maps Only"

            if website:
                lead_status = "Website Only (No IG)"
                ig_handle = self._extract_instagram_from_website(website)
                if ig_handle:
                    lead_status = "Instagram Verified"

            # If no IG handle found on website, try quick search fallback
            if not ig_handle:
                ig_handle = self._search_instagram_fallback(place["name"], location)
                if ig_handle:
                    lead_status = "Instagram Verified"

            ig_url = f"https://www.instagram.com/{ig_handle}/" if ig_handle else None

            lead = DiscoveredLeadItem(
                business_name=place["name"],
                category=niche_or_query,
                address_or_location=location,
                website=website,
                instagram_handle=ig_handle,
                instagram_url=ig_url,
                maps_url=place.get("maps_url"),
                rating=place.get("rating"),
                review_count=place.get("reviews"),
                phone=place.get("phone"),
                lead_status=lead_status
            )
            leads.append(lead)

        verified_count = sum(1 for l in leads if l.instagram_handle)
        logger.info(f"Prospecting completed. Discovered {len(leads)} places, {verified_count} with Instagram.")

        return LeadProspectingReport(
            search_query=combined_query,
            target_locality=location,
            total_places_scanned=len(leads),
            leads_with_instagram=verified_count,
            leads=leads
        )

    def _scrape_maps_places(self, query: str, limit: int = 8) -> List[dict]:
        """
        Uses Playwright to query Google Maps and extract place listings with websites.
        """
        places = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=self.headers["User-Agent"],
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()

                search_url = f"https://www.google.com/maps/search/{requests.utils.quote(query)}"
                page.goto(search_url, timeout=30000)
                page.wait_for_timeout(3500)

                # Collect links matching place listings
                raw_links = page.eval_on_selector_all(
                    'a[href*="/maps/place/"]',
                    '''els => els.map(el => {
                        return {
                            name: el.getAttribute("aria-label") || "",
                            href: el.href || ""
                        };
                    }).filter(x => x.name && x.href)'''
                )

                seen_names = set()
                deduped_places = []
                for item in raw_links:
                    name_clean = item["name"].strip()
                    if name_clean and name_clean not in seen_names:
                        seen_names.add(name_clean)
                        deduped_places.append(item)
                    if len(deduped_places) >= limit:
                        break

                logger.info(f"Found {len(deduped_places)} raw place items from Google Maps")

                # Visit top items to extract authority website and ratings
                for place_meta in deduped_places:
                    name = place_meta["name"]
                    href = place_meta["href"]
                    website = None
                    rating = None
                    reviews = None

                    try:
                        page.goto(href, timeout=20000)
                        page.wait_for_timeout(2000)

                        # Check for website link
                        site_el = page.query_selector('a[data-item-id="authority"]')
                        if site_el:
                            website = site_el.get_attribute("href")

                        # Check for rating text
                        rating_el = page.query_selector('div.F7nice span[aria-hidden="true"]')
                        if rating_el:
                            rating = rating_el.inner_text().strip()

                        reviews_el = page.query_selector('div.F7nice span span[aria-label*="reviews"]')
                        if reviews_el:
                            reviews = reviews_el.inner_text().strip("()")

                    except Exception as ex:
                        logger.warning(f"Could not load details for {name}: {ex}")

                    places.append({
                        "name": name,
                        "maps_url": href,
                        "website": website,
                        "rating": rating,
                        "reviews": reviews
                    })

                browser.close()
        except Exception as e:
            logger.error(f"Error during Google Maps Playwright scraping: {e}")

        return places

    def _extract_instagram_from_website(self, website_url: str) -> Optional[str]:
        """
        Fetches website HTML and extracts Instagram profile handle.
        """
        try:
            resp = requests.get(website_url, headers=self.headers, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Check <a> tags with instagram.com
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    match = re.search(r"instagram\.com/([a-zA-Z0-9_\.]{3,30})/?", href, re.IGNORECASE)
                    if match:
                        handle = match.group(1).lower()
                        if handle not in ["p", "explore", "reels", "stories", "accounts", "direct", "developer", "about"]:
                            return handle
        except Exception as ex:
            logger.debug(f"Website social scrape failed for {website_url}: {ex}")

        return None

    def _search_instagram_fallback(self, business_name: str, location: str) -> Optional[str]:
        """
        Fallback search for Instagram handle if website didn't have it or has no website.
        """
        try:
            clean_name = re.sub(r"[|/\\-].*$", "", business_name).strip()
            query = f"{clean_name} {location} Instagram"
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            resp = requests.get(url, headers=self.headers, timeout=6)
            if resp.status_code in (200, 202):
                matches = re.findall(r"instagram\.com/([a-zA-Z0-9_\.]{3,30})/?", resp.text, re.IGNORECASE)
                for m in matches:
                    handle = m.lower()
                    if handle not in ["p", "explore", "reels", "stories", "accounts", "direct", "developer", "about"]:
                        return handle
        except Exception:
            pass
        return None
