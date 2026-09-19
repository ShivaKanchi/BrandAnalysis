import argparse
import sys
import getpass
from pathlib import Path

# Ensure UTF-8 output encoding for terminals supporting emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.prompt import Prompt, Confirm

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from core.scraper import InstagramScraper, LoginBarrierException
from core.analyzer import BrandAnalyzer
from core.report_generator import ReportGenerator, console
from core.models import ProfileData
from core.storage import StorageManager

def main():
    parser = argparse.ArgumentParser(
        description="BrandIntel AI: Personal Branding, Competitor Analysis, and Software Opportunity Intelligence"
    )
    parser.add_argument("--id", "-i", type=str, help="Instagram username / ID (e.g. hubermanlab, levelsio)")
    parser.add_argument("--location", "-l", type=str, default="", help="Brand locality/city override (e.g. 'Austin, TX', 'London')")
    parser.add_argument("--posts", "-p", type=int, default=settings.MAX_POSTS_TO_ANALYZE, help="Max posts to inspect (default: 12)")
    parser.add_argument("--model", "-m", type=str, default=settings.OLLAMA_MODEL, help=f"Ollama model name (default: {settings.OLLAMA_MODEL})")
    parser.add_argument("--login", action="store_true", help="Prompt for Instagram credentials to log in")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window during scraping")
    parser.add_argument("--manual", action="store_true", help="Manually paste profile bio and captions")
    parser.add_argument("--no-competitors", action="store_true", help="Skip web search competitor analysis")
    parser.add_argument("--export-prefix", type=str, default="", help="Custom filename prefix for report export")

    # New flags for Auto-Prospecting & Problem Radar & History
    parser.add_argument("--prospect", "-P", type=str, help="Auto-prospect businesses in a niche near a location (e.g. 'Gyms')")
    parser.add_argument("--radar", "-R", action="store_true", help="Run Software Engineer Problem & Micro-SaaS Radar")
    parser.add_argument("--limit", type=int, default=8, help="Limit items for prospecting or radar (default: 8)")
    parser.add_argument("--history", action="store_true", help="List all saved past analyses and comeback reports")

    args = parser.parse_args()

    # Handle View History Flag
    if args.history:
        console.rule("[bold cyan]📂 Saved Analysis History & Intelligence Index[/bold cyan]")
        saved_profiles = StorageManager.list_saved_profiles()
        if not saved_profiles:
            console.print("[yellow]No saved analyses found yet.[/yellow]")
            return
        
        from rich.table import Table
        from rich import box
        hist_table = Table(title="Saved Brand Analyses", box=box.ROUNDED)
        hist_table.add_column("Username", style="bold cyan", width=20)
        hist_table.add_column("Locality", style="dim", width=18)
        hist_table.add_column("Archetype", style="magenta", width=25)
        hist_table.add_column("Followers", style="yellow", width=12)
        hist_table.add_column("Saved Date", style="green", width=20)
        hist_table.add_column("Analyses", justify="center", width=10)

        for p in saved_profiles:
            hist_table.add_row(
                f"@{p['username']}",
                p["locality"],
                p["archetype"],
                p["followers"],
                p["timestamp_label"],
                str(p["history_count"])
            )
        console.print(hist_table)
        console.print("[dim]Use `python cli.py --id <username>` to run fresh analysis or view in Streamlit UI.[/dim]")
        return

    # Handle Problem Radar Flag
    if args.radar:
        console.rule("[bold cyan]⚡ Software Engineer Problem & Micro-SaaS Radar[/bold cyan]")
        from core.problem_radar import SoftwareProblemRadar
        with console.status("[bold green]Ingesting developer discussions across Hacker News, Reddit, Dev.to & Tech News...", spinner="bouncingBar"):
            radar_engine = SoftwareProblemRadar(model_name=args.model)
            radar_report = radar_engine.run_radar_analysis(max_items_per_source=args.limit)
        
        console.print(f"\n[bold green]Macro Trend Summary:[/bold green] {radar_report.macro_trend_summary}\n")
        for idx, prob in enumerate(radar_report.top_problems, 1):
            console.rule(f"[bold yellow]{idx}. {prob.problem_title} ({prob.category})[/bold yellow]")
            console.print(f"[bold]Severity:[/bold] {prob.severity_score}/10 | [bold]Velocity:[/bold] {prob.frequency_velocity}")
            console.print(f"[dim]{prob.summary_and_quotes}[/dim]\n")
            console.print(f"[bold cyan]🚀 Micro-SaaS Concept:[/bold cyan] {prob.recommended_microsaas.product_name_concept}")
            console.print(f"[bold]Value Prop:[/bold] {prob.recommended_microsaas.core_value_proposition}")
            console.print(f"[bold]Monetization:[/bold] {prob.recommended_microsaas.monetization_model} | [bold]Target ICP:[/bold] {prob.recommended_microsaas.target_icp}")
            console.print(f"[bold]MVP Features:[/bold] {', '.join(prob.recommended_microsaas.mvp_features)}\n")
        
        out_file = Path("reports") / f"dev_problem_radar_{radar_report.timeframe.replace(' ', '_')}.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(radar_report.model_dump_json(indent=2))
        console.print(f"[bold green]✓ Problem Radar JSON saved to:[/bold green] [cyan]{out_file}[/cyan]")
        return

    # Handle Auto-Prospecting Flag
    if args.prospect:
        console.rule(f"[bold cyan]📍 Auto-Prospecting: {args.prospect} in {args.location or 'Local Region'}[/bold cyan]")
        from core.auto_prospector import AutoProspector
        loc = args.location or Prompt.ask("[bold yellow]Enter Target Locality / City[/bold yellow]")
        with console.status(f"[bold green]Scraping Google Maps for '{args.prospect}' in '{loc}' & resolving Instagram handles...", spinner="dots"):
            prospector = AutoProspector(headless=not args.no_headless)
            lead_report = prospector.discover_leads(niche_or_query=args.prospect, location=loc, limit=args.limit)
        
        console.print(f"\n[bold green]Found {lead_report.total_places_scanned} places ({lead_report.leads_with_instagram} verified Instagram handles):[/bold green]\n")
        for idx, lead in enumerate(lead_report.leads, 1):
            ig_str = f"[magenta]@{lead.instagram_handle}[/magenta]" if lead.instagram_handle else "[dim]None[/dim]"
            console.print(f"[bold]{idx}. {lead.business_name}[/bold] (⭐ {lead.rating or 'N/A'}) - IG: {ig_str}")
            if lead.website:
                console.print(f"   [dim]Site: {lead.website}[/dim]")
        
        out_file = Path("reports") / f"leads_{loc.replace(' ', '_')}.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(lead_report.model_dump_json(indent=2))
        console.print(f"\n[bold green]✓ Leads JSON saved to:[/bold green] [cyan]{out_file}[/cyan]")
        return

    console.rule("[bold cyan]BrandIntel AI: Strategic Personal Branding & Competitor Intelligence[/bold cyan]")

    username = args.id
    if not username and not args.manual:
        username = Prompt.ask("[bold yellow]Enter Instagram Username / ID[/bold yellow]")

    headless = not args.no_headless

    # Handle manual input mode
    if args.manual:
        console.print("[green]Manual Profile Ingestion Mode[/green]")
        manual_username = username or Prompt.ask("Instagram Username")
        console.print("[dim]Paste the profile bio and captions below. Type 'EOF' on a new line when done:[/dim]")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            except EOFError:
                break
        raw_text = "\n".join(lines)
        profile_data = InstagramScraper.parse_manual_input(manual_username, raw_text)
    else:
        # Automated scraping mode
        insta_user = settings.INSTAGRAM_USERNAME
        insta_pass = settings.INSTAGRAM_PASSWORD
        session_id = settings.INSTAGRAM_SESSIONID

        if args.login:
            insta_user = Prompt.ask("Instagram Username")
            insta_pass = getpass.getpass("Instagram Password: ")

        scraper = InstagramScraper(
            username=insta_user,
            password=insta_pass,
            sessionid=session_id,
            headless=headless
        )

        with console.status(f"[bold green]Fetching profile @{username} with Playwright...", spinner="dots"):
            try:
                profile_data = scraper.scrape_profile(username, max_posts=args.posts)
            except LoginBarrierException:
                console.print("\n[bold red]⚠️ Instagram Login Barrier Encountered![/bold red]")
                should_login = Confirm.ask("Would you like to provide login credentials to proceed?")
                if should_login:
                    u = Prompt.ask("Instagram Username")
                    p = getpass.getpass("Instagram Password: ")
                    scraper.username = u
                    scraper.password = p
                    profile_data = scraper.scrape_profile(username, max_posts=args.posts)
                else:
                    console.print("[yellow]Falling back to manual text input...[/yellow]")
                    raw_text = Prompt.ask("Paste any bio or post text you have for this user")
                    profile_data = InstagramScraper.parse_manual_input(username, raw_text)
            except Exception as e:
                console.print(f"[bold red]Failed to scrape profile:[/bold red] {e}")
                sys.exit(1)

    console.print(f"[bold green]✓[/bold green] Profile data acquired: [bold]{len(profile_data.posts)}[/bold] posts collected.")

    # Run AI Analysis & Competitor Discovery via Ollama
    with console.status(f"[bold cyan]Running brand analysis & competitor discovery via Ollama ({args.model})...", spinner="bouncingBar"):
        try:
            analyzer = BrandAnalyzer(model_name=args.model)
            report = analyzer.analyze_profile(
                profile_data,
                user_location_override=args.location.strip() or None,
                enable_competitor_research=not args.no_competitors
            )
        except Exception as e:
            console.print(f"[bold red]Analysis failed:[/bold red] {e}")
            sys.exit(1)

    # Display Rich Terminal Output
    ReportGenerator.print_to_console(report)

    # Save Unified Master JSON and Markdown Reports (Auto-saved to history & prefix)
    prefix = args.export_prefix or f"{profile_data.username}_master_intelligence"
    saved_paths = ReportGenerator.save_reports(report, output_prefix=prefix)
    auto_saved = StorageManager.auto_save_report(report)

    console.print()
    console.print(f"[bold green]✓ Auto-saved to History Index:[/bold green] [cyan]{auto_saved['json']}[/cyan]")
    console.print(f"[bold green]✓ Unified Master JSON saved to:[/bold green] [cyan]{saved_paths['json']}[/cyan]")
    console.print(f"[bold green]✓ Markdown strategic report saved to:[/bold green] [cyan]{saved_paths['markdown']}[/cyan]")
    console.rule("[bold cyan]Analysis Complete[/bold cyan]")

if __name__ == "__main__":
    main()
