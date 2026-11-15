"""
backend/tools/scrapers
Atomic scraping tools for platform detection, social presence, Google Maps prospecting, and console error listening.
"""
from .shopify_detector import detect_shopify, detect_shopify_async, detect_shopify_from_html
from .social_scraper import extract_social_links, scrape_instagram_metrics, scrape_tiktok_metrics, resolve_social_presence
from .maps_harvester import MapsHarvester, harvest_niche_leads
from .console_listener import capture_console_errors, ConsoleListener

__all__ = [
    "detect_shopify",
    "detect_shopify_async",
    "detect_shopify_from_html",
    "extract_social_links",
    "scrape_instagram_metrics",
    "scrape_tiktok_metrics",
    "resolve_social_presence",
    "MapsHarvester",
    "harvest_niche_leads",
    "capture_console_errors",
    "ConsoleListener"
]
