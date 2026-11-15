"""
backend/tools/storage/report_generator.py
Markdown and JSON report exporter for Brand Audits, Lead Prospecting, and Shopify Revamps.
Ported cleanly from core/report_generator.py.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from backend.models import BrandingAnalysisReport, ShopifyStoreLead

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "reports"


class ReportGenerator:
    """Generates structured Markdown reports for audits and leads."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_shopify_revamp_md(self, lead: ShopifyStoreLead) -> str:
        """Generates a clean markdown audit & outreach sheet for a Shopify store lead."""
        lines = [
            f"# Shopify Revamp Audit Dossier: {lead.store_name or lead.domain}",
            f"**Audited URL**: [{lead.domain}](https://{lead.domain})",
            f"**Timestamp**: {lead.created_at}",
            f"**Qualification Status**: {'QUALIFIED FOR REVAMP' if lead.qualified_for_revamp else 'NOT QUALIFIED'}",
            "",
            "## 1. Technical Health & Performance",
            f"- **Mobile Lighthouse Speed**: {lead.lighthouse_performance:.0f}/100" if lead.lighthouse_performance else "- **Mobile Lighthouse**: N/A",
            f"- **SEO Score**: {lead.lighthouse_seo:.0f}/100" if lead.lighthouse_seo else "- **SEO Score**: N/A",
            f"- **Accessibility Score**: {lead.lighthouse_accessibility:.0f}/100" if lead.lighthouse_accessibility else "- **Accessibility Score**: N/A",
            f"- **Active Console Errors**: {lead.console_errors_count} runtime errors",
            "",
            "### Runtime Error Sample",
        ]
        if lead.console_error_logs:
            for log in lead.console_error_logs[:4]:
                lines.append(f"- `{log}`")
        else:
            lines.append("- *No fatal console errors logged.*")

        lines.extend([
            "",
            "## 2. Audience & Social Reach",
            f"- **Social Handle**: {lead.social_handle or 'N/A'}",
            f"- **Followers**: {lead.followers:,}" if lead.followers else "- **Followers**: N/A",
            f"- **Engagement Rate**: {lead.engagement_rate:.1f}%" if lead.engagement_rate else "- **Engagement Rate**: N/A",
            "",
            "## 3. Visual & UX Critique",
            f"- **Design Score**: {lead.vision_score}/100" if lead.vision_score else "- **Design Score**: N/A",
            f"- **Critique**: {lead.vision_critique or 'N/A'}",
            "",
            "### 3-Point Revamp Blueprint"
        ])

        for pt in lead.redesign_blueprint:
            lines.append(f"1. {pt}")

        lines.extend([
            "",
            "## 4. Cold Outreach Kit",
            "### Personalized Cold Email",
            "```text",
            lead.pitch_email or "N/A",
            "```",
            "",
            "### Short DM (Instagram/LinkedIn)",
            "```text",
            lead.pitch_dm or "N/A",
            "```"
        ])

        md_content = "\n".join(lines)
        file_path = self.output_dir / f"{lead.domain.replace('.', '_')}_audit.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return md_content
