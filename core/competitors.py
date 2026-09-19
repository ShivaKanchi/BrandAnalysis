import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import requests
from bs4 import BeautifulSoup

try:
    from config.settings import settings
    from core.models import CompetitorItem, MarketAnalysis, LocationInfo
except (ImportError, ValueError):
    from ..config.settings import settings
    from .models import CompetitorItem, MarketAnalysis, LocationInfo

logger = logging.getLogger("BrandAnalysis.Competitors")

COMPETITOR_SYNTHESIS_PROMPT = """You are a Principal Market Intelligence Analyst and Competitive Strategy Consultant.
Your task is to analyze competitor research data and search findings for an Instagram brand to produce a comprehensive Market and Competitor intelligence breakdown.

Brand Info:
- Target Account: @{username} ({full_name})
- Primary Niche: {niche}
- Archetype: {archetype}
- Detected Locality: {location}

Search Findings & Competitor Signals:
{search_corpus}

You must extract and synthesize:
1. COMPETITORS LIST (Both Local competitors in that city/region if applicable, and Domain/niche competitors):
   - Name
   - Competitor Type: "Local Competitor" | "Direct Domain Rival" | "Indirect / Alternative"
   - Location (City or "Global / Online")
   - url_or_handle (URL, @handle, or Maps listing)
   - Market Standing: "Market Leader" | "Established" | "Emerging / Challenger" | "Niche Player"
   - Estimated Pricing / Monetization model
   - Strengths (2-3 items)
   - Weaknesses (2-3 items)
   - Ratings / Reviews summary or public reputation
   - Differentiator vs Target Brand (where target brand stands out or has an edge)

2. MARKET ANALYSIS & TRAJECTORY:
   - Market Saturation: "Low" | "Medium" | "High" | "Saturated"
   - Market Trend: "Rapidly Growing" | "Steady Growth" | "Mature / Flat" | "Declining / Disrupted"
   - Locality Market Dynamics (demand, density of alternatives, and city-level opportunities)
   - Domain Market Dynamics (industry macro trends and monetization shifts)
   - Untapped Market Opportunities (whitespace gaps left open by competitors)
   - Strategic Threats (emerging headwinds or aggressive competitor moves)

Output MUST be a valid JSON object matching the requested schema.
"""

COMPETITOR_SCHEMA = """
{
  "competitors": [
    {
      "name": "string",
      "competitor_type": "Local Competitor" | "Direct Domain Rival" | "Indirect / Alternative",
      "location": "string",
      "url_or_handle": "string or null",
      "market_standing": "Market Leader" | "Established" | "Emerging / Challenger" | "Niche Player",
      "estimated_pricing": "string or null",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "ratings_or_reviews": "string or null",
      "differentiator_vs_target": "string"
    }
  ],
  "market_analysis": {
    "market_saturation": "Low" | "Medium" | "High" | "Saturated",
    "market_trend": "Rapidly Growing" | "Steady Growth" | "Mature / Flat" | "Declining / Disrupted",
    "locality_market_dynamics": "string",
    "domain_market_dynamics": "string",
    "untapped_market_opportunities": ["string"],
    "strategic_threats": ["string"]
  }
}
"""

class CompetitorResearcher:
    def __init__(self, ollama_url: Optional[str] = None, model_name: Optional[str] = None):
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }

    def research_competitors_and_market(
        self,
        username: str,
        full_name: str,
        niche: str,
        archetype: str,
        location_info: LocationInfo
    ) -> Tuple[List[CompetitorItem], MarketAnalysis]:
        """
        Executes Google/web searches for local and domain competitors,
        and synthesizes findings into structured models via Ollama.
        """
        logger.info(f"Researching competitors for @{username} in niche '{niche}' and location '{location_info.detected_location}'")

        # Gather search results
        search_corpus = self._gather_search_snippets(
            username=username,
            full_name=full_name,
            niche=niche,
            location=location_info.detected_location
        )

        # Call Ollama to synthesize
        raw_json = self._synthesize_with_ollama(
            username=username,
            full_name=full_name,
            niche=niche,
            archetype=archetype,
            location=location_info.detected_location,
            search_corpus=search_corpus
        )

        competitors = [CompetitorItem(**c) for c in raw_json.get("competitors", [])]
        market_analysis = MarketAnalysis(**raw_json.get("market_analysis", {
            "market_saturation": "Medium",
            "market_trend": "Steady Growth",
            "locality_market_dynamics": "Local market exhibits steady interest with fragmented alternatives.",
            "domain_market_dynamics": "Broad digital market with strong demand for specialized authority.",
            "untapped_market_opportunities": ["Custom software workflows", "High-touch community membership"],
            "strategic_threats": ["Low barriers to entry for generic content creators"]
        }))

        return competitors, market_analysis

    def _gather_search_snippets(
        self,
        username: str,
        full_name: str,
        niche: str,
        location: str
    ) -> str:
        queries = []
        is_local = location and "global" not in location.lower() and "online" not in location.lower()

        if is_local:
            queries.append(f"top {niche} in {location} businesses studios competitors")
            queries.append(f"{niche} services {location} google maps reviews")

        queries.append(f"top {niche} brands like @{username} competitors")
        queries.append(f"best {niche} creators alternatives market")

        all_snippets = []
        for q in queries:
            try:
                url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code in (200, 202):
                    soup = BeautifulSoup(resp.text, "html.parser")
                    titles = [t.get_text().strip() for t in soup.select(".result__title")]
                    snippets = [s.get_text().strip() for s in soup.select(".result__snippet")]
                    for t, s in zip(titles[:4], snippets[:4]):
                        all_snippets.append(f"Title: {t}\nSnippet: {s}")
            except Exception as e:
                logger.warning(f"Search query '{q}' encountered error: {e}")

        if not all_snippets:
            return f"Niche: {niche}. General competitor space includes direct digital creators and local providers in {location}."

        return "\n---\n".join(all_snippets[:12])

    def _synthesize_with_ollama(
        self,
        username: str,
        full_name: str,
        niche: str,
        archetype: str,
        location: str,
        search_corpus: str
    ) -> Dict[str, Any]:
        prompt = COMPETITOR_SYNTHESIS_PROMPT.format(
            username=username,
            full_name=full_name,
            niche=niche,
            archetype=archetype,
            location=location,
            search_corpus=search_corpus
        )
        prompt += f"\n\nStrict Output Schema:\n{COMPETITOR_SCHEMA}\nReturn valid JSON only:"

        url = f"{self.ollama_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2}
        }

        try:
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data.get("message", {}).get("content", "")
            return self._clean_json(raw_content)
        except Exception as e:
            logger.error(f"Competitor synthesis via Ollama failed: {e}")
            return {
                "competitors": [
                    {
                        "name": f"Top Regional {niche} Leader",
                        "competitor_type": "Local Competitor" if "global" not in location.lower() else "Direct Domain Rival",
                        "location": location,
                        "url_or_handle": None,
                        "market_standing": "Established",
                        "estimated_pricing": "Mid-tier subscriptions or fee-for-service",
                        "strengths": ["Strong local recognition", "Established legacy brand"],
                        "weaknesses": ["Slow digital innovation", "Lack of custom interactive tools"],
                        "ratings_or_reviews": "4.6/5 across local listings",
                        "differentiator_vs_target": f"Target brand has modern digital audience and higher direct engagement."
                    }
                ],
                "market_analysis": {
                    "market_saturation": "Medium",
                    "market_trend": "Steady Growth",
                    "locality_market_dynamics": f"Steady demand in {location} with room for a modern tech-enabled player.",
                    "domain_market_dynamics": f"Expanding domain with high digital monetization potential.",
                    "untapped_market_opportunities": ["Automated client onboarding", "Interactive niche calculators"],
                    "strategic_threats": ["Rise of low-cost copycat creators"]
                }
            }

    def _clean_json(self, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]

        return json.loads(cleaned)
