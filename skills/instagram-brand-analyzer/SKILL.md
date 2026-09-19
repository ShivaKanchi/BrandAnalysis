---
name: instagram-brand-analyzer
description: Analyzes an Instagram profile to extract verified likes & interests with citations and confidence scores, deconstructs personal brand identity, uncovers local & domain competitors via Google Search/Maps, evaluates market health, and determines software product/Micro-SaaS opportunities using Chrome DevTools MCP, Playwright, or Ollama/LLM.
---

# Instagram Brand, Competitor & Software Opportunity Analyzer Skill

This skill guides AI agents on how to execute end-to-end brand deconstruction, location discovery, multi-platform social link auditing, local/domain competitor discovery, and software product opportunity evaluation for any Instagram creator or brand.

---

## Capabilities & Execution Pathways

### Pathway A: Automated Python Engine Execution
Run the full automated pipeline via terminal:
```bash
# Full analysis with automated location detection & competitor discovery
python cli.py --id <username>

# Specify or override brand locality (e.g. Austin, London, NYC)
python cli.py --id <username> --location "Austin, TX"

# Auto-prospect local businesses near a locality and harvest their Instagram handles
python cli.py --prospect "Specialty Coffee" --location "Austin, TX" --limit 8

# Scan software engineers' weekly complaints across HN, Reddit, and News & synthesize Micro-SaaS ideas
python cli.py --radar --limit 10

# If Instagram prompts for a login barrier:
python cli.py --id <username> --login

# Interactive manual text/caption paste mode:
python cli.py --manual
```

### Pathway B: Direct Agent Autonomous Browsing (Chrome DevTools MCP)
When browsing interactively with Chrome DevTools MCP:
1. **Navigate to Instagram Profile**:
   Call MCP tool `chrome-devtools-mcp:navigate_page` with `url: "https://www.instagram.com/<username>/"`.
2. **Extract Profile & Outbound Links**:
   Call `chrome-devtools-mcp:take_snapshot` to extract Bio, Metrics, Post Captions, and `external_url` (Linktree, Beacons, website).
3. **Resolve Locality**:
   - Check bio or captions for city/location tags (e.g. "📍 Austin, TX", "London").
   - **If no location is in the bio**: Execute a web search query:
     `"<creator full name> instagram location based in city"` or `"<username> headquarters"` to identify their home base.
4. **Scrape Outbound Social Profiles**:
   - Navigate to their `external_url` to collect their YouTube, Twitter/X, TikTok, LinkedIn, Podcast, and Newsletter links.
5. **Discover Competitors (Google Search & Google Maps)**:
   - **Local Competitors**: Query `top <niche> in <locality> businesses studios competitors` and Google Maps listings.
   - **Domain Rivals**: Query `top <niche> brands like @<username> competitors`.
6. **Synthesize Master Intelligence & Output Single JSON**:
   Assemble all findings into the unified master schema.

---

## Master Analytical Framework

Every report must fulfill these 6 pillars:

### 1. Granular Likes & Interests (With Citations & Confidence)
- Catalog all distinct hobbies, disciplines, topics, and domains.
- **Strict Evidence Citation**: Extract exact quotes from bio, post captions, reels, or external links.
- **Confidence Scoring**:
  - `🟢 High`: Explicitly in bio or recurring across 3+ posts.
  - `🟡 Medium`: Explicit in 1-2 posts or strong contextual evidence.
  - `⚪ Low`: Inferred from a single hashtag or casual mention.
  - Must include explicit `confidence_reasoning`.

### 2. Personal Brand Architecture & Social Status
- **Brand Archetype**: (e.g., *The Technical Solopreneur*, *The Scientific Educator*, *The High-Performance Coach*).
- **Target Audience Profile**: Demographics, mindset, and acute pain points.
- **Cross-Platform Presence**: Score as *Strong Multi-Platform*, *Moderate*, or *Single-Platform Dependent*.
- **Social Funnel Gaps**: Traffic leaks, missing lead magnets, or lack of owned audience channels.

### 3. Actionable Brand Improvement Roadmap
- **⚡ Quick Wins (<30 Days)**: Immediate optimizations for profile, bio copy, and CTA.
- **🎯 Funnel & Conversion Upgrades**: Lead capture funnels, newsletter integration.
- **✍️ Content & Messaging Enhancements**: Hook structures, recurring series.
- **🚀 Cross-Platform Repurposing**: Scaling to YouTube Shorts, LinkedIn, or Substack.

### 4. Competitor Landscape (Local & Domain)
- **Local Competitors**: Physical studios, local coaches, or agencies in their city/region.
- **Direct Domain Rivals**: Industry competitors targeting the same niche.
- **Attributes per Competitor**: Name, type, location, market standing, estimated pricing, strengths, weaknesses, customer sentiment/reviews, and competitive differentiator against target brand.

### 5. Market Dynamics & Trajectory
- **Market Saturation**: Low | Medium | High | Saturated.
- **Market Trend**: Rapidly Growing | Steady Growth | Mature / Flat | Declining.
- **Locality Dynamics**: City-level demand and saturation.
- **Untapped Market Opportunities**: Whitespace left open by competitors.

### 6. Software Product Opportunity Assessment
- **Definitive Verdict**: `needs_software_product: boolean`.
- **Executive Rationale**: Clear reasoning on why custom software makes sense or why off-the-shelf tools suffice.
- **Tailored Product Blueprints**:
  - Product Name & Type (Micro-SaaS, Lead-Gen Calculator, Workflow Automation, Client Portal).
  - Core Value Proposition & Problem Solved.
  - Target Buyers & Pricing Model.
  - MVP Feature List & Development Effort (Low, Medium, High).

---

## Output Formats
All outputs are automatically generated in:
1. `<username>_master_intelligence.json`: **Single unified master JSON file** containing all 6 pillars.
2. `<username>_master_intelligence.md`: Formatted Markdown report.
