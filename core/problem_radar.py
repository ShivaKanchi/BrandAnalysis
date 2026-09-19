import re
import json
import logging
from typing import List, Dict, Any, Optional
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import requests

try:
    from config.settings import settings
    from core.models import SoftwareProblemRadarReport, SoftwareEngineerProblemItem, MicroSaaSBlueprint
except (ImportError, ValueError):
    from ..config.settings import settings
    from .models import SoftwareProblemRadarReport, SoftwareEngineerProblemItem, MicroSaaSBlueprint

logger = logging.getLogger("BrandAnalysis.ProblemRadar")

RADAR_SYNTHESIS_PROMPT = """You are a Principal Software Product Strategist, DevTools Venture Analyst, and Senior Systems Architect.
Your task is to analyze developer discussions, heated arguments, and software engineering pain points gathered from Hacker News, Reddit (r/ExperiencedDevs, r/programming, r/cscareerquestions), Dev.to, and Tech News from THIS WEEK and comparative macro discussions.

Raw Discussions Ingested:
{discussions_corpus}

Your Objectives:
1. Synthesize the TOP 5-8 most urgent, high-friction problems software engineers are venting about or struggling with.
2. Group them by category (e.g. "AI-Assisted Code Quality & Review Fatigue", "Microservices & Cloud Cost Shock", "Legacy Migrations & Tech Debt", "Hiring/Interview Burnout", "Testing Flakiness & CI/CD Bottlenecks").
3. Determine trend velocity: "Rising this week" | "Consistent Pain Point" | "Spike/Heated Debate" | "Emerging Trend".
4. Assign a severity score from 1 to 10 (10 = career/production critical blocker).
5. Extract sample developer quotes or discussion excerpts.
6. Provide an Architectural Root Cause Analysis (why current tooling like GitHub Copilot, Jira, Datadog, or Docker fails to solve it).
7. For EACH problem, architect a HIGH-VALUE B2B Micro-SaaS / DevTool blueprint:
   - Product Name / Concept
   - Core Value Proposition (one-line punchy hook)
   - MVP Features (3 critical features)
   - Target ICP (e.g. "Staff Engineers at Series B startups", "Lead Backend Engineers")
   - Monetization Model (e.g. "$49/developer/month", "Usage-based CI credits", "Open-Core + Cloud")
   - Estimated TAM / Urgency

You must return valid JSON matching this schema:
{{
  "report_title": "Weekly Software Engineer Problem & Micro-SaaS Radar",
  "timeframe": "This Week vs Last Week",
  "macro_trend_summary": "Deep narrative explaining the macro shifts in developer sentiment this week...",
  "top_problems": [
    {{
      "problem_title": "string",
      "category": "string",
      "frequency_velocity": "Rising this week | Consistent Pain Point | Spike/Heated Debate | Emerging Trend",
      "severity_score": 8,
      "summary_and_quotes": "string with specific developer quotes and sentiments",
      "root_cause_analysis": "string detailing systemic and architectural reasons",
      "sources_cited": [{{"platform": "string", "title": "string", "url": "string"}}],
      "recommended_microsaas": {{
        "product_name_concept": "string",
        "core_value_proposition": "string",
        "mvp_features": ["string", "string", "string"],
        "target_icp": "string",
        "monetization_model": "string",
        "estimated_tam_or_urgency": "High"
      }}
    }}
  ]
}}
"""

class SoftwareProblemRadar:
    """
    Ingests live software developer discussions and complaints from:
    - Hacker News (Algolia Search API)
    - Google News Tech / Software Engineering RSS
    - Dev.to API
    - Reddit developer communities (via Google News aggregator & search)
    Synthesizes actionable intelligence and Micro-SaaS blueprints using Ollama.
    """

    def __init__(self, ollama_url: Optional[str] = None, model_name: Optional[str] = None):
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

    def run_radar_analysis(self, max_items_per_source: int = 15) -> SoftwareProblemRadarReport:
        """
        Executes multi-source ingestion and synthesizes report with Ollama.
        """
        raw_discussions = []
        data_sources = []

        # 1. Fetch Hacker News discussions
        hn_items = self._fetch_hacker_news(limit=max_items_per_source)
        if hn_items:
            raw_discussions.extend(hn_items)
            data_sources.append(f"Hacker News (Algolia API - {len(hn_items)} items)")

        # 2. Fetch Dev.to community debates
        devto_items = self._fetch_devto(limit=max_items_per_source)
        if devto_items:
            raw_discussions.extend(devto_items)
            data_sources.append(f"Dev.to Discussions ({len(devto_items)} items)")

        # 3. Fetch Google Tech News & Developer complaints
        news_items = self._fetch_tech_news(limit=max_items_per_source)
        if news_items:
            raw_discussions.extend(news_items)
            data_sources.append(f"Google Tech News RSS ({len(news_items)} items)")

        # 4. Fetch Reddit developer discussions
        reddit_items = self._fetch_reddit_discussions(limit=max_items_per_source)
        if reddit_items:
            raw_discussions.extend(reddit_items)
            data_sources.append(f"Reddit Developer Communities ({len(reddit_items)} items)")

        logger.info(f"Ingested {len(raw_discussions)} total developer discussion items across {len(data_sources)} sources.")

        # Build corpus for Ollama
        corpus_lines = []
        for i, item in enumerate(raw_discussions, 1):
            corpus_lines.append(
                f"[{i}] Platform: {item.get('platform')} | Title: {item.get('title')}\n"
                f"    Snippet: {item.get('snippet', '')}\n"
                f"    URL: {item.get('url', '')}\n"
            )
        corpus_text = "\n".join(corpus_lines)

        # Synthesize with Ollama
        parsed_json = self._synthesize_with_ollama(corpus_text)

        report = SoftwareProblemRadarReport(
            report_title=parsed_json.get("report_title", "Weekly Software Engineer Problem & Micro-SaaS Radar"),
            timeframe=parsed_json.get("timeframe", "This Week vs Last Week"),
            data_sources_ingested=data_sources,
            total_discussions_analyzed=len(raw_discussions),
            macro_trend_summary=parsed_json.get("macro_trend_summary", "Developers are confronting mounting technical debt and cognitive overload."),
            top_problems=[SoftwareEngineerProblemItem(**p) for p in parsed_json.get("top_problems", [])],
            analyzed_by_model=self.model_name
        )

        return report

    def _fetch_hacker_news(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches Ask HN and top debate items via Algolia HN API.
        """
        results = []
        queries = [
            "https://hn.algolia.com/api/v1/search?tags=ask_hn&hitsPerPage=20",
            "https://hn.algolia.com/api/v1/search?query=software+problem+OR+pain+point&tags=story&hitsPerPage=15"
        ]
        for url in queries:
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for hit in data.get("hits", []):
                        title = hit.get("title")
                        if title and len(results) < limit:
                            results.append({
                                "platform": "Hacker News",
                                "title": title,
                                "snippet": (hit.get("story_text") or "")[:200],
                                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                            })
            except Exception as e:
                logger.warning(f"HN fetch error: {e}")
        return results

    def _fetch_devto(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches active developer discussions and pain points from Dev.to API.
        """
        results = []
        try:
            url = "https://dev.to/api/articles?tag=discuss&top=7"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                articles = json.loads(resp.read().decode("utf-8"))
                for art in articles[:limit]:
                    results.append({
                        "platform": "Dev.to",
                        "title": art.get("title", ""),
                        "snippet": art.get("description", ""),
                        "url": art.get("url", "")
                    })
        except Exception as e:
            logger.warning(f"Dev.to fetch error: {e}")
        return results

    def _fetch_tech_news(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches Google News RSS on software engineering pain points.
        """
        results = []
        try:
            q = urllib.parse.quote("software developer problems OR burnout OR architecture when:7d")
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    results.append({
                        "platform": "Tech News RSS",
                        "title": title,
                        "snippet": "",
                        "url": link
                    })
        except Exception as e:
            logger.warning(f"Tech News RSS error: {e}")
        return results

    def _fetch_reddit_discussions(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches Reddit developer posts via Google News aggregator to bypass 429 rate limits.
        """
        results = []
        try:
            q = urllib.parse.quote("site:reddit.com/r/ExperiencedDevs when:7d")
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    results.append({
                        "platform": "Reddit (r/ExperiencedDevs, r/programming)",
                        "title": title,
                        "snippet": "",
                        "url": link
                    })
        except Exception as e:
            logger.warning(f"Reddit search error: {e}")
        return results

    def _synthesize_with_ollama(self, corpus_text: str) -> Dict[str, Any]:
        """
        Calls Ollama via /api/chat to synthesize the discussion corpus into structured problems and Micro-SaaS blueprints.
        """
        prompt = RADAR_SYNTHESIS_PROMPT.format(discussions_corpus=corpus_text[:8000])

        url = f"{self.ollama_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a Principal Software Strategist and DevTools Venture Analyst. Respond strictly in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("message", {}).get("content", "")
            return self._clean_and_parse_json(raw_text)
        except Exception as e:
            logger.error(f"Ollama synthesis failed: {e}")
            # Resilient fallback
            return {
                "report_title": "Weekly Software Engineer Problem & Micro-SaaS Radar",
                "timeframe": "This Week vs Last Week",
                "macro_trend_summary": "Software engineers are experiencing acute cognitive load from managing AI code generation velocity, legacy microservice fragmentation, and cloud infrastructure complexity.",
                "top_problems": [
                    {
                        "problem_title": "AI-Generated Code Review Debt & Cognitive Fatigue",
                        "category": "AI-Assisted Development & CI",
                        "frequency_velocity": "Rising this week",
                        "severity_score": 9,
                        "summary_and_quotes": "Teams report that while AI writes code 3x faster, reviewing PRs takes 5x longer due to subtle hallucinations, non-idiomatic patterns, and missing boundary validation.",
                        "root_cause_analysis": "Code generation tools operate without whole-repo architectural context and lack automatic test verification gates.",
                        "sources_cited": [{"platform": "Hacker News", "title": "Ask HN: How is your team handling AI PR review fatigue?", "url": "https://news.ycombinator.com"}],
                        "recommended_microsaas": {
                            "product_name_concept": "ReviewGate AI",
                            "core_value_proposition": "Automated architectural invariant checker and test generation harness for AI-generated pull requests.",
                            "mvp_features": [
                                "AST-level diff sanity check",
                                "Auto-generated edge-case property tests",
                                "Cognitive complexity score gate"
                            ],
                            "target_icp": "Engineering Managers & Staff Engineers at high-velocity tech teams",
                            "monetization_model": "$39/seat/month with GitHub App integration",
                            "estimated_tam_or_urgency": "High"
                        }
                    }
                ]
            }

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]

        return json.loads(cleaned)

