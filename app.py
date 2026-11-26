"""MLBB INSIGHT read-only meta API.

Fetches public aggregate hero statistics from Moonton GMS sources and exposes
one normalized, cacheable JSON interface for the static MLBB INSIGHT website.
No player login, game ID, password, or personal account data is required.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

APP_ID = "2669606"
GMS_ROOT = os.getenv(
    "GMS_SOURCE_ROOT",
    f"https://api.gms.moontontech.com/api/gms/source/{APP_ID}",
).rstrip("/")
CACHE_TTL = max(60, int(os.getenv("CACHE_TTL_SECONDS", "1800")))
HTTP_TIMEOUT = max(4, min(20, int(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "12"))))

# These source IDs were observed in the public Moonton web client data flow.
# They are not a formally published developer API contract and may change.
WINDOW_SOURCE_IDS = {
    "1d": "2756567",
    "3d": "2756568",
    "7d": "2756569",
    "15d": "2756565",
    "30d": "2756570",
}
RANK_VALUES = {
    "all": ("1", "Semua rank"),
    "epic_plus": ("2", "Epic ke atas"),
}

app = FastAPI(
    title="MLBB INSIGHT API",
    version="1.0.0",
    description=(
        "Read-only API for aggregate MLBB ranked hero statistics. "
        "Data is fetched from public Moonton GMS endpoints; this is an "
        "unofficial fan project and not affiliated with Moonton."
    ),
)

origins = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = asyncio.Lock()


def _get_path(obj: Any, *keys: str) -> Any:
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_percent(value: Any) -> float | None:
    """Normalize ratio (0..1) or percent (0..100) to percentage points."""
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, str):
            value = value.strip().replace("%", "").replace(",", ".")
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not (0 <= number <= 100):
        return None
    if number <= 1:
        number *= 100
    return round(number, 2)


def _records(payload: dict[str, Any]) -> list[Any]:
    data = payload.get("data", payload)
    if isinstance(data, dict):
        records = data.get("records") or data.get("list") or []
        if isinstance(records, list):
            return records
    if isinstance(data, list):
        return data
    records = payload.get("records", [])
    return records if isinstance(records, list) else []


def normalize_stats(
    payload: dict[str, Any], window: str, rank: str
) -> list[dict[str, Any]]:
    """Convert GMS records into a predictable list for the web frontend."""
    wanted_rank = RANK_VALUES[rank][0]
    found: dict[str, dict[str, Any]] = {}

    for raw_record in _records(payload):
        record = _as_dict(raw_record)
        record_data = _as_dict(record.get("data", record))

        row_rank = record_data.get("bigrank")
        if row_rank is not None and str(row_rank) != wanted_rank:
            continue
        # camp_type 1 is Ranked; 0 is Classic. Ignore explicit Classic rows.
        camp_type = record_data.get("camp_type")
        if camp_type is not None and str(camp_type) != "1":
            continue

        hero_block = record_data.get("main_hero") or record_data.get("hero") or {}
        hero_data = _as_dict(hero_block)
        if isinstance(hero_data.get("data"), dict):
            hero_data = hero_data["data"]
        if not hero_data and any(k in record_data for k in ("heroid", "hero_id", "name")):
            hero_data = record_data
        if not hero_data:
            continue

        name = hero_data.get("name") or hero_data.get("hero_name") or hero_data.get("heroname")
        hero_id = hero_data.get("heroid") or hero_data.get("hero_id") or hero_data.get("id")
        if not name:
            continue

        win = _to_percent(hero_data.get("win_rate", hero_data.get("winrate")))
        pick = _to_percent(hero_data.get("pick_rate", hero_data.get("pickrate")))
        ban = _to_percent(hero_data.get("ban_rate", hero_data.get("banrate")))
        if win is None and pick is None and ban is None:
            continue

        key = str(hero_id if hero_id is not None else name).lower()
        found[key] = {
            "hero_id": hero_id,
            "name": str(name),
            "portrait": hero_data.get("head") or hero_data.get("portrait") or hero_data.get("icon"),
            "win_rate": win,
            "pick_rate": pick,
            "ban_rate": ban,
            "window": window,
            "rank": rank,
        }

    rows = list(found.values())
    rows.sort(key=lambda item: (item["win_rate"] is not None, item["win_rate"] or -1), reverse=True)
    return rows


async def fetch_gms(source_id: str) -> dict[str, Any]:
    url = f"{GMS_ROOT}/{source_id}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "X-AppId": APP_ID,
        "X-Lang": "en",
        "Origin": "https://www.mobilelegends.com",
        "Referer": "https://www.mobilelegends.com/",
        "User-Agent": "Mozilla/5.0 (compatible; MLBB-INSIGHT/1.0; +https://github.com)",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        response = await client.post(url, json={"pageSize": 200}, headers=headers)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Respons sumber Moonton bukan JSON yang valid.") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Format respons sumber Moonton berubah.")
    code = data.get("code")
    if code not in (None, 0, "0", 200, "200"):
        message = str(data.get("message") or data.get("msg") or "Sumber Moonton menolak permintaan.")
        raise HTTPException(status_code=502, detail=f"GMS upstream: {message[:180]}")
    return data


async def _get_cached_stats(window: str, rank: str) -> dict[str, Any]:
    key = f"stats:{window}:{rank}"
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL:
        result = dict(cached[1])
        result["cache"] = "hit"
        return result

    async with _cache_lock:
        now = time.monotonic()
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_TTL:
            result = dict(cached[1])
            result["cache"] = "hit"
            return result

        upstream = await fetch_gms(WINDOW_SOURCE_IDS[window])
        heroes = normalize_stats(upstream, window, rank)
        if not heroes:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Sumber Moonton berhasil dijangkau, tetapi format statistik tidak cocok. "
                    "Endpoint mungkin berubah; data kosong tidak akan ditampilkan sebagai statistik live."
                ),
            )

        result = {
            "ok": True,
            "source": "Moonton GMS public ranked data",
            "source_type": "aggregate_ranked_statistics",
            "window": window,
            "rank": rank,
            "rank_label": RANK_VALUES[rank][1],
            "mode": "ranked",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": len(heroes),
            "heroes": heroes,
            "cache_seconds": CACHE_TTL,
            "cache": "miss",
        }
        _cache[key] = (time.monotonic(), result)
        return result


@app.get("/")
async def root():
    return {
        "name": "MLBB INSIGHT API",
        "version": app.version,
        "status": "ok",
        "docs": "/docs",
        "endpoints": ["/api/health", "/api/meta/stats", "/api/heroes/catalog"],
        "note": "Unofficial fan project. No player login or credentials are collected.",
    }


@app.get("/api/health")
async def health(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "service": "mlbb-insight-api", "upstream": "Moonton GMS", "checked_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/meta/stats")
async def meta_stats(
    response: Response,
    window: str = Query("7d", pattern="^(1d|3d|7d|15d|30d)$"),
    rank: str = Query("all", pattern="^(all|epic_plus)$"),
):
    try:
        result = await _get_cached_stats(window, rank)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Permintaan ke sumber Moonton timeout. Coba beberapa saat lagi.") from exc
    except httpx.HTTPStatusError as exc:
        upstream_status = exc.response.status_code
        raise HTTPException(status_code=502, detail=f"Sumber Moonton merespons HTTP {upstream_status}.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Sumber Moonton sementara tidak dapat dijangkau.") from exc
    response.headers["Cache-Control"] = f"public, s-maxage={CACHE_TTL}, stale-while-revalidate=3600"
    return result


@app.get("/api/heroes/catalog")
async def hero_catalog(response: Response):
    try:
        payload = await fetch_gms("2756564")
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Permintaan katalog hero timeout.") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Moonton GMS merespons HTTP {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Katalog hero dari Moonton tidak dapat dijangkau.") from exc
    response.headers["Cache-Control"] = f"public, s-maxage={CACHE_TTL}, stale-while-revalidate=3600"
    return {"ok": True, "source": "Moonton GMS public hero catalog", "data": payload.get("data", payload), "fetched_at": datetime.now(timezone.utc).isoformat()}
