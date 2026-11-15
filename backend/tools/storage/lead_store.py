"""
backend/tools/storage/lead_store.py
Persistent storage engine for Shopify Store Leads and prospecting data.
Supports JSON persistence, querying, updating, and CSV export.
"""

import os
import csv
import json
import io
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from backend.models import ShopifyStoreLead

logger = logging.getLogger("BrandAnalysis.LeadStore")

DEFAULT_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "reports"
LEADS_FILE = DEFAULT_STORAGE_DIR / "shopify_leads.json"


class LeadStore:
    """
    Manages persistence and retrieval of Shopify store audit leads.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.leads_file = self.storage_dir / "shopify_leads.json"

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        """Loads all leads from JSON file into a domain-keyed dict."""
        if not self.leads_file.exists():
            return {}
        try:
            with open(self.leads_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read leads file: {e}")
            return {}

    def _save_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Writes domain-keyed dict to JSON file."""
        try:
            with open(self.leads_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save leads file: {e}")

    def save_lead(self, lead: ShopifyStoreLead) -> ShopifyStoreLead:
        """
        Saves or updates a ShopifyStoreLead.
        Keyed by domain.
        """
        all_leads = self._load_all()
        clean_domain = lead.domain.lower().replace("https://", "").replace("http://", "").rstrip("/")
        lead_dict = lead.model_dump()
        all_leads[clean_domain] = lead_dict
        self._save_all(all_leads)
        logger.info(f"Persisted lead for domain: {clean_domain}")
        return lead

    def get_leads(self, qualified_only: bool = False) -> List[ShopifyStoreLead]:
        """
        Retrieves all stored leads, optionally filtering for qualified leads.
        """
        all_leads = self._load_all()
        leads: List[ShopifyStoreLead] = []
        for d, data in all_leads.items():
            try:
                lead = ShopifyStoreLead(**data)
                if not qualified_only or lead.qualified_for_revamp:
                    leads.append(lead)
            except Exception as e:
                logger.warning(f"Error parsing stored lead {d}: {e}")
        return leads

    def get_lead(self, domain: str) -> Optional[ShopifyStoreLead]:
        """Retrieves a single lead by domain."""
        all_leads = self._load_all()
        clean_domain = domain.lower().replace("https://", "").replace("http://", "").rstrip("/")
        if clean_domain in all_leads:
            return ShopifyStoreLead(**all_leads[clean_domain])
        return None

    def export_csv(self) -> str:
        """
        Exports all leads into CSV string format matching standard CRM lead imports.
        """
        leads = self.get_leads()
        output = io.StringIO()
        fieldnames = [
            "domain",
            "store_name",
            "platform",
            "is_shopify",
            "followers",
            "engagement_rate",
            "lighthouse_performance",
            "lighthouse_seo",
            "lighthouse_accessibility",
            "console_errors_count",
            "vision_score",
            "qualified_for_revamp",
            "qualification_reasons",
            "subject_line",
            "pitch_email",
            "pitch_dm",
            "created_at"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for lead in leads:
            reasons_str = "; ".join(lead.qualification_reasons)
            writer.writerow({
                "domain": lead.domain,
                "store_name": lead.store_name or "",
                "platform": lead.platform,
                "is_shopify": lead.is_shopify,
                "followers": lead.followers or 0,
                "engagement_rate": lead.engagement_rate or 0.0,
                "lighthouse_performance": lead.lighthouse_performance or "",
                "lighthouse_seo": lead.lighthouse_seo or "",
                "lighthouse_accessibility": lead.lighthouse_accessibility or "",
                "console_errors_count": lead.console_errors_count,
                "vision_score": lead.vision_score or "",
                "qualified_for_revamp": lead.qualified_for_revamp,
                "qualification_reasons": reasons_str,
                "subject_line": lead.metadata.get("subject_line", ""),
                "pitch_email": lead.pitch_email or "",
                "pitch_dm": lead.pitch_dm or "",
                "created_at": lead.created_at
            })

        csv_str = output.getvalue()
        # Also persist to reports/leads_export.csv
        try:
            export_file = self.storage_dir / "leads_export.csv"
            with open(export_file, "w", encoding="utf-8", newline="") as f:
                f.write(csv_str)
        except Exception:
            pass

        return csv_str


# Global default store instance
lead_store = LeadStore()
