"""
ACI — Assortment Intelligence Platform
FastAPI backend entry point.

Run from backend/:
    uvicorn main:app --reload --port 8000
"""

from dotenv import load_dotenv
load_dotenv()  # must happen before any agents import Anthropic client

import math
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def _sanitize(obj):
    """Recursively replace nan/inf with None so FastAPI can serialize."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj

from agents.orchestrator import run_all_agents_parallel
from db.queries import (
    get_monday_briefing_summary,
    get_category_gap_heatmap,
    get_network_vs_store_coverage,
    get_low_productivity_skus,
    get_assortment_gaps_by_store,
    get_celebration_demand_by_week,
    get_clip_to_redemption_rate,
    get_category_performance,
)

app = FastAPI(
    title="ACI — Assortment Intelligence Platform",
    description="Multi-agent retail assortment analytics for Albertsons Division 20",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_AGENTS = {
    "category_gap",
    "demand_signal",
    "diet_affinity",
    "promotion_gap",
    "seasonal_trend",
    "low_productivity",
    "store_recommender",
}


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    """Health check — confirms API + DB are reachable."""
    try:
        summary = get_monday_briefing_summary()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "service": "ACI", "version": "2.0.0", "db": db_status}


# ── Hero endpoint ──────────────────────────────────────────────────────────────

@app.get("/api/monday-briefing")
async def monday_briefing(store_id: int = 36):
    """
    Hero endpoint — runs all 7 agents in parallel, returns full Monday Briefing.
    Includes per-agent results and synthesised executive summary.
    Typical latency: 15-30s (7 parallel LLM calls + synthesis).
    """
    start = time.time()
    result = await run_all_agents_parallel(store_id=store_id)
    result["elapsed_seconds"] = round(time.time() - start, 2)
    return result


# ── DuckDB-only endpoints (no LLM, fast) ──────────────────────────────────────

@app.get("/api/briefing-summary")
def briefing_summary():
    """Raw DuckDB Monday briefing snapshot — no LLM, returns in <1s."""
    return get_monday_briefing_summary()


@app.get("/api/category-gap")
def category_gap(limit: int = 30):
    """Category gap heatmap data from Q4 OMNI."""
    return {
        "heatmap": get_category_gap_heatmap(),
        "performance": get_category_performance(limit=limit),
    }


@app.get("/api/store-coverage")
def store_coverage():
    """Network vs. store SKU coverage for all stores."""
    return {"data": get_network_vs_store_coverage()}


@app.get("/api/store-recommendations/{store_id}")
def store_recommendations(store_id: int):
    """Add/Remove SKU candidates for a specific store."""
    return get_assortment_gaps_by_store(store_id)


@app.get("/api/low-productivity-skus")
def low_productivity(bottom_pct: float = 0.25):
    """Bottom-quartile SKUs by category — rationalization candidates."""
    return JSONResponse(_sanitize({"data": get_low_productivity_skus(bottom_pct=bottom_pct)}))


@app.get("/api/celebration-demand")
def celebration_demand():
    """Celebration purchase predictions by fiscal week."""
    return {"data": get_celebration_demand_by_week()}


@app.get("/api/promo-performance")
def promo_performance():
    """Clip-to-redemption rates by banner and offer type."""
    return {"data": get_clip_to_redemption_rate()}


# ── Single agent endpoints (LLM, ~5-10s each) ─────────────────────────────────

@app.get("/api/agents/{agent_name}")
async def run_single_agent(
    agent_name: str,
    store_id: int = 36,
):
    """
    Run a single named agent and return its result.
    Valid agent names: category_gap | demand_signal | diet_affinity |
                       promotion_gap | seasonal_trend | low_productivity | store_recommender
    """
    if agent_name not in VALID_AGENTS:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Valid agents: {sorted(VALID_AGENTS)}",
        )

    from agents.category_gap import run_category_gap_agent
    from agents.demand_signal import run_demand_signal_agent
    from agents.diet_affinity import run_diet_affinity_agent
    from agents.promotion_gap import run_promotion_gap_agent
    from agents.seasonal_trend import run_seasonal_trend_agent
    from agents.low_productivity import run_low_productivity_agent
    from agents.store_recommender import run_store_recommender_agent
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    agent_map = {
        "category_gap":     run_category_gap_agent,
        "demand_signal":    run_demand_signal_agent,
        "diet_affinity":    run_diet_affinity_agent,
        "promotion_gap":    run_promotion_gap_agent,
        "seasonal_trend":   run_seasonal_trend_agent,
        "low_productivity": run_low_productivity_agent,
        "store_recommender": run_store_recommender_agent,
    }

    fn = agent_map[agent_name]
    initial_state = {"store_id": store_id, "query": agent_name}

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        result = await loop.run_in_executor(executor, lambda: fn(initial_state))

    return result
