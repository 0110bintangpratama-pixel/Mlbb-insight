from app import normalize_stats


def test_normalize_ranked_all_and_percent_ratios():
    payload = {
        "data": {"records": [
            {"data": {"bigrank": "1", "camp_type": "1", "main_hero": {"data": {
                "heroid": 101, "name": "Hero A", "head": "https://img/a.png",
                "win_rate": 0.56, "pick_rate": 12.5, "ban_rate": 0.03
            }}}},
            {"data": {"bigrank": "2", "camp_type": "1", "main_hero": {"data": {
                "heroid": 102, "name": "Hero B", "win_rate": 0.60, "pick_rate": 8, "ban_rate": 2
            }}}},
            {"data": {"bigrank": "1", "camp_type": "0", "main_hero": {"data": {
                "heroid": 103, "name": "Classic Hero", "win_rate": 0.9, "pick_rate": 50, "ban_rate": 0
            }}}},
        ]}
    }
    rows = normalize_stats(payload, "7d", "all")
    assert len(rows) == 1
    assert rows[0]["name"] == "Hero A"
    assert rows[0]["win_rate"] == 56.0
    assert rows[0]["pick_rate"] == 12.5
    assert rows[0]["ban_rate"] == 3.0


def test_normalize_epic_plus():
    payload = {"data": {"records": [
        {"data": {"bigrank": "1", "camp_type": "1", "main_hero": {"data": {"heroid": 1, "name": "All", "win_rate": 0.5}}}},
        {"data": {"bigrank": "2", "camp_type": "1", "main_hero": {"data": {"heroid": 2, "name": "Epic+", "win_rate": 0.51}}}},
    ]}}
    rows = normalize_stats(payload, "1d", "epic_plus")
    assert [row["name"] for row in rows] == ["Epic+"]


def test_health_and_stats_endpoint_contract(monkeypatch):
    from fastapi.testclient import TestClient
    import app as api_module

    async def fake_stats(window, rank):
        return {
            "ok": True,
            "source": "Moonton GMS public ranked data",
            "window": window,
            "rank": rank,
            "rank_label": "Semua rank" if rank == "all" else "Epic ke atas",
            "fetched_at": "2026-11-13T00:00:00+00:00",
            "count": 1,
            "heroes": [{"hero_id": 1, "name": "Test Hero", "win_rate": 55, "pick_rate": 11, "ban_rate": 2}],
        }

    monkeypatch.setattr(api_module, "_get_cached_stats", fake_stats)
    client = TestClient(api_module.app)
    health = client.get("/api/health")
    assert health.status_code == 200 and health.json()["ok"] is True
    stats = client.get("/api/meta/stats?window=7d&rank=all")
    assert stats.status_code == 200
    assert stats.json()["heroes"][0]["win_rate"] == 55
    assert "s-maxage" in stats.headers.get("cache-control", "")
