import sys
import html
from pathlib import Path
import streamlit as st
import requests

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from core.scraper import InstagramScraper, LoginBarrierException
from core.analyzer import BrandAnalyzer
from core.auto_prospector import AutoProspector
from core.problem_radar import SoftwareProblemRadar
from core.report_generator import ReportGenerator
from core.models import (
    ProfileData,
    BrandingAnalysisReport,
    LeadProspectingReport,
    SoftwareProblemRadarReport
)
from core.storage import StorageManager
from core.icons import lucide

st.set_page_config(
    page_title="BrandAnalysis AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html(html_str: str):
    """
    Safely renders HTML via st.markdown by stripping leading indentation and empty lines.
    This prevents CommonMark markdown parsers from treating indented lines or lines
    following blank space as raw <pre><code> code blocks.
    """
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

# Custom High-End Styling: Prevent dimming, three-dot pulsing loader & Lucide icon formatting
st.markdown(f"""
<!-- Load Lucide Web Component Support -->
<script src="https://unpkg.com/lucide@latest"></script>
<style>
    /* Completely hide deploy button, options menu, and footer while keeping sidebar toggle button visible */
    [data-testid="stAppDeployButton"], .stDeployButton, footer, #MainMenu {{
        display: none !important;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* PREVENT PAGE OPACITY DIMMING ON RERUN (PREVENTS WASHED-OUT / GREY SCREEN) */
    [data-testid="stAppViewContainer"],
    .stApp[data-test-script-state="running"],
    .stApp[data-test-script-state="running"] [data-testid="stAppViewContainer"],
    .stApp[data-test-script-state="running"] .main,
    .stApp[data-test-script-state="running"] .block-container,
    .stApp[data-test-script-state="running"] [data-testid="stMainBlockContainer"],
    .stApp[data-test-script-state="running"] div {{
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }}

    /* THREE-DOT PULSING ANIMATED LOADER FOR STREAMLIT SPINNER */
    [data-testid="stSpinner"],
    .stSpinner {{
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        margin: 1.25rem 0 !important;
        box-sizing: border-box !important;
    }}

    [data-testid="stSpinner"] > div,
    .stSpinner > div {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 16px !important;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.09) 0%, rgba(30, 41, 59, 0.85) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.35) !important;
        border-radius: 10px !important;
        padding: 1rem 1.4rem !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        box-sizing: border-box !important;
    }}

    /* Target the spinner icon specifically, NOT the wrapper div */
    [data-testid="stSpinnerIcon"] svg,
    [data-testid="stSpinner"] svg {{
        display: none !important;
    }}

    [data-testid="stSpinnerIcon"] {{
        width: 34px !important;
        min-width: 34px !important;
        max-width: 34px !important;
        height: 12px !important;
        min-height: 12px !important;
        background: radial-gradient(circle, #10B981 3.5px, transparent 3.5px) no-repeat center !important;
        border: none !important;
        position: relative !important;
        display: inline-block !important;
        animation: threeDotsPulse 1.2s infinite ease-in-out both !important;
        animation-delay: -0.16s !important;
        box-shadow: none !important;
        flex-shrink: 0 !important;
    }}

    [data-testid="stSpinnerIcon"]::before,
    [data-testid="stSpinnerIcon"]::after {{
        content: "" !important;
        position: absolute !important;
        width: 7px !important;
        height: 7px !important;
        border-radius: 50% !important;
        background-color: #10B981 !important;
        top: 2.5px !important;
    }}

    [data-testid="stSpinnerIcon"]::before {{
        left: 0 !important;
        animation: threeDotsPulse 1.2s infinite ease-in-out both !important;
        animation-delay: -0.32s !important;
    }}

    [data-testid="stSpinnerIcon"]::after {{
        right: 0 !important;
        animation: threeDotsPulse 1.2s infinite ease-in-out both !important;
        animation-delay: 0s !important;
    }}

    @keyframes threeDotsPulse {{
        0%, 80%, 100% {{
            transform: scale(0.35);
            opacity: 0.25;
        }}
        40% {{
            transform: scale(1.15);
            opacity: 1;
        }}
    }}

    /* Ensure spinner text wrapper stretches horizontally and NEVER breaks per letter */
    [data-testid="stSpinner"] div:has(> [role="status"]),
    [data-testid="stSpinner"] [role="status"],
    [data-testid="stSpinner"] .stMarkdown {{
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }}

    [data-testid="stSpinner"] p,
    [data-testid="stSpinner"] span,
    [data-testid="stSpinner"] [role="status"] * {{
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        font-size: 0.96rem !important;
        font-weight: 500 !important;
        color: #E2E8F0 !important;
        line-height: 1.5 !important;
        margin: 0 !important;
    }}

    /* Scope text wrapping to content containers so UI controls (sliders, numbers) are never split */
    .profile-hero *,
    .stats-grid *,
    .stat-card *,
    .panel-card *,
    .panel-card-accent *,
    .bio-container *,
    .citation-box,
    [data-testid="stMetricValue"] *,
    [data-testid="stMetricLabel"] *,
    .stMarkdown:not([data-testid="stSpinner"] *) p {{
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
        text-overflow: unset !important;
    }}

    /* Slider thumb and tooltips MUST strictly stay on ONE line */
    [data-testid="stSlider"],
    [data-testid="stSlider"] *,
    [data-baseweb="slider"],
    [data-baseweb="slider"] *,
    div[role="slider"],
    div[role="slider"] * {{
        white-space: nowrap !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        min-width: max-content !important;
    }}

    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1240px;
    }}

    /* Module Explanation Banner */
    .module-banner {{
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        border: 1px solid #334155;
        border-left: 4px solid #10B981;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    .module-banner-header {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
        margin-bottom: 0.4rem;
    }}
    .module-banner-title {{
        font-size: 1.45rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
        letter-spacing: -0.02em;
    }}
    .module-banner-subtitle {{
        font-size: 0.92rem;
        color: #94A3B8;
        margin: 0.2rem 0 0 0;
    }}
    .module-banner-desc {{
        font-size: 0.92rem;
        color: #CBD5E1;
        line-height: 1.6;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid rgba(51, 65, 85, 0.6);
    }}

    /* Hero Profile Container */
    .profile-hero {{
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .profile-hero-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 1rem;
        margin-bottom: 1.25rem;
    }}
    .profile-handle {{
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }}
    .profile-subname {{
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 0.2rem;
    }}
    
    /* Stats Grid */
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1.25rem;
    }}
    .stat-card {{
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.9rem 1rem;
    }}
    .stat-card-title {{
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .stat-card-value {{
        font-size: 1.15rem;
        font-weight: 600;
        color: #F1F5F9;
        line-height: 1.35;
        white-space: normal !important;
        word-break: break-word !important;
    }}
    .stat-card-sub {{
        font-size: 0.75rem;
        color: #64748B;
        margin-top: 0.2rem;
    }}

    /* Bio Box */
    .bio-container {{
        background-color: #0F172A;
        border: 1px solid #334155;
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
    }}
    .bio-label {{
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #10B981;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .bio-content {{
        font-size: 0.95rem;
        color: #E2E8F0;
        line-height: 1.5;
        white-space: pre-line;
    }}

    /* Pill Badges */
    .pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        line-height: 1;
    }}
    .pill-green {{ background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .pill-yellow {{ background-color: rgba(234, 179, 8, 0.15); color: #FACC15; border: 1px solid rgba(234, 179, 8, 0.3); }}
    .pill-blue {{ background-color: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .pill-purple {{ background-color: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }}
    .pill-gray {{ background-color: rgba(148, 163, 184, 0.15); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.3); }}

    /* Cards */
    .panel-card {{
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }}
    .panel-card-accent {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(30, 41, 59, 1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }}
    .citation-box {{
        background-color: #0F172A;
        border-left: 3px solid #10B981;
        padding: 0.6rem 0.9rem;
        border-radius: 0 6px 6px 0;
        margin-top: 0.5rem;
        font-size: 0.88rem;
        color: #94A3B8;
        font-style: italic;
    }}
</style>
""", unsafe_allow_html=True)

# Helper: Detect Ollama models with embedding models filtered out
from core.ollama_helper import OllamaManager

def get_ollama_models(host: str):
    status = OllamaManager.check_status(host)
    if status.get("online") and status.get("installed_models"):
        chat_models = [
            m for m in status["installed_models"]
            if not any(x in m.lower() for x in ["embed", "bge", "minilm"])
        ]
        return chat_models if chat_models else status["installed_models"]
    return ["llama3.2", "mistral", "llama3:8b", "qwen2.5:7b"]

# Sidebar Navigation & Settings
with st.sidebar:
    st.markdown(f'<div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.4rem; color: #94A3B8; display: flex; align-items: center; gap: 0.4rem;">{lucide("compass", 16, "#10B981")} NAVIGATION</div>', unsafe_allow_html=True)
    app_mode = st.radio(
        "Navigation",
        options=[
            "Lead Harvester",
            "Brand Audit",
            "Saved Reports",
            "Problem Radar"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(f'<div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.4rem; color: #94A3B8; display: flex; align-items: center; gap: 0.4rem;">{lucide("settings", 16, "#38BDF8")} ENGINE CONFIGURATION</div>', unsafe_allow_html=True)
    ollama_host = st.text_input("Ollama Base URL", value=settings.OLLAMA_BASE_URL)
    
    ollama_status = OllamaManager.check_status(ollama_host)
    if ollama_status.get("online"):
        st.caption(f"🟢 **Ollama Connected** ({len(ollama_status.get('installed_models', []))} model(s) available)")
    else:
        st.caption("⚪ **Ollama Offline** (Auto-failover active. Run `ollama serve` to start local AI)")

    available_models = get_ollama_models(ollama_host)
    default_model_idx = 0

    selected_model = st.selectbox(
        "Active AI Model",
        options=available_models,
        index=default_model_idx
    )
    
    if app_mode == "Brand Audit":
        st.markdown("---")
        st.markdown(f'<div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.4rem; color: #94A3B8; display: flex; align-items: center; gap: 0.4rem;">{lucide("bar-chart-3", 16, "#A78BFA")} SCRAPING DEPTH</div>', unsafe_allow_html=True)
        max_posts = st.slider(
            "Posts to Read & Analyze",
            min_value=3,
            max_value=50,
            value=settings.MAX_POSTS_TO_ANALYZE,
            step=1,
            help="Controls how many recent Instagram posts and captions the scraper inspects (3 to 50)."
        )

        with st.expander("Instagram Credentials (Optional)"):
            st.caption("Provide only if you hit an Instagram login barrier.")
            ig_user = st.text_input("Username", value=settings.INSTAGRAM_USERNAME)
            ig_pass = st.text_input("Password", type="password", value=settings.INSTAGRAM_PASSWORD)
            ig_session = st.text_input("Session Cookie", value=settings.INSTAGRAM_SESSIONID)
    else:
        max_posts = settings.MAX_POSTS_TO_ANALYZE
        ig_user = settings.INSTAGRAM_USERNAME
        ig_pass = settings.INSTAGRAM_PASSWORD
        ig_session = settings.INSTAGRAM_SESSIONID

# ==============================================================================
# MODE 1: LEAD HARVESTER (DEFAULT LANDING PAGE)
# ==============================================================================
if app_mode == "Lead Harvester":
    st.markdown(f"""
    <div class="module-banner">
        <div class="module-banner-header">
            {lucide("target", 24, "#10B981")}
            <div>
                <h3 class="module-banner-title">Lead Harvester & Local Prospector</h3>
                <div class="module-banner-subtitle">High-intent business lead generation from Google Maps & automated Instagram discovery</div>
            </div>
        </div>
        <div class="module-banner-desc">
            Prospect local businesses in any target niche or city. The engine scrapes live Google Maps listings, crawls company websites for social links, and automatically surfaces verified Instagram profiles ready for deep brand intelligence.
        </div>
    </div>
    """, unsafe_allow_html=True)

    total_registry_leads = StorageManager.get_leads_registry_count()

    with st.container():
        c_niche, c_loc, c_lim, c_run = st.columns([2.5, 2.5, 1, 1.5])
        with c_niche:
            search_niche = st.text_input("Business Niche / Category", value="Gyms", placeholder="e.g. Specialty Coffee, Dentists, Gyms")
        with c_loc:
            search_locality = st.text_input("Locality / City", value="Kandivali, Mumbai", placeholder="e.g. Austin TX, Bandra Mumbai")
        with c_lim:
            search_limit = st.number_input("Max Places", min_value=3, max_value=25, value=6, step=1)
        with c_run:
            st.write("")
            st.write("")
            start_prospect = st.button("Harvest Leads", type="primary", use_container_width=True)

        c_opt1, c_opt2, c_opt3 = st.columns([1.2, 1.2, 1])
        with c_opt1:
            fresh_only = st.checkbox(
                "✨ Fresh Leads Only (Skip previously harvested)",
                value=True,
                help="Checks against the leads database to ensure you never get the same leads repeatedly."
            )
        with c_opt2:
            auto_expand = st.checkbox(
                "🔄 Auto-Expand Neighborhoods (If top results saturated)",
                value=True,
                help="Automatically generates sub-localities (East/West/Central) or sub-niche queries if top listings have already been gathered."
            )
        with c_opt3:
            use_browser = st.checkbox(
                "🌐 Browser Scraper",
                value=False,
                help="Launch headless Chromium. If unchecked, uses the fast multi-tier directory search engine."
            )

    if start_prospect:
        with st.spinner(f"Harvesting fresh business leads in '{search_locality}' and verifying commercial intent..."):
            prospector = AutoProspector(headless=True, use_playwright=use_browser)
            try:
                lead_report = prospector.discover_leads(
                    niche_or_query=search_niche,
                    location=search_locality,
                    limit=search_limit,
                    exclude_previously_seen=fresh_only,
                    auto_expand=auto_expand
                )
                st.session_state["lead_report"] = lead_report
            except Exception as e:
                st.error(f"Lead prospecting failed: {e}")

    if "lead_report" in st.session_state:
        l_rep: LeadProspectingReport = st.session_state["lead_report"]
        
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Fresh Leads Discovered", l_rep.fresh_leads_count or len(l_rep.leads))
        with m2:
            st.metric("Previously Seen Skipped", l_rep.recycled_leads_skipped)
        with m3:
            st.metric("High-Intent Prospects", l_rep.high_intent_count)
        with m4:
            st.metric("Total in Lead Registry", l_rep.total_registry_leads or StorageManager.get_leads_registry_count())

        st.subheader("Discovered Business Leads")
        
        for idx, lead in enumerate(l_rep.leads, 1):
            with st.container():
                intent_pill_class = (
                    "pill-green" if lead.lead_intent_score == "High Intent"
                    else "pill-yellow" if lead.lead_intent_score == "Promising"
                    else "pill-gray"
                )

                signals_html = ""
                if lead.authenticity_signals:
                    badges = "".join([f"<span class='pill pill-blue' style='font-size: 0.78rem; margin-right: 0.35rem;'>{html.escape(sig)}</span>" for sig in lead.authenticity_signals])
                    signals_html = f"<div style='margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.35rem;'>{badges}</div>"

                pitch_html = ""
                if lead.opportunity_angle:
                    pitch_html = f"""
                    <div style="margin-top: 0.65rem; padding: 0.5rem 0.75rem; background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38BDF8; border-radius: 4px; font-size: 0.85rem; color: #E2E8F0;">
                        <strong>Targeted Pitch Angle:</strong> {html.escape(lead.opportunity_angle)}
                    </div>
                    """

                render_html(f"""
                <div class="panel-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                                <h4 style="margin: 0; color: #F8FAFC; font-size: 1.15rem;">{idx}. {html.escape(lead.business_name)}</h4>
                                <span class="pill {intent_pill_class}">{html.escape(lead.lead_intent_score)}</span>
                                <span class="pill pill-green">✨ Fresh Lead</span>
                            </div>
                            <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.3rem; display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
                                {lucide("map-pin", 14, "#94A3B8")} {html.escape(lead.address_or_location or '')} &nbsp;|&nbsp; {lucide("star", 14, "#FACC15")} {html.escape(lead.rating or 'N/A')} ({html.escape(lead.review_count or '0')} reviews)
                                {f"&nbsp;|&nbsp; {lucide('phone', 14, '#38BDF8')} {html.escape(lead.phone)}" if lead.phone else ""}
                            </div>
                        </div>
                        <div>
                            <span class="pill {'pill-green' if lead.instagram_handle else 'pill-yellow'}">{lead.lead_status}</span>
                        </div>
                    </div>
                    {signals_html}
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; font-size: 0.9rem;">
                        <div><strong>Website:</strong> {f"<a href='{lead.website}' target='_blank' style='color: #60A5FA;'>{html.escape(lead.website)}</a>" if lead.website else "<span style='color: #EF4444;'>None (High Opportunity)</span>"}</div>
                        <div><strong>Instagram:</strong> {f"<a href='{lead.instagram_url}' target='_blank' style='color: #E879F9; font-weight: bold;'>@{html.escape(lead.instagram_handle)}</a>" if lead.instagram_handle else "Not Found"}</div>
                        <div><strong>Google Maps:</strong> {f"<a href='{lead.maps_url}' target='_blank' style='color: #38BDF8;'>View Listing ↗</a>" if lead.maps_url else "N/A"}</div>
                    </div>
                    {pitch_html}
                </div>
                """)
                
                if lead.instagram_handle:
                    if st.button(f"Analyze @{lead.instagram_handle} in Brand Audit", key=f"btn_lead_{idx}"):
                        st.session_state["selected_prospect_handle"] = lead.instagram_handle
                        st.session_state["location_override"] = lead.address_or_location
                        st.success(f"Selected @{lead.instagram_handle}! Switch to 'Brand Audit' in the left sidebar to run the audit.")

        st.markdown("---")
        c_dl, c_clr = st.columns([2, 1])
        with c_dl:
            st.download_button(
                "Download Discovered Leads JSON",
                data=l_rep.model_dump_json(indent=2),
                file_name=f"leads_{l_rep.target_locality.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )
        with c_clr:
            with st.expander("Reset Registry History"):
                st.caption(f"Currently tracking {StorageManager.get_leads_registry_count()} unique business leads across past runs.")
                if st.button("Clear Leads Database", type="secondary", use_container_width=True):
                    StorageManager.clear_leads_registry()
                    st.success("Lead registry cleared! Next search will start completely fresh.")


# ==============================================================================
# MODE 2: BRAND ANALYSIS & PROFILE AUDIT
# ==============================================================================
elif app_mode == "Brand Audit":
    st.markdown(f"""
    <div class="module-banner">
        <div class="module-banner-header">
            {lucide("zap", 24, "#38BDF8")}
            <div>
                <h3 class="module-banner-title">Brand Audit & Profile Intelligence</h3>
                <div class="module-banner-subtitle">Deep-dive Instagram intelligence, verified citations, competitor analysis & software blueprints</div>
            </div>
        </div>
        <div class="module-banner-desc">
            Perform end-to-end intelligence audits on any Instagram creator or business. Reads recent posts, extracts granular domain interests backed by verified citations, audits website lead leakage, and synthesizes local competitors and custom Micro-SaaS software opportunities.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col_user, col_loc, col_btn = st.columns([3.5, 2.5, 1.2])
        with col_user:
            default_handle = st.session_state.get("selected_prospect_handle", "")
            target_username = st.text_input(
                "Instagram Handle",
                value=default_handle,
                placeholder="e.g. bananaleaf_india_",
                label_visibility="collapsed"
            )
        with col_loc:
            location_input = st.text_input(
                "Location / Locality",
                placeholder="City/Suburbs (Auto-detected if empty)",
                label_visibility="collapsed"
            )
        with col_btn:
            start_auto = st.button("Analyze Brand", type="primary", use_container_width=True)

    # Execution Logic
    profile_to_analyze = None
    location_override = location_input.strip() if location_input else None

    if start_auto and target_username:
        clean_user = target_username.strip().lstrip("@")
        with st.spinner(f"Fetching @{clean_user} (reading {max_posts} posts)..."):
            scraper = InstagramScraper(
                username=ig_user if 'ig_user' in locals() else settings.INSTAGRAM_USERNAME,
                password=ig_pass if 'ig_pass' in locals() else settings.INSTAGRAM_PASSWORD,
                sessionid=ig_session if 'ig_session' in locals() else settings.INSTAGRAM_SESSIONID,
                headless=True
            )
            try:
                profile_to_analyze = scraper.scrape_profile(clean_user, max_posts=max_posts)
                st.session_state["current_profile"] = profile_to_analyze
                st.session_state["location_override"] = location_override
                if "current_report" in st.session_state:
                    del st.session_state["current_report"]
            except LoginBarrierException:
                st.warning("Instagram requires login for this profile. Enter your credentials in the sidebar.")
            except Exception as e:
                st.error(f"Error fetching profile: {e}")

    # If we have a profile loaded
    if "current_profile" in st.session_state:
        profile: ProfileData = st.session_state["current_profile"]
        loc_override = st.session_state.get("location_override")

        # Run AI Analysis if not cached
        if "current_report" not in st.session_state or st.session_state["current_report"].profile.username != profile.username:
            with st.spinner(f"Running intelligence analysis & competitor discovery via Ollama ({selected_model})..."):
                analyzer = BrandAnalyzer(ollama_url=ollama_host, model_name=selected_model)
                try:
                    report = analyzer.analyze_profile(profile, user_location_override=loc_override)
                    st.session_state["current_report"] = report
                    # Automatically save analysis data for instant comeback
                    saved_paths = StorageManager.auto_save_report(report)
                    st.session_state["last_auto_saved"] = saved_paths
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

        report: BrandingAnalysisReport = st.session_state["current_report"]
        prof = report.profile
        loc = report.location
        soc = report.social_status
        bp = report.brand_profile
        imp = report.brand_improvements
        mkt = report.market_analysis
        so = report.software_opportunity
        web = report.website_opportunity

        # --- BEAUTIFUL, UN-TRUNCATED HERO PROFILE CARD ---
        verified_mark = f' <span title="Verified">{lucide("check-circle-2", 18, "#38BDF8")}</span>' if prof.is_verified else ""
        posts_count_str = str(len(prof.posts)) if prof.posts else (prof.posts_count or "N/A")
        soc_pill_class = "pill-green" if "strong" in soc.cross_platform_presence_score.lower() else "pill-yellow" if "moderate" in soc.cross_platform_presence_score.lower() else "pill-blue"
        web_pill_class = "pill-green" if web.has_website else "pill-yellow"
        web_pill_label = "Website: Active" if web.has_website else "Website: None (Lead Leak)"

        render_html(f"""
        <div class="profile-hero">
            <div class="profile-hero-header">
                <div>
                    <h2 class="profile-handle">@{html.escape(prof.username)}{verified_mark}</h2>
                    <div class="profile-subname">{html.escape(prof.full_name or 'Brand Profile')}</div>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                <span class="pill pill-green">{lucide("save", 12, "#34D399")} Auto-Saved</span>
                <span class="pill {web_pill_class}">{html.escape(web_pill_label)}</span>
                <span class="pill {soc_pill_class}">Ecosystem: {html.escape(soc.cross_platform_presence_score)}</span>
            </div>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-title">{lucide("map-pin", 14, "#94A3B8")} Locality / Region</div>
                    <div class="stat-card-value">{html.escape(loc.detected_location)}</div>
                    <div class="stat-card-sub">Source: {html.escape(loc.source)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">{lucide("users", 14, "#94A3B8")} Audience Reach</div>
                    <div class="stat-card-value">{html.escape(prof.followers_count or 'N/A')} Followers</div>
                    <div class="stat-card-sub">{html.escape(prof.following_count or '0')} Following</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">{lucide("camera", 14, "#94A3B8")} Content Sampled</div>
                    <div class="stat-card-value">{posts_count_str} Posts Analyzed</div>
                    <div class="stat-card-sub">Direct post captions & media</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">{lucide("building-2", 14, "#94A3B8")} Brand Archetype</div>
                    <div class="stat-card-value">{html.escape(bp.brand_archetype)}</div>
                    <div class="stat-card-sub">Niche: {html.escape(bp.primary_niche)}</div>
                </div>
            </div>
            <div class="bio-container">
                <div class="bio-label">{lucide("file-text", 14, "#10B981")} Instagram Biography</div>
                <div class="bio-content">{html.escape(prof.biography or 'No bio provided')}</div>
            </div>
        </div>
        """)

        # --- ORGANIZED TABS ---
        tab_int, tab_brand, tab_web, tab_imp, tab_comp, tab_soft, tab_json = st.tabs([
            "Likes & Interests",
            "Brand & Social Status",
            "Website & Lead Engine",
            "Growth Roadmap",
            "Competitors & Market",
            "Software Opportunity",
            "Unified Master JSON"
        ])

        # TAB 1: LIKES & INTERESTS (WITH CITATIONS & CONFIDENCE)
        with tab_int:
            st.subheader("Granular Likes, Domain Interests & Passions")
            st.caption("Every detected interest is anchored by explicit quotations and citations from the profile.")

            cats = sorted(list(set([i.category for i in report.interests])))
            sel_cat = st.selectbox("Filter by Category", options=["All Categories"] + cats)
            filtered = [i for i in report.interests if sel_cat == "All Categories" or i.category == sel_cat]

            for item in filtered:
                badge_pill = "pill-green" if item.confidence == "High" else "pill-yellow" if item.confidence == "Medium" else "pill-gray"
                with st.container():
                    st.markdown(f"""
                    <div class="panel-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <h4 style="margin: 0; color: #F8FAFC; font-size: 1.15rem;">{html.escape(item.topic)}</h4>
                            <div>
                                <span class="pill pill-blue">{html.escape(item.category)}</span>
                                <span class="pill {badge_pill}">{html.escape(item.confidence)} Confidence</span>
                            </div>
                        </div>
                        <p style="color: #94A3B8; font-size: 0.92rem; margin-bottom: 0.5rem;">
                            <strong>Reasoning:</strong> {html.escape(item.confidence_reasoning)}
                        </p>
                        <div>
                            <strong style="color: #CBD5E1; font-size: 0.88rem;">Evidence & Citations ({len(item.citations)}):</strong>
                        </div>
                    """, unsafe_allow_html=True)

                    for c in item.citations:
                        src_tag = f"[{c.source_type.upper()}]"
                        if c.post_index:
                            src_tag += f" Post #{c.post_index}"
                        st.markdown(f"""
                        <div class="citation-box">
                            <strong style="color: #10B981;">{html.escape(src_tag)}:</strong> "{html.escape(c.content_excerpt)}"
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

        # TAB 2: BRAND IDENTITY & SOCIAL FOOTPRINT
        with tab_brand:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("building-2", 18, "#38BDF8")} Brand Identity & Voice</h4>
                    <p><strong>Brand Archetype:</strong> <span class="pill pill-blue">{html.escape(bp.brand_archetype)}</span></p>
                    <p><strong>Primary Niche:</strong> {html.escape(bp.primary_niche)}</p>
                    <p><strong>Secondary Niches:</strong> {html.escape(', '.join(bp.secondary_niches) or 'None')}</p>
                    <p><strong>Tone & Voice:</strong> {html.escape(bp.tone_and_voice)}</p>
                    <p><strong>Current Monetization:</strong> {html.escape(', '.join(bp.current_monetization_methods) or 'None evident')}</p>
                </div>
                """, unsafe_allow_html=True)
    
            with col_b2:
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("target", 18, "#A78BFA")} Target Audience & Reach</h4>
                    <p>{html.escape(bp.target_audience)}</p>
                    <div style="margin-top: 1rem; border-top: 1px solid #334155; padding-top: 0.75rem;">
                        <strong>Cross-Platform Status:</strong> <span class="pill {soc_pill_class}">{html.escape(soc.cross_platform_presence_score)}</span>
                        <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.3rem;">{html.escape(soc.social_ecosystem_overview)}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
            if soc.linked_socials:
                st.markdown(f'<div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("globe", 18, "#38BDF8")} Discovered Outbound Social Links</div>', unsafe_allow_html=True)
                cols_s = st.columns(len(soc.linked_socials) if len(soc.linked_socials) <= 4 else 4)
                for i, s in enumerate(soc.linked_socials):
                    with cols_s[i % len(cols_s)]:
                        st.markdown(f"""
                        <div class="panel-card" style="padding: 0.75rem 1rem;">
                            <strong style="display: flex; align-items: center; gap: 0.35rem;">{lucide("link", 14, "#94A3B8")} {html.escape(s.platform)}</strong>
                            <a href="{s.url}" target="_blank" style="font-size: 0.85rem; color: #38BDF8; word-break: break-all;">{s.url}</a>
                            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.3rem;">{html.escape(s.status_notes or '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
            st.markdown(f'<div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("layers", 18, "#A78BFA")} Content Pillars</div>', unsafe_allow_html=True)
            cols_cp = st.columns(len(bp.content_pillars) if bp.content_pillars else 1)
            for i, cp in enumerate(bp.content_pillars):
                with cols_cp[i % len(cols_cp)]:
                    st.info(f"**{cp}**")
    
        # TAB 3: WEBSITE AUDIT & INBOUND LEAD ENGINE
        with tab_web:
            st.markdown(f'<div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.2rem; display: flex; align-items: center; gap: 0.5rem;">{lucide("globe", 22, "#38BDF8")} Website Presence & Inbound Lead Engine</div>', unsafe_allow_html=True)
            st.caption("Audits whether the brand has a dedicated website to capture high-intent Google Search and social traffic.")
    
            if not web.has_website:
                st.markdown(f"""
                <div class="panel-card-accent" style="border-left: 4px solid #F87171; background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(30, 41, 59, 1) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <h3 style="color: #F87171; margin: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("alert-triangle", 20, "#F87171")} No Dedicated Website Found — Critical Lead Leakage</h3>
                        <span class="pill pill-yellow">Expected Boost: {html.escape(web.estimated_lead_increase)}</span>
                    </div>
                    <p style="color: #E2E8F0; margin-top: 0.75rem; font-size: 1.02rem;">{html.escape(web.lead_leakage_analysis)}</p>
                </div>
                """, unsafe_allow_html=True)
    
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #38BDF8; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("rocket", 18, "#38BDF8")} Recommended Website Blueprint: {html.escape(web.recommended_website_type)}</h4>
                    <p style="color: #CBD5E1;">By establishing an on-demand booking website, <strong>@{html.escape(prof.username)}</strong> can turn casual Instagram visitors into confirmed, paid customers 24/7 without manual phone call friction.</p>
                </div>
                """, unsafe_allow_html=True)
    
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    for lm in web.core_lead_magnets:
                        st.markdown(f"- **{lm}**")
                    st.markdown("</div>", unsafe_allow_html=True)
    
                with col_w2:
                    st.markdown(f"""
                    <div class="panel-card">
                        <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("file-text", 18, "#94A3B8")} High-Converting Pages & Architecture</h4>
                        <p style="font-size: 0.88rem; color: #94A3B8;">Must-have sections to build local authority and eliminate booking hesitation:</p>
                    """, unsafe_allow_html=True)
                    for ep in web.essential_pages_and_sections:
                        st.markdown(f"- {ep}")
                    st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #34D399; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("map-pin", 18, "#34D399")} Local Google Search & Maps SEO Playbook</h4>
                    <p style="color: #E2E8F0; font-size: 0.95rem;">{html.escape(web.local_seo_traffic_playbook)}</p>
                </div>
                """, unsafe_allow_html=True)
    
            else:
                st.markdown(f"""
                <div class="panel-card-accent">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <h3 style="color: #34D399; margin: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("check-circle-2", 20, "#34D399")} Dedicated Website Active</h3>
                        <span class="pill pill-green">Active Domain</span>
                    </div>
                    <p style="color: #E2E8F0; margin-top: 0.75rem;"><strong>Website URL:</strong> <a href="{web.existing_url}" target="_blank" style="color: #38BDF8;">{web.existing_url}</a></p>
                    <p style="color: #CBD5E1;">{html.escape(web.lead_leakage_analysis)}</p>
                </div>
                """, unsafe_allow_html=True)
    
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    st.markdown(f"""
                    <div class="panel-card">
                        <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("target", 18, "#38BDF8")} Lead Capture Optimization Hooks</h4>
                    """, unsafe_allow_html=True)
                    for lm in web.core_lead_magnets:
                        st.markdown(f"- {lm}")
                    st.markdown("</div>", unsafe_allow_html=True)
    
                with col_w2:
                    st.markdown(f"""
                    <div class="panel-card">
                        <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("map-pin", 18, "#34D399")} Local SEO Growth Playbook</h4>
                        <p style="color: #CBD5E1;">{html.escape(web.local_seo_traffic_playbook)}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
        # TAB 4: GROWTH & IMPROVEMENT ROADMAP
        with tab_imp:
            st.subheader("Strategic Brand Improvement Roadmap")
            st.caption("Actionable recommendations to plug traffic leaks, increase monetization, and scale reach.")
    
            st.markdown(f"""
            <div class="panel-card-accent">
                <h4 style="color: #34D399; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("zap", 18, "#34D399")} High-Impact Quick Wins (Next 30 Days)</h4>
            </div>
            """, unsafe_allow_html=True)
    
            for qw in imp.quick_wins_under_30_days:
                st.checkbox(f"**{qw}**", value=False, key=f"qw_{hash(qw)}")
    
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("target", 18, "#38BDF8")} Funnel & Conversion Enhancements</h4>
                """, unsafe_allow_html=True)
                for fc in imp.funnel_and_conversion_improvements:
                    st.markdown(f"- {fc}")
                st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("feather", 18, "#A78BFA")} Content & Messaging Upgrades</h4>
                """, unsafe_allow_html=True)
                for cm in imp.content_and_messaging_improvements:
                    st.markdown(f"- {cm}")
                st.markdown("</div>", unsafe_allow_html=True)
    
            with col_i2:
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("rocket", 18, "#38BDF8")} Cross-Platform Expansion</h4>
                """, unsafe_allow_html=True)
                for cpg in imp.cross_platform_growth_improvements:
                    st.markdown(f"- {cpg}")
                st.markdown("</div>", unsafe_allow_html=True)
    
                st.markdown(f"""
                <div class="panel-card">
                    <h4 style="color: #F8FAFC; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("alert-triangle", 18, "#FACC15")} Social Gaps & Vulnerabilities</h4>
                """, unsafe_allow_html=True)
                for v in soc.vulnerabilities:
                    st.markdown(f"- {v}")
                st.markdown("</div>", unsafe_allow_html=True)
    
        # TAB 5: COMPETITOR LANDSCAPE & MARKET HEALTH
        with tab_comp:
            st.subheader(f"Competitor Intelligence & Market Health: {loc.detected_location}")
            
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                sat_pill = "pill-green" if mkt.market_saturation == "Low" else "pill-yellow" if mkt.market_saturation == "Medium" else "pill-blue"
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">Market Saturation</div>
                    <div class="stat-card-value"><span class="pill {sat_pill}">{mkt.market_saturation}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c_m2:
                trend_pill = "pill-green" if "growing" in mkt.market_trend.lower() else "pill-yellow"
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">Industry Trajectory</div>
                    <div class="stat-card-value"><span class="pill {trend_pill}">{mkt.market_trend}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c_m3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-card-title">Competitors Identified</div>
                    <div class="stat-card-value">{len(report.competitors)} Entities</div>
                </div>
                """, unsafe_allow_html=True)
    
            st.markdown(f"""
            <div class="panel-card" style="margin-top: 1rem;">
                <strong>Locality Dynamics ({html.escape(loc.detected_location)}):</strong> {html.escape(mkt.locality_market_dynamics)}
            </div>
            """, unsafe_allow_html=True)
    
            st.markdown(f'<div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("swords", 20, "#F43F5E")} Identified Competitors (Local & Domain Rivals)</div>', unsafe_allow_html=True)
            if report.competitors:
                for comp in report.competitors:
                    type_pill = "pill-green" if "local" in comp.competitor_type.lower() else "pill-blue"
                    render_html(f"""
                    <div class="panel-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; border-bottom: 1px solid #334155; padding-bottom: 0.6rem; margin-bottom: 0.75rem;">
                            <h4 style="margin: 0; color: #F8FAFC;">{html.escape(comp.name)}</h4>
                            <div>
                                <span class="pill {type_pill}">{html.escape(comp.competitor_type)}</span>
                                <span class="pill pill-purple">Standing: {html.escape(comp.market_standing)}</span>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.9rem; margin-bottom: 0.75rem;">
                            <div><strong>Location:</strong> {html.escape(comp.location)}</div>
                            <div><strong>Pricing / Model:</strong> {html.escape(comp.estimated_pricing or 'Standard market rate')}</div>
                            <div><strong>Public Sentiment:</strong> {html.escape(comp.ratings_or_reviews or 'Active social presence')}</div>
                        </div>
                        <div style="background-color: #0F172A; padding: 0.75rem; border-radius: 6px; font-size: 0.9rem; margin-bottom: 0.75rem;">
                            <strong style="color: #38BDF8;">Differentiator vs Target:</strong> {html.escape(comp.differentiator_vs_target)}
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                            <span style="color: #34D399; display: flex; align-items: center; gap: 0.25rem;">{lucide("check-circle-2", 14, "#34D399")} Strengths:</span> {html.escape(', '.join(comp.strengths))} &nbsp;|&nbsp;
                            <span style="color: #F87171; display: flex; align-items: center; gap: 0.25rem;">{lucide("alert-triangle", 14, "#F87171")} Flaws/Gaps:</span> {html.escape(', '.join(comp.weaknesses))}
                        </div>
                    </div>
                    """)
            else:
                st.info("No direct competing entities registered for this query.")
    
            if mkt.untapped_market_opportunities:
                st.markdown(f'<div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("lightbulb", 18, "#FACC15")} Untapped Whitespace Opportunities</div>', unsafe_allow_html=True)
                for opp in mkt.untapped_market_opportunities:
                    st.success(f"✓ {opp}")
    
        # TAB 6: SOFTWARE PRODUCT OPPORTUNITY
        with tab_soft:
            st.subheader("Software Product Opportunity Assessment")
    
            if so.needs_software_product:
                st.markdown(f"""
                <div class="panel-card-accent">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <h3 style="color: #34D399; margin: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("check-circle-2", 20, "#34D399")} Software Product Highly Recommended</h3>
                        <span class="pill pill-green">Confidence: {so.confidence_in_verdict}</span>
                    </div>
                    <p style="color: #E2E8F0; margin-top: 0.75rem; font-size: 1.05rem;">{html.escape(so.verdict_summary)}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="panel-card" style="border-left: 4px solid #FACC15;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <h3 style="color: #FACC15; margin: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("alert-circle", 20, "#FACC15")} Custom Software Not Currently Recommended</h3>
                        <span class="pill pill-yellow">Confidence: {so.confidence_in_verdict}</span>
                    </div>
                    <p style="color: #E2E8F0; margin-top: 0.75rem; font-size: 1.05rem;">{html.escape(so.verdict_summary)}</p>
                </div>
                """, unsafe_allow_html=True)
    
            if so.recommended_product_ideas:
                st.markdown(f'<div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("rocket", 20, "#38BDF8")} Tailored Software Blueprints</div>', unsafe_allow_html=True)
                for idx, idea in enumerate(so.recommended_product_ideas, 1):
                    effort_pill = "pill-green" if idea.feasibility_effort == "Low" else "pill-yellow" if idea.feasibility_effort == "Medium" else "pill-blue"
                    render_html(f"""
                    <div class="panel-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; border-bottom: 1px solid #334155; padding-bottom: 0.6rem; margin-bottom: 0.75rem;">
                            <h4 style="margin: 0; color: #38BDF8;">{idx}. {html.escape(idea.product_name)}</h4>
                            <div>
                                <span class="pill pill-purple">{html.escape(idea.product_type)}</span>
                                <span class="pill {effort_pill}">Build Effort: {html.escape(idea.feasibility_effort)}</span>
                            </div>
                        </div>
                        <p style="font-size: 1.02rem; color: #F1F5F9;"><strong>Value Proposition:</strong> {html.escape(idea.core_value_proposition)}</p>
                        <p style="font-size: 0.95rem; color: #CBD5E1;"><strong>Problem Solved:</strong> {html.escape(idea.problem_it_solves)}</p>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; font-size: 0.9rem; margin-top: 0.75rem; margin-bottom: 0.75rem;">
                            <div><strong>Target Buyers:</strong> {html.escape(idea.target_buyers)}</div>
                            <div><strong>Suggested Pricing:</strong> <span class="pill pill-green">{html.escape(idea.suggested_monetization_model)}</span></div>
                        </div>
                        <div>
                            <strong>MVP Core Features:</strong>
                            <ul style="margin-top: 0.4rem; color: #94A3B8;">
                                {''.join([f"<li>{html.escape(f)}</li>" for f in idea.mvp_features])}
                            </ul>
                        </div>
                    </div>
                    """)
    
            if so.why_not_reasons:
                st.markdown(f'<div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("alert-triangle", 18, "#FACC15")} Strategic Considerations & Risks</div>', unsafe_allow_html=True)
                for r in so.why_not_reasons:
                    st.markdown(f"- {r}")
    
            if so.existing_software_gaps:
                st.markdown(f'<div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("search", 18, "#94A3B8")} Current Operational Friction</div>', unsafe_allow_html=True)
                for g in so.existing_software_gaps:
                    st.markdown(f"- {g}")
    
        # TAB 7: UNIFIED MASTER JSON EXPORT
        with tab_json:
            st.subheader("Unified Master Intelligence JSON")
            st.caption("Contains the entire aggregated intelligence payload across all 6 analytical pillars.")
    
            master_json = report.model_dump_json(indent=2)
            
            c_dl1, c_dl2 = st.columns([1, 1])
            with c_dl1:
                st.download_button(
                    label="Download Master JSON",
                    data=master_json,
                    file_name=f"{prof.username}_master_intelligence.json",
                    mime="application/json",
                    type="primary",
                    use_container_width=True
                )
            with c_dl2:
                md_doc = ReportGenerator.generate_markdown(report)
                st.download_button(
                    label="Download Markdown Report",
                    data=md_doc,
                    file_name=f"{prof.username}_master_intelligence.md",
                    mime="text/markdown",
                    use_container_width=True
                )
    
            with st.expander("View Full Master JSON Schema", expanded=True):
                st.json(master_json)
    


# ==============================================================================
# MODE 3: SAVED ANALYSES & INTELLIGENCE ARCHIVE
# ==============================================================================
elif app_mode == "Saved Reports":
    st.markdown(f"""
    <div class="module-banner">
        <div class="module-banner-header">
            {lucide("archive", 24, "#A78BFA")}
            <div>
                <h3 class="module-banner-title">Saved Reports & Intelligence Archive</h3>
                <div class="module-banner-subtitle">Historical archive of auto-saved brand analyses and audits</div>
            </div>
        </div>
        <div class="module-banner-desc">
            Every search and analysis is <strong>automatically saved</strong>. Browse previously analyzed Instagram accounts, 
            view historical snapshots, and instantly load past intelligence reports without re-scraping or re-running Ollama.
        </div>
    </div>
    """, unsafe_allow_html=True)

    saved_list = StorageManager.list_saved_profiles()

    if not saved_list:
        st.info("No saved profile analyses found yet. Run an analysis in 'Brand Audit' to get started!")
    else:
        st.subheader(f"Saved Creator & Business Profiles ({len(saved_list)})")
        
        for idx, item in enumerate(saved_list, 1):
            user = item["username"]
            with st.container():
                render_html(f"""
                <div class="panel-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">@{html.escape(user)}</h3>
                            <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.2rem; display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
                                {lucide("map-pin", 14, "#94A3B8")} Locality: <strong>{html.escape(item['locality'])}</strong> &nbsp;|&nbsp; {lucide("users", 14, "#94A3B8")} Followers: <strong>{html.escape(item['followers'])}</strong>
                            </div>
                        </div>
                        <div>
                            <span class="pill pill-purple">{html.escape(item['archetype'])}</span>
                            <span class="pill pill-green">{item['history_count']} Analysis Snapshot(s)</span>
                        </div>
                    </div>
                    <div style="font-size: 0.82rem; color: #64748B; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.35rem;">
                        {lucide("clock", 13, "#64748B")} Last Updated: {html.escape(item['timestamp_label'])}
                    </div>
                </div>
                """)

                col_load, col_hist = st.columns([2, 4])
                with col_load:
                    if st.button(f"Load @{user} Intelligence", key=f"load_btn_{user}_{idx}", type="primary", use_container_width=True):
                        loaded_rep = StorageManager.load_latest_report(user)
                        if loaded_rep:
                            st.session_state["current_profile"] = loaded_rep.profile
                            st.session_state["current_report"] = loaded_rep
                            st.session_state["location_override"] = loaded_rep.location.detected_location
                            st.success(f"Loaded analysis for @{user}! Switch to 'Brand Audit' tab in the sidebar to view full dashboard.")
                        else:
                            st.error(f"Could not load report for @{user}.")

                with col_hist:
                    histories = StorageManager.get_profile_history(user)
                    if len(histories) > 1:
                        with st.expander(f"View All {len(histories)} Historical Versions for @{user}"):
                            for h_idx, h in enumerate(histories):
                                h_col1, h_col2 = st.columns([3, 1])
                                with h_col1:
                                    st.caption(f"Snapshot #{len(histories)-h_idx}: {h['timestamp_label']} ({h['locality']})")
                                Port_btn = h_col2.button("Load This", key=f"btn_h_{user}_{h_idx}")
                                if Port_btn:
                                    p_rep = StorageManager.load_report_by_path(h.get("abs_json_path", ""))
                                    if p_rep:
                                        st.session_state["current_profile"] = p_rep.profile
                                        st.session_state["current_report"] = p_rep
                                        st.session_state["location_override"] = p_rep.location.detected_location
                                        st.success(f"Loaded snapshot from {h['timestamp_label']}!")


# ==============================================================================
# MODE 4: DEV PROBLEM RADAR & MICRO-SAAS
# ==============================================================================
elif app_mode == "Problem Radar":
    st.markdown(f"""
    <div class="module-banner">
        <div class="module-banner-header">
            {lucide("lightbulb", 24, "#FACC15")}
            <div>
                <h3 class="module-banner-title">Developer Problem Radar & Micro-SaaS</h3>
                <div class="module-banner-subtitle">Aggregated dev pain points across tech communities transformed into software blueprints</div>
            </div>
        </div>
        <div class="module-banner-desc">
            Scrapes software engineers' most discussed problems, systemic complaints, and architectural bottlenecks 
            across Hacker News, Reddit (r/ExperiencedDevs, r/programming), Dev.to, and Google News, 
            and synthesizes high-margin B2B DevTool & Micro-SaaS blueprints using Ollama.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_time, c_depth, c_btn = st.columns([3, 2, 2])
    with c_time:
        timeframe_sel = st.selectbox("Tracking Window", ["This Week vs Last Week", "Last 14 Days", "Monthly Macro Trends"])
    with c_depth:
        discussions_depth = st.slider("Discussions Per Source", min_value=3, max_value=20, value=8)
    with c_btn:
        st.write("")
        st.write("")
        run_radar = st.button("Scan Dev Discussions", type="primary", use_container_width=True)

    if run_radar:
        with st.spinner(f"Ingesting live discussions across Hacker News, Reddit, Dev.to & Google News and synthesizing with Ollama ({selected_model})..."):
            radar_engine = SoftwareProblemRadar(ollama_url=ollama_host, model_name=selected_model)
            try:
                radar_report = radar_engine.run_radar_analysis(max_items_per_source=discussions_depth)
                st.session_state["radar_report"] = radar_report
            except Exception as e:
                st.error(f"Problem Radar analysis failed: {e}")

    if "radar_report" in st.session_state:
        r_rep: SoftwareProblemRadarReport = st.session_state["radar_report"]

        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Discussions Analyzed", r_rep.total_discussions_analyzed)
        with r2:
            st.metric("Urgent Pain Points", len(r_rep.top_problems))
        with r3:
            st.metric("Data Feeds Ingested", len(r_rep.data_sources_ingested))

        st.markdown(f"""
        <div class="panel-card-accent" style="margin-top: 1rem; margin-bottom: 1.5rem;">
            <h4 style="color: #38BDF8; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("activity", 18, "#38BDF8")} Developer Sentiment & Macro Trend Summary ({html.escape(r_rep.timeframe)})</h4>
            <p style="color: #E2E8F0; font-size: 1rem; line-height: 1.6; margin: 0;">
                {html.escape(r_rep.macro_trend_summary)}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; margin: 1.25rem 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;">{lucide("flame", 22, "#F97316")} Top Trending Software Engineering Problems & Proposed Micro-SaaS</div>', unsafe_allow_html=True)

        for idx, prob in enumerate(r_rep.top_problems, 1):
            velo_pill = "pill-red" if "rising" in prob.frequency_velocity.lower() or "spike" in prob.frequency_velocity.lower() else "pill-yellow"
            with st.container():
                render_html(f"""
                <div class="panel-card" style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">{idx}. {html.escape(prob.problem_title)}</h3>
                            <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.2rem;">
                                Category: <strong>{html.escape(prob.category)}</strong> | Severity: <strong style="color: #F87171;">{prob.severity_score}/10</strong>
                            </div>
                        </div>
                        <div>
                            <span class="pill {velo_pill}">{html.escape(prob.frequency_velocity)}</span>
                        </div>
                    </div>
                    <div style="margin-top: 0.85rem; color: #CBD5E1; font-size: 0.95rem; line-height: 1.55;">
                        <strong>Developer Complaints & Discussion:</strong>
                        <p style="margin-top: 0.3rem; color: #94A3B8;">{html.escape(prob.summary_and_quotes)}</p>
                    </div>
                    <div style="margin-top: 0.6rem; color: #CBD5E1; font-size: 0.92rem;">
                        <strong>Architectural Root Cause:</strong>
                        <p style="margin-top: 0.3rem; color: #94A3B8;">{html.escape(prob.root_cause_analysis)}</p>
                    </div>
                    <div class="panel-card-accent" style="margin-top: 1rem; padding: 1rem; border-left: 4px solid #38BDF8;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.4rem;">
                            <h4 style="margin: 0; color: #38BDF8; font-size: 1.15rem; display: flex; align-items: center; gap: 0.5rem;">{lucide("rocket", 18, "#38BDF8")} Micro-SaaS Concept: {html.escape(prob.recommended_microsaas.product_name_concept)}</h4>
                            <span class="pill pill-green">{html.escape(prob.recommended_microsaas.monetization_model)}</span>
                        </div>
                        <p style="font-size: 0.98rem; color: #F1F5F9; margin-bottom: 0.4rem;">
                            <strong>Core Value Proposition:</strong> {html.escape(prob.recommended_microsaas.core_value_proposition)}
                        </p>
                        <p style="font-size: 0.9rem; color: #CBD5E1; margin-bottom: 0.4rem;">
                            <strong>Target ICP:</strong> {html.escape(prob.recommended_microsaas.target_icp)} | <strong>TAM / Urgency:</strong> {html.escape(prob.recommended_microsaas.estimated_tam_or_urgency)}
                        </p>
                        <div style="margin-top: 0.5rem;">
                            <strong style="font-size: 0.9rem;">MVP Core Features:</strong>
                            <ul style="margin-top: 0.3rem; color: #94A3B8; font-size: 0.88rem;">
                                {''.join([f"<li>{html.escape(f)}</li>" for f in prob.recommended_microsaas.mvp_features])}
                            </ul>
                        </div>
                    </div>
                </div>
                """)

        st.markdown("---")
        st.download_button(
            "Download Problem Radar JSON Report",
            data=r_rep.model_dump_json(indent=2),
            file_name=f"dev_problem_radar_{r_rep.timeframe.replace(' ', '_')}.json",
            mime="application/json"
        )

