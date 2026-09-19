import json
from pathlib import Path
from typing import Optional, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

try:
    from core.models import BrandingAnalysisReport
    from config.settings import settings
except (ImportError, ValueError):
    from .models import BrandingAnalysisReport
    from ..config.settings import settings

console = Console()

class ReportGenerator:
    @staticmethod
    def generate_markdown(report: BrandingAnalysisReport) -> str:
        prof = report.profile
        loc = report.location
        soc = report.social_status
        bp = report.brand_profile
        imp = report.brand_improvements
        so = report.software_opportunity
        mkt = report.market_analysis

        verdict_badge = "✅ **RECOMMENDED**" if so.needs_software_product else "❌ **NOT RECOMMENDED / LOW FIT**"
        conf_badge_map = {"High": "🟢 High", "Medium": "🟡 Medium", "Low": "⚪ Low"}

        md = []
        md.append(f"# 📊 Master Personal Branding, Competitor & Software Intelligence: @{prof.username}\n")
        md.append(f"> **Analyzed At**: `{report.analysis_timestamp}` | **Engine**: `{report.analyzed_by_model}`\n")
        
        # Profile & Locality Overview
        md.append("## 👤 Profile & Geographic Presence")
        md.append(f"- **Name**: {prof.full_name or 'N/A'}")
        md.append(f"- **Bio**: {prof.biography or 'N/A'}")
        md.append(f"- **Detected Location / Locality**: **{loc.detected_location}** *(Source: {loc.source}, Confidence: {loc.confidence})*")
        if loc.details:
            md.append(f"  - *Location Details*: {loc.details}")
        md.append(f"- **Metrics**: {prof.followers_count or '?'} Followers | {prof.following_count or '?'} Following | {prof.posts_count or '?'} Posts")
        md.append(f"- **Verified**: {'Yes' if prof.is_verified else 'No'}\n")

        # Cross-Platform Social Status
        md.append("## 🌐 Social Status & Multi-Platform Footprint")
        md.append(f"- **Cross-Platform Presence**: `{soc.cross_platform_presence_score}`")
        md.append(f"- **Audience Ecosystem**: {soc.social_ecosystem_overview}")
        if soc.linked_socials:
            md.append("- **Discovered Social Channels & Links**:")
            for s in soc.linked_socials:
                note = f" *({s.status_notes})*" if s.status_notes else ""
                md.append(f"  - **{s.platform}**: [{s.url}]({s.url}){note}")
        else:
            md.append("- **Discovered Social Channels**: *No external profiles linked from Instagram bio.*")
        
        if soc.strengths:
            md.append("- **Social Strengths**:")
            for st_item in soc.strengths:
                md.append(f"  - ✓ {st_item}")
        if soc.vulnerabilities:
            md.append("- **Social Vulnerabilities & Gaps**:")
            for v_item in soc.vulnerabilities:
                md.append(f"  - ⚠️ {v_item}")
        md.append("\n---\n")

        # Likes and Interests with Citations
        md.append("## 🎯 Likes & Interests (With Citations & Confidence)")
        md.append("| Interest / Topic | Category | Confidence | Citations & Evidence | Reasoning |")
        md.append("| :--- | :--- | :---: | :--- | :--- |")

        for item in report.interests:
            conf_display = conf_badge_map.get(item.confidence, item.confidence)
            cite_texts = []
            for c in item.citations:
                excerpt = c.content_excerpt.replace("|", "\\|").replace("\n", " ")
                source = f"**{c.source_type}**"
                if c.post_index:
                    source += f" [Post #{c.post_index}]"
                cite_texts.append(f"- {source}: *\"{excerpt}\"*")
            citations_md = "<br>".join(cite_texts) if cite_texts else "General profile context"
            reasoning_clean = item.confidence_reasoning.replace("|", "\\|")
            md.append(f"| **{item.topic}** | {item.category} | {conf_display} | {citations_md} | {reasoning_clean} |")

        md.append("\n---\n")

        # Brand Identity
        md.append("## 🏛️ Personal Brand Architecture")
        md.append(f"- **Brand Archetype**: `{bp.brand_archetype}`")
        md.append(f"- **Primary Niche**: {bp.primary_niche}")
        if bp.secondary_niches:
            md.append(f"- **Secondary Niches**: {', '.join(bp.secondary_niches)}")
        md.append(f"- **Tone & Voice**: {bp.tone_and_voice}")
        md.append(f"- **Target Audience**: {bp.target_audience}")
        md.append("- **Content Pillars**:")
        for cp in bp.content_pillars:
            md.append(f"  - {cp}")
        if bp.current_monetization_methods:
            md.append(f"- **Current Monetization**: {', '.join(bp.current_monetization_methods)}")

        md.append("\n---\n")

        # Brand Improvement Roadmap
        md.append("## 📈 Actionable Brand Improvement Roadmap")
        md.append("### ⚡ Quick Wins (Under 30 Days)")
        for qw in imp.quick_wins_under_30_days:
            md.append(f"- [ ] **{qw}**")
        
        md.append("\n### 🎯 Funnel & Conversion Enhancements")
        for fc in imp.funnel_and_conversion_improvements:
            md.append(f"- {fc}")

        md.append("\n### ✍️ Content & Messaging Upgrades")
        for cm in imp.content_and_messaging_improvements:
            md.append(f"- {cm}")

        md.append("\n### 🚀 Cross-Platform Expansion")
        for cp in imp.cross_platform_growth_improvements:
            md.append(f"- {cp}")

        md.append("\n---\n")

        # Competitor Landscape
        md.append("## ⚔️ Competitor Landscape (Local & Domain Rivals)")
        if report.competitors:
            md.append("| Competitor Name | Type | Location | Standing | Pricing / Model | Differentiator vs Target |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for comp in report.competitors:
                url_str = f"[{comp.name}]({comp.url_or_handle})" if comp.url_or_handle else comp.name
                diff = comp.differentiator_vs_target.replace("|", "\\|")
                pricing = (comp.estimated_pricing or "N/A").replace("|", "\\|")
                md.append(f"| **{url_str}** | `{comp.competitor_type}` | {comp.location} | {comp.market_standing} | {pricing} | {diff} |")
        else:
            md.append("*No direct competing entities registered.*")

        md.append("\n---\n")

        # Market Analysis
        md.append("## 📊 Market Dynamics & Trajectory")
        md.append(f"- **Market Saturation Level**: `{mkt.market_saturation}`")
        md.append(f"- **Market Trajectory**: `{mkt.market_trend}`")
        md.append(f"- **Local Market Dynamics ({loc.detected_location})**: {mkt.locality_market_dynamics}")
        md.append(f"- **Domain & Macro Dynamics**: {mkt.domain_market_dynamics}")
        if mkt.untapped_market_opportunities:
            md.append("- **Untapped Market Whitespace / Opportunities**:")
            for opp in mkt.untapped_market_opportunities:
                md.append(f"  - 💡 **{opp}**")
        if mkt.strategic_threats:
            md.append("- **Strategic Threats & Risks**:")
            for th in mkt.strategic_threats:
                md.append(f"  - ⚠️ {th}")

        # Website Audit & Inbound Lead Strategy
        web = report.website_opportunity
        web_badge = "✅ **ACTIVE WEBSITE**" if web.has_website else "🚨 **NO DEDICATED WEBSITE (CRITICAL LEAD LEAKAGE)**"
        md.append("## 🌐 Website Audit & Inbound Lead Generation Engine")
        md.append(f"### Status: {web_badge}")
        if web.existing_url:
            md.append(f"- **Existing URL**: [{web.existing_url}]({web.existing_url})")
        md.append(f"- **Audit Verdict**: {web.audit_verdict}")
        md.append(f"- **Lead Leakage Analysis**: {web.lead_leakage_analysis}")
        md.append(f"- **Recommended Website Type**: `{web.recommended_website_type}`")
        md.append(f"- **Projected Lead Growth**: **{web.estimated_lead_increase}**")
        
        if web.core_lead_magnets:
            md.append("\n#### 🧲 Core Lead Capture Hooks")
            for lm in web.core_lead_magnets:
                md.append(f"- ✓ {lm}")

        if web.essential_pages_and_sections:
            md.append("\n#### 📑 High-Converting Pages & Sections")
            for ep in web.essential_pages_and_sections:
                md.append(f"- {ep}")

        md.append(f"\n#### 📍 Local SEO Traffic Playbook\n{web.local_seo_traffic_playbook}")
        md.append("\n---\n")

        # Software Opportunity
        md.append("## 💡 Software Product Opportunity Assessment")
        md.append(f"### Verdict: {verdict_badge} (Confidence: {so.confidence_in_verdict})")
        md.append(f"\n> **Executive Summary**: {so.verdict_summary}\n")

        if so.recommended_product_ideas:
            md.append("### 🚀 Tailored Software Product Concepts")
            for idx, idea in enumerate(so.recommended_product_ideas, 1):
                md.append(f"#### {idx}. {idea.product_name} (`{idea.product_type}`)")
                md.append(f"- **Value Proposition**: {idea.core_value_proposition}")
                md.append(f"- **Problem Solved**: {idea.problem_it_solves}")
                md.append(f"- **Target Buyers**: {idea.target_buyers}")
                md.append(f"- **Suggested Monetization**: {idea.suggested_monetization_model}")
                md.append(f"- **Development Effort**: `{idea.feasibility_effort}`")
                md.append("- **MVP Features**:")
                for feat in idea.mvp_features:
                    md.append(f"  - {feat}")
                md.append("")

        if so.why_not_reasons:
            md.append("### ⚠️ Considerations & Risks Against Software")
            for r in so.why_not_reasons:
                md.append(f"- {r}")

        if so.existing_software_gaps:
            md.append("\n### 🔍 Observed Gaps & Operational Friction")
            for g in so.existing_software_gaps:
                md.append(f"- {g}")

        return "\n".join(md)

    @staticmethod
    def print_to_console(report: BrandingAnalysisReport):
        prof = report.profile
        loc = report.location
        bp = report.brand_profile
        so = report.software_opportunity
        imp = report.brand_improvements

        console.print()
        console.print(Panel(
            f"[bold cyan]@{prof.username}[/bold cyan] ({prof.full_name or 'N/A'})\n"
            f"[italic]{prof.biography or 'No bio'}[/italic]\n"
            f"[bold yellow]📍 Locality:[/bold yellow] {loc.detected_location} [dim]({loc.source})[/dim]\n"
            f"[dim]Followers: {prof.followers_count or '?'} | Posts: {prof.posts_count or '?'}[/dim]",
            title="[bold green]Instagram Profile & Geographic Presence[/bold green]",
            border_style="green"
        ))

        # Interests Table
        int_table = Table(title="🎯 Likes & Interests (With Citations)", box=box.ROUNDED)
        int_table.add_column("Topic / Interest", style="bold white", width=25)
        int_table.add_column("Category", style="cyan", width=16)
        int_table.add_column("Confidence", justify="center", width=12)
        int_table.add_column("Citations & Evidence", style="dim", width=45)

        for item in report.interests:
            conf_color = "green" if item.confidence == "High" else "yellow" if item.confidence == "Medium" else "white"
            cites = "\n".join([f"• [{c.source_type}] \"{c.content_excerpt[:60]}...\"" for c in item.citations])
            int_table.add_row(
                item.topic,
                item.category,
                f"[{conf_color}]{item.confidence}[/{conf_color}]",
                cites or "Profile context"
            )
        console.print(int_table)

        # Competitors Table
        if report.competitors:
            comp_table = Table(title="⚔️ Competitor Landscape (Local & Domain)", box=box.ROUNDED)
            comp_table.add_column("Competitor", style="bold cyan", width=22)
            comp_table.add_column("Type", style="yellow", width=18)
            comp_table.add_column("Location", style="dim", width=16)
            comp_table.add_column("Standing", style="green", width=14)
            comp_table.add_column("Competitive Differentiator", style="white", width=36)

            for c in report.competitors:
                comp_table.add_row(
                    c.name,
                    c.competitor_type,
                    c.location,
                    c.market_standing,
                    c.differentiator_vs_target
                )
            console.print(comp_table)

        # Brand & Quick Wins Panel
        quick_wins_text = "\n".join([f"• [bold green]✓[/bold green] {qw}" for qw in imp.quick_wins_under_30_days])
        console.print(Panel(
            f"[bold]Archetype:[/bold] [magenta]{bp.brand_archetype}[/magenta]\n"
            f"[bold]Primary Niche:[/bold] {bp.primary_niche}\n"
            f"[bold]Tone & Voice:[/bold] {bp.tone_and_voice}\n"
            f"[bold]Target Audience:[/bold] {bp.target_audience}\n\n"
            f"[bold yellow]⚡ Top Quick Wins (<30 Days):[/bold yellow]\n{quick_wins_text}",
            title="[bold magenta]🏛️ Brand Identity & Actionable Improvements[/bold magenta]",
            border_style="magenta"
        ))

        # Software Verdict Panel
        verdict_color = "green" if so.needs_software_product else "red"
        verdict_text = "YES - SOFTWARE PRODUCT HIGHLY RECOMMENDED" if so.needs_software_product else "NO - CUSTOM SOFTWARE NOT RECOMMENDED"
        
        console.print(Panel(
            f"[bold {verdict_color}]{verdict_text}[/bold {verdict_color}] (Confidence: {so.confidence_in_verdict})\n\n"
            f"{so.verdict_summary}",
            title="[bold yellow]💡 Software Product Opportunity[/bold yellow]",
            border_style=verdict_color
        ))

    @classmethod
    def save_reports(cls, report: BrandingAnalysisReport, output_prefix: Optional[str] = None) -> Dict[str, Path]:
        output_prefix = output_prefix or f"{report.profile.username}_analysis"
        md_file = settings.OUTPUT_DIR / f"{output_prefix}.md"
        json_file = settings.OUTPUT_DIR / f"{output_prefix}.json"

        # Markdown export
        md_content = cls.generate_markdown(report)
        md_file.write_text(md_content, encoding="utf-8")

        # Unified single master JSON export
        json_content = report.model_dump_json(indent=2)
        json_file.write_text(json_content, encoding="utf-8")

        return {"markdown": md_file, "json": json_file}
