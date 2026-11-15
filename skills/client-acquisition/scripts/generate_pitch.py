#!/usr/bin/env python3
"""
generate_pitch.py
Companion utility for the 'client-acquisition' skill.
Generates value-first diagnostic teardowns, 60-second video audit scripts,
and cold outreach sequences based on verified commercial buying signals.
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from core.storage import StorageManager
except ImportError:
    StorageManager = None


def generate_pitch(
    name: str,
    niche: str,
    locality: str,
    reviews: int,
    rating: float,
    website: str,
    handle: str
) -> dict:
    # 1. Determine bottleneck angle
    has_domain = False
    is_link_aggregator = False
    if website:
        clean_url = website.lower()
        if any(h in clean_url for h in ["linktr.ee", "bio.link", "wa.me", "beacons.ai", "instagram.com"]):
            is_link_aggregator = True
            bottleneck_type = "LINK_AGGREGATOR"
            leak_summary = "Using a basic link aggregator (Linktree/WhatsApp) that requires 3-4 clicks on mobile, causing high reservation drop-off."
            pitch_hook = "embed a direct 1-click mobile booking flow to stop leaking reservations from mobile visitors"
        else:
            has_domain = True
            domain = re.sub(r"^https?://(www\.)?", "", website).split("/")[0]
            bottleneck_type = "CUSTOM_DOMAIN_OPTIMIZATION"
            leak_summary = f"Dedicated domain ({domain}) exists, but likely missing automated retention, retargeting pixels, and conversion speed optimization."
            pitch_hook = "optimize mobile checkout speed and activate automated customer re-engagement"
    else:
        bottleneck_type = "NO_WEBSITE"
        leak_summary = "Zero dedicated web presence outside of Google Maps, leaking high-intent search traffic to local competitors."
        pitch_hook = "launch a fast, high-converting 1-page mobile booking portal to capture local search traffic"

    # 2. Formulate 60-Second Video Audit Script
    video_outline = [
        f"0:00 - 0:15 [PROOF]: Show their Google listing ({reviews} reviews, {rating}★). Validate their real customer volume and local reputation.",
        f"0:15 - 0:35 [THE BOTTLENECK]: Screen record opening their link ({website or 'Google Maps link'}) on a mobile simulator. Point out the exact friction: '{leak_summary}'",
        f"0:35 - 0:50 [THE FIX]: Display a clean 2-step wireframe demonstrating how a customer can book or contact in under 5 seconds.",
        "0:50 - 1:00 [LOW-PRESSURE CLOSE]: 'Happy to send the 3-step checklist or wireframe over if you'd like to implement it with your team.'"
    ]

    # 3. Formulate Outreach Message
    email_subject = f"Quick question about bookings for {name}"
    email_body = f"""Hey {name.split()[0] if name else 'there'},

I came across {name} while looking at top-rated {niche.lower() if niche else 'businesses'} in {locality}—huge respect for the {reviews} verified reviews and {rating}★ rating you've built. Real customer volume like that is rare.

I noticed your current setup ({website or 'profile listing'}) makes mobile visitors take multiple steps to book or reach you. {leak_summary}

I recorded a short 60-second video walk-through showing exactly where mobile visitors drop off and how to {pitch_hook}.

No sales pitch at all—would you like me to send the video link over?

Best,
[Your Name]"""

    # 4. Formulate Follow-Up (Day 4)
    followup_body = f"""Hey {name.split()[0] if name else 'there'},

Quick follow-up on the note from earlier this week. In case you didn't have time to review, here's a 1-sentence screenshot of the mobile bottleneck for {name}:

[Attach 1 screenshot with an arrow pointing to the drop-off step]

Happy to send the short clip over if useful, or no worries if you already have this handled!"""

    return {
        "business_name": name,
        "niche": niche,
        "locality": locality,
        "reviews": reviews,
        "rating": rating,
        "bottleneck_type": bottleneck_type,
        "leak_summary": leak_summary,
        "video_audit_outline": video_outline,
        "cold_email_subject": email_subject,
        "cold_email_body": email_body,
        "followup_message": followup_body
    }


def main():
    parser = argparse.ArgumentParser(description="Generate diagnostic client acquisition pitches based on buying signals.")
    parser.add_argument("--name", type=str, default="Apex Studio", help="Business name")
    parser.add_argument("--niche", type=str, default="Fitness Studio", help="Category or niche")
    parser.add_argument("--locality", type=str, default="Indiranagar, Bangalore", help="Location")
    parser.add_argument("--reviews", type=int, default=112, help="Google review count")
    parser.add_argument("--rating", type=float, default=4.7, help="Google rating")
    parser.add_argument("--website", type=str, default="https://linktr.ee/apexstudio", help="Website or link")
    parser.add_argument("--handle", type=str, default="apexstudio", help="Instagram handle")
    parser.add_argument("--latest", action="store_true", help="Load the latest lead from reports/leads_registry.json")

    args = parser.parse_args()

    name = args.name
    niche = args.niche
    loc = args.locality
    reviews = args.reviews
    rating = args.rating
    website = args.website
    handle = args.handle

    if args.latest and StorageManager:
        registry = StorageManager.load_leads_registry()
        leads = registry.get("leads", {})
        if leads:
            latest_sig = list(leads.keys())[-1]
            lead_data = leads[latest_sig]
            name = lead_data.get("business_name", name)
            niche = lead_data.get("category", niche)
            loc = lead_data.get("address_or_location", loc)
            website = lead_data.get("website", website)
            handle = lead_data.get("instagram_handle", handle)
            raw_rev = re.sub(r"[^\d]", "", lead_data.get("review_count") or "")
            reviews = int(raw_rev) if raw_rev else reviews
            try:
                rating = float(lead_data.get("rating") or rating)
            except ValueError:
                pass

    pitch = generate_pitch(name, niche, loc, reviews, rating, website, handle)

    print("=" * 70)
    print(f"🎯 CLIENT ACQUISITION TEARDOWN: {pitch['business_name'].upper()}")
    print("=" * 70)
    print(f"📍 Location: {pitch['locality']} | Proof: {pitch['reviews']} reviews ({pitch['rating']}★)")
    print(f"🚨 Core Bottleneck: {pitch['leak_summary']}")
    print("\n" + "-" * 70)
    print("📹 60-SECOND VALUE-FIRST VIDEO AUDIT OUTLINE:")
    print("-" * 70)
    for step in pitch["video_audit_outline"]:
        print(f"  • {step}")

    print("\n" + "-" * 70)
    print(f"✉️ COLD OUTREACH MESSAGE (Subject: {pitch['cold_email_subject']}):")
    print("-" * 70)
    print(pitch["cold_email_body"])

    print("\n" + "-" * 70)
    print("🔁 DAY 4 FOLLOW-UP:")
    print("-" * 70)
    print(pitch["followup_message"])
    print("=" * 70)


if __name__ == "__main__":
    main()
