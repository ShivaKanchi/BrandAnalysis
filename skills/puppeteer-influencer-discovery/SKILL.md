---
name: puppeteer-influencer-discovery
description: Find publicly visible gaming influencers that match country, niche, audience-fit, and follower-range criteria using Puppeteer. Use for repeatable creator discovery and CSV shortlists; do not use for private contact-data collection.
---

# Puppeteer Influencer Discovery

Use this skill to produce a review-ready creator shortlist from public web results. It is suited to youth gaming, mobile gaming, children’s games, Minecraft, Roblox, and indie games.

## Inputs

Collect the intended country, games/niches, follower range, platforms, and audience bands. Treat audience age as **inferred** unless the creator or a reliable analytics source publishes it. Never represent a search result as verified first-party audience analytics.

## Procedure

1. Run the Puppeteer discovery script with a focused query and follower range. The script uses public search-result pages only, stores result snippets and source URLs, and does not sign in or bypass access controls.
2. Reject brands, stores, fan pages, duplicate names, and accounts with no clear gaming/mobile-game evidence.
3. Confirm the final candidates on their public profile or official link page. Preserve the profile URL and observed follower count with a date.
4. Record a phone number only if it is explicitly published as a **business contact** on an official creator or management page. Never collect, infer, or expose private/personal phone numbers.
5. Save the shortlist as CSV and add only reviewed candidates to `data/influencer_india_seed_catalog.json` or the applicable regional catalogue.

## Commands

From the workspace root, install Puppeteer once when it is not already available:

```powershell
npm --prefix frontend install --save-dev puppeteer
```

Then run a discovery pass:

```powershell
node skills/puppeteer-influencer-discovery/scripts/discover_influencers.mjs `
  --query "India mobile gaming creator BGMI Free Fire" `
  --min-followers 1000 --max-followers 2000 `
  --limit 25 `
  --output reports/puppeteer_india_mobile_candidates.csv
```

The script outputs candidates for review; it does not claim the extracted results are verified influencer identities. Use the existing CLI for a catalogue-only shortlist after validation:

```powershell
python cli.py --influencers --country India --niches "mobile games" --min-followers 1000 --max-followers 2000
```

## Output requirements

CSV rows must include the query, creator name/handle when visible, public follower text, matched niche evidence, source URL, discovery timestamp, and `needs_review` status. Deduplicate by normalized handle first, then normalized creator name.
