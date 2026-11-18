# ⚡ BrandAnalysis AI: Autonomous Brand Intelligence, Lead Harvester & Micro-SaaS Radar

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Playwright](https://img.shields.io/badge/Playwright-Headless%20Scraper-2EAD33.svg)](https://playwright.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg)](https://ollama.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end AI intelligence system that combines **automated local business lead prospecting**, **in-depth Instagram brand reverse-engineering**, **competitor discovery via Google Maps & Search**, and **developer pain-point radar** to identify high-margin software product & Micro-SaaS opportunities.

Powered by **Playwright**, **Chrome DevTools MCP**, and local **Ollama** LLMs (`gemma4:31b-cloud`, `llama3.2`, `mistral`, etc.).

---

## 🌟 Core Modules

```
                        ┌─────────────────────────────────────────────────────────┐
                        │                   BrandAnalysis AI                      │
                        └───────────────────────────┬─────────────────────────────┘
                                                    │
         ┌──────────────────────────┬───────────────┴──────────────┬──────────────────────────┐
         ▼                          ▼                              ▼                          ▼
┌──────────────────┐      ┌──────────────────┐           ┌──────────────────┐       ┌──────────────────┐
│  Lead Harvester  │      │  Brand Analysis  │           │ Competitor Intel │       │  Problem Radar   │
│ (Google Maps/Web)│      │(Reverse-Engineered)│         │(Maps & Search)   │       │(HN, Reddit, News)│
└────────┬─────────┘      └────────┬─────────┘           └────────┬─────────┘       └────────┬─────────┘
         │                         │                              │                          │
         └─────────────────────────┼──────────────────────────────┴──────────────────────────┘
                                   ▼
                   ┌───────────────────────────────┐
                   │  Auto-Save & Offline Archive  │
                   │ (Unified JSON & Markdown MD)  │
                   └───────────────────────────────┘
```

### 1. 📍 Lead Harvester & Local Business Prospector _(Default Landing Page)_

- Autonomous Google Maps discovery: search any niche (e.g. _Specialty Coffee_, _Dentists_, _Gyms_) in any city or suburb.
- Crawls discovered business websites to extract and verify official Instagram handles.
- **1-Click Audit Handoff**: Click "Analyze @handle" to immediately route any harvested lead into the deep brand audit engine.

### 2. ⚡ Brand Analysis & Reverse-Engineering

- **Granular Likes & Interests**: Quotes exact bio phrases, post captions, and hashtags with analytical rationale and confidence scores (`🟢 High`, `🟡 Medium`, `⚪ Low`).
- **Brand Architecture**: Identifies Brand Archetype, Target Audience (demographics, pain points, core desire), Content Pillars, and Tone of Voice.
- **Website & Traffic Opportunity Audit**: Detects if the brand lacks an optimized web presence and outlines conversion and lead generation blueprints.
- **Software Product / Micro-SaaS Verdict**: Direct assessment on whether custom software is warranted. If YES: delivers target ICP, pricing model, MVP feature roadmap, and development effort.

### 3. 🔍 Competitor Intelligence & Local Market Matrix

- Scrapes Google Search and Google Maps to pinpoint both direct local competitors and global domain alternatives.
- Compares followers, strengths, weaknesses, and pricing structures in a comparative matrix.

### 4. 💡 Software Engineer Problem & Micro-SaaS Radar

- Scrapes trending developer discussions, complaints, and bottlenecks across **Hacker News (Algolia API)**, **Reddit (r/ExperiencedDevs, r/programming)**, **Dev.to**, and **Tech News**.
- Synthesizes recurring pain points into high-margin B2B DevTool & Micro-SaaS concepts with monetization strategies.

### 5. 📂 Automated History & Comeback Intelligence

- **Zero manual saving required**: Every profile analyzed in the UI or CLI is instantly persisted into timestamped JSON and Markdown reports under `reports/<username>/`.
- Central registry (`reports/intelligence_index.json`) enables instant 1-click reloading of past analyses without re-scraping or re-invoking Ollama.

### 6. 🎮 Youth Gaming Influencer Discovery

- A configurable catalogue of 100 Roblox, Minecraft, children/family gaming, Nintendo, and indie-game creators.
- Explainable relevance scoring based only on the selected niche and age-band labels; it never represents inferred labels as verified private demographics.
- Deduplicated review queue at `reports/influencer_registry.json` and spreadsheet export from `/api/influencers/export/csv`.

```powershell
python cli.py --influencers --audience-bands "10-13,13-17,16-22" --limit 100
```

Pass `--niches "Roblox,Minecraft,indie games"` to narrow a campaign; omit it to use all catalogue entries. Add `--country India` to use the separate Indian creator pool. Use `--fresh-only` to avoid candidates already returned in an earlier run. Maintain the source pools in `data/influencer_seed_catalog.json` and `data/influencer_india_seed_catalog.json`; each entry should remain `needs_review` until a human confirms current activity, audience analytics, brand safety, and contact route.

---

## 🚀 Quick Start (One-Click Startup Script)

Launch the entire application with one command. The startup script detects Python, activates your virtual environment, installs dependencies, verifies Ollama, and opens the Web Dashboard.

### On Linux, macOS, WSL, or Git Bash:

```bash
bash run.sh
# Or make it directly executable:
chmod +x run.sh
./run.sh
```

### On Windows (Command Prompt or PowerShell):

```cmd
run.bat
```

> **What the script does automatically:**
>
> 1. Detects Python 3 and activates `.venv` or `venv` if present.
> 2. Automatically installs any missing packages from `requirements.txt`.
> 3. Checks Playwright browser dependencies.
> 4. Tests Ollama connectivity at `http://localhost:11434`.
> 5. Launches the Streamlit Web Dashboard at `http://localhost:8501`.

---

## 🛠️ Manual Installation & Setup

If you prefer installing manually:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/BrandAnalysis.git
cd BrandAnalysis
```

### 2. Set Up Virtual Environment & Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

### 3. Configure Ollama

Make sure [Ollama](https://ollama.ai/) is installed and running locally:

```bash
# Start Ollama server
ollama serve

# Pull recommended model
ollama pull gemma4:31b-cloud
# (Or any installed model: llama3.2, mistral, etc.)
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` (all settings have sensible defaults; Instagram credentials are only needed if you encounter Instagram's login wall):

```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud

# Optional: Fill only if you encounter an Instagram login barrier
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
INSTAGRAM_SESSIONID=

# Scraper Settings
HEADLESS_BROWSER=True
MAX_POSTS_TO_ANALYZE=12
```

---

## 💻 Running the Application

### 1. Interactive Web Dashboard (Streamlit)

```bash
# Direct command:
python -m streamlit run app.py

# Or using runner:
./run.sh
```

- Open browser at `http://localhost:8501`.
- **Mode 1 (Default)**: `📍 Lead Harvester & Business Prospector` — Search businesses on Google Maps and harvest Instagram handles.
- **Mode 2**: `⚡ Brand Analysis & Profile Audit` — Deep personal branding, competitor analysis, and software opportunities.
- **Mode 3**: `📂 Saved Analyses & History` — Offline archive of all previously analyzed profiles with 1-click reload.
- **Mode 4**: `💡 Dev Problem Radar & Micro-SaaS` — Live scraping of developer pain points across Reddit/HN.

### 2. Command Line Interface (CLI)

You can run `cli.py` directly with Python or pass flags straight through `./run.sh` / `run.bat`:

```bash
# 1. Harvest business leads in a niche and location
python cli.py --prospect "Specialty Coffee" --location "Kandivali Mumbai" --limit 8

# 2. Analyze an Instagram brand
python cli.py --id hubermanlab

# 3. Analyze with custom post depth & explicit locality override
python cli.py --id levelsio --posts 15 --location "Lisbon, Portugal"

# 4. Run the Software Engineer Problem & Micro-SaaS Radar
python cli.py --radar --limit 8

# 5. View history of all past saved reports
python cli.py --history

# 6. Manual text mode (paste bio/captions without scraping Instagram)
python cli.py --manual

# 7. If Instagram prompts for credentials
python cli.py --id <username> --login
```

---

## 📁 Repository Structure

```
BrandAnalysis/
├── .env.example                # Sample environment configuration template
├── .gitignore                  # Production-ready gitignore (secrets, caches, venv)
├── README.md                   # Project documentation & usage guide
├── requirements.txt            # Python dependencies
├── run.sh                      # One-click startup script (Bash/Linux/Mac/WSL)
├── run.bat                     # One-click startup script (Windows CMD)
├── app.py                      # Interactive Streamlit Web Dashboard
├── cli.py                      # Rich Terminal Command Line Interface
├── config/
│   ├── __init__.py
│   └── settings.py             # Pydantic configuration settings
├── core/
│   ├── __init__.py
│   ├── analyzer.py             # Ollama AI brand deconstruction & product logic
│   ├── auto_prospector.py      # Google Maps business scraper & IG resolver
│   ├── competitors.py          # Google Search/Maps competitor intelligence
│   ├── models.py               # Strict Pydantic data schemas
│   ├── problem_radar.py        # Hacker News & Reddit developer pain-point engine
│   ├── report_generator.py     # Markdown and Rich CLI report renderer
│   ├── scraper.py              # Playwright Instagram scraper
│   ├── social_scraper.py       # Outbound social link & location extractor
│   └── storage.py              # Automated persistence & registry engine
├── reports/
│   ├── intelligence_index.json # Searchable index of all saved analyses
│   ├── alisolankii/            # Sample analyzed report (JSON & MD)
│   └── hubermanlab/            # Sample analyzed report (JSON & MD)
├── skills/
│   └── instagram-brand-analyzer/
│       └── SKILL.md            # Agent Skill specification for autonomous AI agents
└── tests/
    ├── test_pipeline.py        # Unit and integration tests
    └── test_radar_and_prospector.py
```

---

## 🔒 Security, Privacy & Git Checklist

This repository is pre-configured with a strict `.gitignore` to ensure safe public hosting:

- ✅ **`.env` and Credentials**: All `.env` files, API keys, passwords, and tokens are strictly excluded.
- ✅ **Session Cookies**: Browser session cookies and authentication caches (`cookies.json`) are ignored.
- ✅ **Python & OS Artifacts**: `__pycache__`, virtual environments (`.venv/`), and OS files (`.DS_Store`, `Thumbs.db`) are ignored.
- ✅ **Local Only**: Runs fully local on your own machine using Ollama — your scraped data is never sent to external 3rd-party LLM APIs unless explicitly configured.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
