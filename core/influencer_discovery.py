"""Configurable, evidence-aware discovery for youth gaming creators.

The bundled catalogue is a starting pool, not a claim about a creator's private
audience demographics.  Records are deliberately marked ``needs_review`` until
current activity, brand safety, contact route, and first-party audience data
are checked by a human.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from config.settings import settings


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "influencer_seed_catalog.json"
INDIA_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "influencer_india_seed_catalog.json"
PUBLIC_CONTACTS_PATH = Path(__file__).resolve().parent.parent / "data" / "influencer_public_contacts.json"
REGISTRY_FILENAME = "influencer_registry.json"


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


class InfluencerDiscovery:
    """Ranks catalogue or user-supplied candidates and keeps a deduplicated registry."""

    def __init__(self, catalog_path: Path | None = None, reports_dir: Path | None = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.reports_dir = reports_dir or settings.OUTPUT_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @property
    def registry_path(self) -> Path:
        return self.reports_dir / REGISTRY_FILENAME

    def _load_catalog(self) -> list[dict[str, Any]]:
        paths = [self.catalog_path, INDIA_CATALOG_PATH]
        data: list[dict[str, Any]] = []
        signatures: set[str] = set()
        for path in paths:
            try:
                entries = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"Could not read influencer catalogue: {exc}") from exc
            if not isinstance(entries, list):
                raise ValueError("Influencer catalogue must be a JSON array")
            for entry in entries:
                signature = _normalise(str(entry.get("name", "")))
                if signature and signature not in signatures:
                    signatures.add(signature)
                    data.append(entry)
        return data

    def _load_registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"last_updated": None, "influencers": {}}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"last_updated": None, "influencers": {}}

    def _load_public_contacts(self) -> dict[str, dict[str, Any]]:
        try:
            contacts = json.loads(PUBLIC_CONTACTS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return contacts if isinstance(contacts, dict) else {}

    def discover(
        self,
        niches: Iterable[str] | None = None,
        audience_bands: Iterable[str] | None = None,
        country: str | None = None,
        min_followers: int | None = None,
        max_followers: int | None = None,
        limit: int = 100,
        fresh_only: bool = False,
        candidates: Iterable[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        if min_followers is not None and min_followers < 0:
            raise ValueError("min_followers must be zero or greater")
        if max_followers is not None and max_followers < 0:
            raise ValueError("max_followers must be zero or greater")
        if min_followers is not None and max_followers is not None and min_followers > max_followers:
            raise ValueError("min_followers cannot exceed max_followers")
        wanted_niches = {_normalise(item) for item in (niches or []) if item}
        wanted_bands = {str(item).strip() for item in (audience_bands or []) if item}
        registry = self._load_registry()
        seen = registry.get("influencers", {})
        pool = list(candidates) if candidates is not None else self._load_catalog()
        public_contacts = self._load_public_contacts()
        results: list[dict[str, Any]] = []
        skipped = 0

        for raw in pool:
            name = str(raw.get("name", "")).strip()
            creator_country = str(raw.get("country", "")).strip()
            follower_count = raw.get("follower_count")
            tags = [str(tag).strip() for tag in raw.get("niches", []) if str(tag).strip()]
            bands = [str(band).strip() for band in raw.get("audience_bands", []) if str(band).strip()]
            if not name or not tags or not bands:
                continue
            if country and _normalise(creator_country) != _normalise(country):
                continue
            if min_followers is not None and (not isinstance(follower_count, int) or follower_count < min_followers):
                continue
            if max_followers is not None and (not isinstance(follower_count, int) or follower_count > max_followers):
                continue
            key = _normalise(name)
            if fresh_only and key in seen:
                skipped += 1
                continue
            niche_matches = sum(_normalise(tag) in wanted_niches for tag in tags)
            band_matches = sum(band in wanted_bands for band in bands)
            if wanted_niches and not niche_matches:
                continue
            if wanted_bands and not band_matches:
                continue
            # Fit is explainable: category match has more weight than a broad age-band match.
            score = min(100, 45 + (25 * niche_matches) + (10 * band_matches))
            contact = public_contacts.get(key, {})
            results.append({
                "id": key,
                "name": name,
                "niches": tags,
                "audience_bands": bands,
                "audience_fit": raw.get("audience_fit", "inferred"),
                "source": raw.get("source", "curated_catalog"),
                "source_url": raw.get("source_url"),
                "country": creator_country or None,
                "follower_count": follower_count,
                "follower_platform": raw.get("follower_platform"),
                "follower_checked_at": raw.get("follower_checked_at"),
                "fit_score": score,
                "review_status": raw.get("review_status", "needs_review"),
                "instagram_handle": contact.get("instagram_handle"),
                "instagram_url": contact.get("instagram_url"),
                "business_phone": contact.get("business_phone"),
                "phone_status": contact.get("phone_status", "not_publicly_listed"),
                "contact_source_url": contact.get("source_url"),
                "notes": raw.get("notes", "Validate current activity, audience analytics, and brand safety before outreach."),
            })

        results.sort(key=lambda item: (-item["fit_score"], item["name"].lower()))
        results = results[:limit]
        now = datetime.now(timezone.utc).isoformat()
        for item in results:
            prior = seen.get(item["id"], {})
            seen[item["id"]] = {**prior, **item, "first_seen_at": prior.get("first_seen_at", now), "last_seen_at": now}
        registry["last_updated"] = now
        registry["influencers"] = seen
        self.registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        return {
            "count": len(results),
            "skipped_previously_seen": skipped,
            "filters": {"niches": sorted(wanted_niches), "audience_bands": sorted(wanted_bands), "country": country, "min_followers": min_followers, "max_followers": max_followers, "fresh_only": fresh_only},
            "influencers": results,
        }

    def export_csv(self) -> str:
        registry = self._load_registry().get("influencers", {})
        output = io.StringIO()
        columns = ["id", "name", "country", "follower_count", "follower_platform", "follower_checked_at", "instagram_handle", "instagram_url", "business_phone", "phone_status", "contact_source_url", "niches", "audience_bands", "audience_fit", "fit_score", "review_status", "source", "source_url", "notes", "first_seen_at", "last_seen_at"]
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for item in sorted(registry.values(), key=lambda row: row.get("name", "").lower()):
            row = dict(item)
            row["niches"] = "; ".join(row.get("niches", []))
            row["audience_bands"] = "; ".join(row.get("audience_bands", []))
            writer.writerow({column: row.get(column, "") for column in columns})
        return output.getvalue()

    def write_shortlist_csv(self, influencers: Iterable[dict[str, Any]], filename: str) -> Path:
        """Writes exactly one discovery run to a CSV without relying on registry scope."""
        safe_filename = re.sub(r"[^a-z0-9_-]", "_", filename.lower())
        if not safe_filename.endswith(".csv"):
            safe_filename += ".csv"
        output = io.StringIO()
        columns = ["id", "name", "country", "follower_count", "follower_platform", "follower_checked_at", "instagram_handle", "instagram_url", "business_phone", "phone_status", "contact_source_url", "niches", "audience_bands", "audience_fit", "fit_score", "review_status", "source", "source_url", "notes"]
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for item in influencers:
            row = dict(item)
            row["niches"] = "; ".join(row.get("niches", []))
            row["audience_bands"] = "; ".join(row.get("audience_bands", []))
            writer.writerow({column: row.get(column, "") for column in columns})
        path = self.reports_dir / safe_filename
        path.write_text(output.getvalue(), encoding="utf-8", newline="")
        return path
