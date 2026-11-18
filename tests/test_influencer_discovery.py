from pathlib import Path

from core.influencer_discovery import InfluencerDiscovery
from backend.workflows import get_workflow


def test_catalogue_returns_one_hundred_reviewable_creators(tmp_path: Path):
    discovery = InfluencerDiscovery(reports_dir=tmp_path)
    result = discovery.discover(
        audience_bands=["10-13", "13-17", "16-22"],
        limit=100,
    )

    assert result["count"] == 100
    assert all(item["review_status"] == "needs_review" for item in result["influencers"])
    assert all(item["audience_fit"] == "inferred" for item in result["influencers"])
    assert (tmp_path / "influencer_registry.json").exists()


def test_fresh_only_skips_previously_seen_candidates(tmp_path: Path):
    discovery = InfluencerDiscovery(reports_dir=tmp_path)
    discovery.discover(niches=["Roblox"], audience_bands=["10-13"], limit=100)
    fresh_run = discovery.discover(niches=["Roblox"], audience_bands=["10-13"], limit=100, fresh_only=True)

    assert fresh_run["count"] == 0
    assert fresh_run["skipped_previously_seen"] > 0


def test_influencer_discovery_workflow_has_a_review_gate():
    graph = get_workflow("influencer_discovery").get_graph()
    node_ids = {node["id"] for node in graph["nodes"]}

    assert {"audience_brief", "catalog_discovery", "fit_scoring", "review_queue"} <= node_ids


def test_india_pool_is_country_filtered_and_deduplicated(tmp_path: Path):
    result = InfluencerDiscovery(reports_dir=tmp_path).discover(
        country="India",
        audience_bands=["10-13", "13-17", "16-22"],
        limit=100,
    )

    names = [item["name"] for item in result["influencers"]]
    assert len(names) >= 50
    assert len(names) == len({name.casefold() for name in names})
    assert all(item["country"] == "India" for item in result["influencers"])
    techno = next(item for item in result["influencers"] if item["name"] == "Techno Gamerz")
    assert techno["instagram_handle"] == "ujjwalgamer"
    csv_path = InfluencerDiscovery(reports_dir=tmp_path).write_shortlist_csv(result["influencers"], "india_shortlist")
    assert csv_path.read_text(encoding="utf-8").count("\n") == len(names) + 1


def test_india_mobile_micro_creator_filter_uses_public_follower_counts(tmp_path: Path):
    result = InfluencerDiscovery(reports_dir=tmp_path).discover(
        country="India",
        niches=["mobile games"],
        audience_bands=["13-17", "16-22"],
        min_followers=1_000,
        max_followers=2_000,
    )

    assert {item["name"] for item in result["influencers"]} == {
        "DraKeN", "Mr Glitch Gaming", "KhwaishGaming", "SiddGaming"
    }
    assert all(1_000 <= item["follower_count"] <= 2_000 for item in result["influencers"])
