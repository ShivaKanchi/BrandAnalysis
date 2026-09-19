import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from config.settings import settings
    from core.models import BrandingAnalysisReport
except (ImportError, ValueError):
    from ..config.settings import settings
    from .models import BrandingAnalysisReport

logger = logging.getLogger("BrandAnalysis.Storage")

class StorageManager:
    """
    Manages automated persistence, indexing, and fast retrieval of BrandIntel analyses.
    All reports are saved by timestamp in a dedicated directory per profile:
    reports/<username>/<username>_<YYYYMMDD_HHMMSS>.json
    reports/<username>/<username>_<YYYYMMDD_HHMMSS>.md
    Also updates reports/intelligence_index.json for quick access and historical comparison.
    """

    INDEX_FILENAME = "intelligence_index.json"

    @classmethod
    def get_reports_dir(cls) -> Path:
        output_dir = getattr(settings, "OUTPUT_DIR", Path(__file__).resolve().parent.parent / "reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @classmethod
    def get_index_path(cls) -> Path:
        return cls.get_reports_dir() / cls.INDEX_FILENAME

    @classmethod
    def auto_save_report(cls, report: BrandingAnalysisReport) -> Dict[str, Path]:
        """
        Saves a BrandingAnalysisReport as JSON and Markdown, then updates the index.
        Returns the saved paths dict {'json': Path, 'markdown': Path}.
        """
        username = report.profile.username.strip().lstrip("@").lower()
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        file_prefix = f"{username}_{timestamp_str}"

        # Directory per username
        profile_dir = cls.get_reports_dir() / username
        profile_dir.mkdir(parents=True, exist_ok=True)

        json_path = profile_dir / f"{file_prefix}.json"
        md_path = profile_dir / f"{file_prefix}.md"

        # 1. Save JSON
        json_content = report.model_dump_json(indent=2)
        json_path.write_text(json_content, encoding="utf-8")

        # 2. Save Markdown
        try:
            from core.report_generator import ReportGenerator
            md_content = ReportGenerator.generate_markdown(report)
        except Exception:
            md_content = f"# Intelligence Report for @{username}\n\nGenerated at {now.isoformat()}"
        md_path.write_text(md_content, encoding="utf-8")

        # 3. Update Intelligence Index
        cls._update_index(
            username=username,
            report=report,
            file_prefix=file_prefix,
            json_path=json_path,
            md_path=md_path,
            timestamp=now
        )

        logger.info(f"Auto-saved report for @{username} to {json_path}")
        return {"json": json_path, "markdown": md_path}

    @classmethod
    def _update_index(
        cls,
        username: str,
        report: BrandingAnalysisReport,
        file_prefix: str,
        json_path: Path,
        md_path: Path,
        timestamp: datetime
    ):
        index_data = cls.load_index()

        meta_entry = {
            "timestamp": timestamp.isoformat(),
            "timestamp_label": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "file_prefix": file_prefix,
            "followers": report.profile.followers_count or "N/A",
            "posts_analyzed": len(report.profile.posts) if report.profile.posts else (report.profile.posts_count or 0),
            "locality": report.location.detected_location,
            "brand_archetype": report.brand_profile.brand_archetype,
            "needs_software_product": report.software_opportunity.needs_software_product if hasattr(report.software_opportunity, "needs_software_product") else True,
            "competitors_found": len(report.competitors),
            "json_path": str(json_path.relative_to(cls.get_reports_dir().parent) if cls.get_reports_dir().parent in json_path.parents else json_path),
            "markdown_path": str(md_path.relative_to(cls.get_reports_dir().parent) if cls.get_reports_dir().parent in md_path.parents else md_path),
            "abs_json_path": str(json_path.resolve())
        }

        if username not in index_data:
            index_data[username] = {
                "instagram_id": username,
                "latest_analysis": meta_entry,
                "history": [meta_entry]
            }
        else:
            index_data[username]["latest_analysis"] = meta_entry
            history = index_data[username].get("history", [])
            # Prepend newest
            history.insert(0, meta_entry)
            index_data[username]["history"] = history

        try:
            cls.get_index_path().write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to update intelligence index: {e}")

    @classmethod
    def load_index(cls) -> Dict[str, Any]:
        path = cls.get_index_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @classmethod
    def list_saved_profiles(cls) -> List[Dict[str, Any]]:
        """
        Returns a summary list of all saved profiles sorted by latest analysis date.
        """
        index_data = cls.load_index()
        profiles = []
        for username, data in index_data.items():
            latest = data.get("latest_analysis", {})
            history_count = len(data.get("history", []))
            profiles.append({
                "username": username,
                "locality": latest.get("locality", "N/A"),
                "archetype": latest.get("brand_archetype", "N/A"),
                "followers": latest.get("followers", "N/A"),
                "timestamp_label": latest.get("timestamp_label", ""),
                "history_count": history_count,
                "latest_file_prefix": latest.get("file_prefix", ""),
                "latest_json_path": latest.get("abs_json_path", "")
            })
        
        # Sort newest first
        profiles.sort(key=lambda x: x["timestamp_label"], reverse=True)
        return profiles

    @classmethod
    def get_profile_history(cls, username: str) -> List[Dict[str, Any]]:
        clean_user = username.strip().lstrip("@").lower()
        index_data = cls.load_index()
        return index_data.get(clean_user, {}).get("history", [])

    @classmethod
    def load_report_by_path(cls, json_path: str) -> Optional[BrandingAnalysisReport]:
        path = Path(json_path)
        if not path.exists():
            # Try resolving relative to project root or reports dir
            candidates = [
                cls.get_reports_dir().parent / json_path,
                cls.get_reports_dir() / json_path,
                cls.get_reports_dir() / path.name,
            ]
            if len(path.parts) >= 2:
                candidates.append(cls.get_reports_dir() / path.parts[-2] / path.parts[-1])
            for c in candidates:
                if c.exists():
                    path = c
                    break

        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return BrandingAnalysisReport(**data)
        except Exception as e:
            logger.error(f"Failed to load report from {json_path}: {e}")
            return None

    @classmethod
    def load_latest_report(cls, username: str) -> Optional[BrandingAnalysisReport]:
        clean_user = username.strip().lstrip("@").lower()
        history = cls.get_profile_history(clean_user)
        if history:
            latest_entry = history[0]
            for key in ["json_path", "abs_json_path"]:
                candidate_str = latest_entry.get(key)
                if candidate_str:
                    rep = cls.load_report_by_path(candidate_str)
                    if rep:
                        return rep
        # Fallback to scanning profile directory
        profile_dir = cls.get_reports_dir() / clean_user
        if profile_dir.exists():
            json_files = sorted(profile_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if json_files:
                return cls.load_report_by_path(str(json_files[0]))
        return None
