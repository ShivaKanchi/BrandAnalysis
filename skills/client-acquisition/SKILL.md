---
name: client-acquisition
description: Systematic methodology to discover, qualify, and acquire high-intent paying clients and B2B leads. Bypasses vanity follower counts, eliminates repetitive directory leads through micro-locality grids, filters for commercial buying signals, and generates high-converting value-first bottleneck teardowns.
---

# 🎯 Client Acquisition: High-Intent Lead Generation & Value-First Outreach

A battle-tested operational playbook for identifying real, paying business clients, filtering out vanity metrics (fake followers/dead profiles), harvesting unsaturated lead pools, and converting prospects using value-first diagnostic audits.

---

## 1. The Core Philosophy: The Buyer Intent Matrix

Most outreach fails because agents and agencies target **vanity metrics** rather than **commercial buying intent**.

```
                           ┌────────────────────────────────────────┐
                           │          THE QUALIFICATION GATE        │
                           └───────────────────┬────────────────────┘
                                               │
                    ┌──────────────────────────┴──────────────────────────┐
                    ▼                                                     ▼
     ❌ WEAK METRIC (Do Not Target)                       ✅ BUYING SIGNAL (Target)
     ───────────────────────────────                      ─────────────────────────
     • Follower count (easily bought)                     • Active Meta Ad Library spend (has budget)
     • Number of likes / views (bot-farmed)               • Review velocity (>15 reviews, recent 30 days)
     • General directories / top 5 results                • Commercial footprint (in-person customer flow)
     • Unverified social influencers                      • Digital funnel leaks (broken booking, no domain)
```

### The 4 Pillars of Buyer Intent:
1. **Real Human Velocity:** Look at Google Business Profile reviews. A local brand with 120 reviews and 4.7★ has real foot traffic, real customers, and cash flow—even if they only have 400 Instagram followers.
2. **Paid Acquisition Activity:** Check the **Meta Ad Library** (`facebook.com/ads/library`). If a company is actively running paid ads, they have an active customer acquisition budget and an executive who understands marketing ROI.
3. **Funnel Gaps & Digital Leaks:** The best clients are businesses with **high offline demand but poor digital infrastructure** (e.g., using a Linktree instead of an automated booking engine, unoptimized mobile speed, or missing conversion tracking).
4. **Hiring Velocity:** Businesses actively seeking front-desk managers, sales reps, or technicians have expanding payroll and urgent need for automation.

---

## 2. Escaping the "Top-of-Maps" Bubble

Querying generic terms like `"Dentist in New York"` or `"Gyms in Chicago"` traps scrapers in the same 10–20 sponsored or top-SEO results that get 50+ cold emails a day.

### Systematic Saturation Breakout:

#### A. Micro-Locality & Directional Grids
Divide cities into micro-neighborhoods, postal codes, and directional sectors:
* **Generic:** `"Gyms in Austin, TX"`
* **Micro-Grid:**
  * `"Gyms in South Congress Austin"`
  * `"Gyms in Mueller Austin"`
  * `"Gyms in 78704"`
  * `"Boutique fitness North Austin"`

#### B. High-Ticket Sub-Niches
Replace root category queries with specific, high-margin specializations:
* Instead of **Dentist** $\rightarrow$ `Invisalign provider`, `Pediatric dental surgeon`, `Cosmetic veneer clinic`
* Instead of **Gym** $\rightarrow$ `Pilates reformer studio`, `CrossFit box`, `Private personal training studio`
* Instead of **Coffee** $\rightarrow$ `Specialty coffee roastery`, `Artisan bakery cafe`
* Instead of **Lawyer** $\rightarrow$ `Commercial real estate attorney`, `Estate planning practice`

#### C. Continuous Lead Deduplication
Always check prospects against a persistent registry ([`reports/leads_registry.json`](file:///c:/Shiva/Projects/Automation/BrandAnalysis/reports/leads_registry.json)) to skip previously gathered businesses and automatically scroll deeper into directory results.

---

## 3. Running Lead Harvesting via BrandAnalysis AI

### Terminal & CLI Execution:
```bash
# Harvest fresh, verified leads for a niche & location (auto-deduplicating past runs)
python cli.py --prospect "Specialty Coffee" --location "Kandivali, Mumbai" --limit 8

# Deep audit on a discovered prospect's handle
python cli.py --id <instagram_handle> --location "Kandivali, Mumbai"
```

### Python Programmatic Harvesting:
```python
from core.auto_prospector import AutoProspector
from core.storage import StorageManager

# 1. Initialize prospector (runs Playwright with infinite feed scrolling)
prospector = AutoProspector(headless=True)

# 2. Discover fresh leads with auto-expansion and deduplication
report = prospector.discover_leads(
    niche_or_query="Pilates Studio",
    location="Bandra, Mumbai",
    limit=8,
    exclude_previously_seen=True, # Skips leads in database
    auto_expand=True              # Automatically queries East/West/sub-areas if saturated
)

# 3. Inspect high-intent prospects
for lead in report.leads:
    if lead.lead_intent_score == "High Intent":
        print(f"🔥 {lead.business_name} | {lead.rating}★ ({lead.review_count} reviews)")
        print(f"   Pitch Angle: {lead.opportunity_angle}")
        print(f"   Signals: {', '.join(lead.authenticity_signals)}")
```

---

## 4. The "Value-First" Teardown Pitch (Cold Conversion)

**Never pitch your services directly in message #1.** Pitching a 30-minute call yields $<1\%$ response rates. Instead, provide a **60-second diagnostic audit** pointing out one specific, high-cost bottleneck.

### The 3-Step Cold Conversion Framework:

```
[Observation of Real Traffic] ──► [Identification of Funnel Leak] ──► [Low-Friction Resource Drop]
```

### High-Converting Outreach Templates:

#### Template A: For Businesses with High Reviews but a Linktree / Biolink
> **Subject:** Quick question about bookings for {{Business Name}}
>
> *"Hey {{First Name}},*
>
> *I came across {{Business Name}} while looking at top-rated studios in {{Location}}—huge respect for the {{Review Count}} verified reviews and reputation you've built.*
>
> *I noticed your Instagram bio routes customers to a Linktree with 6 options, but on mobile, users have to scroll past 3 dead links to reach your class schedule. You're likely losing 15–20% of potential bookings right at that step.*
>
> *I recorded a quick 60-second clip showing how to embed a 1-click booking flow directly so mobile visitors don't drop off. No sales pitch at all—mind if I send the video link over?"*

#### Template B: For Businesses with Zero Website (Google Maps Only)
> **Subject:** Question about {{Business Name}} website listing
>
> *"Hey {{First Name}},*
>
> *Noticed {{Business Name}} has {{Review Count}} Google reviews with a {{Rating}}★ rating in {{Location}}, but your Google profile doesn't have an official website or menu link connected.*
>
> *Right now, when people search for '{{Category}} in {{Location}}' on their phones, they see competitors with 1-click booking links right below you, siphoning off search traffic.*
>
> *Put together a simple 2-slide blueprint on how to launch a fast, mobile-first intake page in an afternoon to capture those lost calls. Would it be alright if I forwarded it over?"*

---

## 5. Inbound Client Attraction (Authority Engine)

To stop chasing cold leads entirely, turn your lead audits into public authority:

1. **The 3-Minute Teardown Video:**
   - Record a screen-share analyzing a popular local brand in your niche.
   - Breakdown: *Why [Brand X] has 25,000 followers but leaks 30% of their web orders (and the 2 fixes).*
   - Post to LinkedIn, YouTube, or Twitter/X tagging relevant industry keywords.
2. **The "Free Bottleneck Audit" Lead Magnet:**
   - Offer local business owners a free "5-Point Conversion & Review Audit".
   - Collect their Google Maps URL, Website, and Instagram handle to pre-qualify them before talking.

---

## 6. Pitch Generator Utility Script

Run the built-in script to instantly generate tailored outreach copy and teardown scripts for any prospect:
```bash
python .agents/skills/client-acquisition/scripts/generate_pitch.py --name "Aurum Fitness" --niche "Gyms" --locality "Indiranagar, Bangalore" --reviews 142 --rating 4.8 --website "https://linktr.ee/aurum" --handle "aurum.bangalore"
```
