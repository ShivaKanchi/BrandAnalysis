import os
import json
import csv
import io
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("BrandAnalysis.BackendStorage")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LEADS_FILE = DATA_DIR / "shopify_leads.json"
SETTINGS_FILE = DATA_DIR / "app_settings.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    "min_followers": 2500,
    "max_lighthouse_score": 60,
    "min_console_errors": 1,
    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud"),
    "ollama_api_key": os.getenv("OLLAMA_API_KEY", ""),
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "google_pagespeed_api_key": os.getenv("GOOGLE_PAGESPEED_API_KEY", ""),
    "headless_browser": True,
}


class StorageManager:
    """Handles persistence for discovered leads, global app settings, and reports."""

    @classmethod
    def load_leads(cls) -> List[Dict[str, Any]]:
        if not LEADS_FILE.exists():
            return []
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading leads from {LEADS_FILE}: {e}")
            return []

    @classmethod
    def save_leads(cls, leads: List[Dict[str, Any]]) -> bool:
        try:
            with open(LEADS_FILE, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving leads to {LEADS_FILE}: {e}")
            return False

    @classmethod
    def upsert_lead(cls, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update an e-commerce store lead."""
        leads = cls.load_leads()
        domain = lead_data.get("domain", "").strip().lower()
        if not domain and "store_url" in lead_data:
            domain = lead_data["store_url"].replace("https://", "").replace("http://", "").split("/")[0].lower()
            lead_data["domain"] = domain

        lead_id = lead_data.get("id") or domain or f"lead_{int(datetime.now().timestamp())}"
        lead_data["id"] = lead_id

        if "created_at" not in lead_data or not lead_data["created_at"]:
            lead_data["created_at"] = datetime.now().isoformat()
        lead_data["updated_at"] = datetime.now().isoformat()

        # Derive qualification status string if not present
        if "status" not in lead_data or not lead_data["status"]:
            if not lead_data.get("is_shopify", True):
                lead_data["status"] = "Non-Shopify"
            elif lead_data.get("qualified_for_revamp"):
                lead_data["status"] = "Qualified"
            else:
                lead_data["status"] = "Rejected"

        existing_index = next((i for i, item in enumerate(leads) if item.get("id") == lead_id or item.get("domain") == domain), None)
        if existing_index is not None:
            # Merge with existing
            merged = {**leads[existing_index], **lead_data}
            leads[existing_index] = merged
            cls.save_leads(leads)
            return merged
        else:
            leads.insert(0, lead_data)
            cls.save_leads(leads)
            return lead_data

    @classmethod
    def get_leads(
        cls,
        status: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        leads = cls.load_leads()
        if status and status.lower() != "all":
            leads = [l for l in leads if l.get("status", "").lower() == status.lower()]
        if query:
            q = query.lower()
            leads = [
                l for l in leads
                if q in l.get("domain", "").lower()
                or q in l.get("store_name", "").lower()
                or q in l.get("niche", "").lower()
            ]
        return leads

    @classmethod
    def get_lead(cls, lead_id: str) -> Optional[Dict[str, Any]]:
        leads = cls.load_leads()
        lead_id_clean = lead_id.strip().lower()
        for item in leads:
            if item.get("id") == lead_id or item.get("domain", "").lower() == lead_id_clean:
                return item
        return None

    @classmethod
    def delete_lead(cls, lead_id: str) -> bool:
        leads = cls.load_leads()
        lead_id_clean = lead_id.strip().lower()
        new_leads = [
            item for item in leads
            if item.get("id") != lead_id and item.get("domain", "").lower() != lead_id_clean
        ]
        if len(new_leads) != len(leads):
            cls.save_leads(new_leads)
            return True
        return False

    @classmethod
    def export_leads_csv(cls) -> str:
        """Exports all e-commerce store leads as a CSV string."""
        leads = cls.load_leads()
        output = io.StringIO()
        fieldnames = [
            "id",
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
            "status",
            "pitch_email",
            "pitch_dm",
            "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            row = {}
            for field in fieldnames:
                val = lead.get(field, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                row[field] = val
            writer.writerow(row)
        return output.getvalue()

    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        """Loads app settings with fallback to default values."""
        current = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    current.update(saved)
            except Exception as e:
                logger.error(f"Error reading {SETTINGS_FILE}: {e}")
        return current

    @classmethod
    def update_settings(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates and persists app settings."""
        settings_data = cls.get_settings()
        for k, v in updates.items():
            if k in DEFAULT_SETTINGS or k in settings_data:
                settings_data[k] = v
            else:
                settings_data[k] = v
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {SETTINGS_FILE}: {e}")
        return settings_data

    @classmethod
    def get_legacy_reports_index(cls) -> List[Dict[str, Any]]:
        """Reads reports index and compiles teardown reports from audited leads."""
        reports: List[Dict[str, Any]] = []

        # 1. Load any reports from intelligence_index.json if present
        index_file = REPORTS_DIR / "intelligence_index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        reports.extend(data.get("reports", []))
                    elif isinstance(data, list):
                        reports.extend(data)
            except Exception as e:
                logger.error(f"Error loading legacy index: {e}")

        # 2. Compile real reports from audited store leads
        leads = cls.load_leads()
        for idx, lead in enumerate(leads):
            domain = lead.get("domain", f"store-{idx+1}")
            store_name = lead.get("store_name", domain)
            perf = lead.get("lighthouse_performance", "N/A")
            errors_count = lead.get("console_errors_count", 0)
            status = lead.get("status", "Pending")
            created_at = lead.get("created_at", datetime.now().isoformat())
            blueprint_items = lead.get("redesign_blueprint") or lead.get("vision_revamp_suggestions") or ["Store speed optimization", "Script consolidation"]
            blueprint_str = "\n".join(f"- {item}" for item in blueprint_items)

            report_content = f"""# Technical Store Audit: {domain}
> Status: {status} | Platform: {lead.get('platform', 'Shopify')}

## 1. Executive Performance Summary
- Store Name: {store_name}
- Domain: {domain}
- Mobile Lighthouse Score: {perf} / 100
- JavaScript Console Errors: {errors_count}
- Social Audience: {lead.get('followers', 0):,} followers ({lead.get('social_handle', '@' + domain)})

## 2. Technical Remediation Blueprint
{blueprint_str}

## 3. Client Acquisition Outreach Pitch
### Email Draft
{lead.get('pitch_email', 'Pitch draft pending audit.')}

### Direct Message Draft
{lead.get('pitch_dm', 'DM draft pending audit.')}
"""

            reports.append({
                "id": f"rep-{lead.get('id', domain)}",
                "title": f"{store_name} - Technical Performance & Lead Teardown",
                "domain": domain,
                "type": "Store Lead Kit",
                "format": "Markdown",
                "generatedAt": created_at,
                "fileSize": f"{len(report_content.encode('utf-8')) // 1024 + 1} KB",
                "summary": f"Complete technical audit for {domain}: {perf}/100 speed score, {errors_count} runtime exceptions, status: {status}.",
                "content": report_content,
            })

        return reports
