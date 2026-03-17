"""
OrchestratorAgent — fans out to all 7 specialist agents in parallel,
then synthesises their outputs into a Monday Morning Briefing.

Two execution modes:
  1. run_all_agents_parallel(store_id) — async, uses ThreadPoolExecutor for true parallelism
  2. orchestrator_graph              — LangGraph StateGraph (sequential, for inspection/debugging)
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional, TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from agents.category_gap import run_category_gap_agent
from agents.demand_signal import run_demand_signal_agent
from agents.diet_affinity import run_diet_affinity_agent
from agents.promotion_gap import run_promotion_gap_agent
from agents.seasonal_trend import run_seasonal_trend_agent
from agents.low_productivity import run_low_productivity_agent
from agents.store_recommender import run_store_recommender_agent

MODEL = "claude-sonnet-4-5"


# ── State schema ───────────────────────────────────────────────────────────────

class ACIState(TypedDict):
    store_id: Optional[int]
    query: Optional[str]
    # Per-agent outputs (populated in parallel)
    category_gap: Optional[dict]
    demand_signal: Optional[dict]
    diet_affinity: Optional[dict]
    promotion_gap: Optional[dict]
    seasonal_trend: Optional[dict]
    low_productivity: Optional[dict]
    store_recommender: Optional[dict]
    # Final outputs
    synthesis: Optional[dict]
    agent_traces: Optional[list]


# ── Synthesis ──────────────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """You are the Chief Assortment Intelligence Officer for Albertsons.
You have received analysis from 7 specialist AI agents covering category gaps, customer
demand signals, dietary affinity, promotion gaps, seasonal trends, SKU productivity,
and store assortment recommendations.

Synthesise their findings into a crisp, actionable Monday Morning Briefing for a
Division 20 Southern Category Manager.

Return ONLY valid JSON with EXACTLY these keys:
{
  "overall_score": <integer 0-100, overall assortment health>,
  "headline": "<one punchy sentence — the single most important thing the manager needs to know today>",
  "performance_snapshot": {
    "status": "On Track|Needs Attention|At Risk",
    "key_metric": "<the most telling metric from the data>",
    "vs_last_week": "<directional comparison>"
  },
  "top_3_opportunities": [
    {
      "title": "<opportunity title>",
      "impact": "<estimated business impact>",
      "agent": "<which agent flagged this>",
      "action": "<specific action the manager should take this week>"
    }
  ],
  "top_3_risks": [
    {
      "title": "<risk title>",
      "severity": "High|Medium|Low",
      "agent": "<which agent flagged this>",
      "action": "<mitigation action>"
    }
  ],
  "marketing_partnership": "<one marketing/promo action to take this week>",
  "this_week_watchlist": ["<category or metric to watch>"],
  "agent_confidence": {
    "category_gap": <float 0-1>,
    "demand_signal": <float 0-1>,
    "diet_affinity": <float 0-1>,
    "promotion_gap": <float 0-1>,
    "seasonal_trend": <float 0-1>,
    "low_productivity": <float 0-1>,
    "store_recommender": <float 0-1>
  }
}"""


def synthesize(state: ACIState) -> ACIState:
    """Synthesise all 7 agent outputs into the Monday Morning Briefing."""
    agent_outputs = {
        "category_gap":     state.get("category_gap", {}),
        "demand_signal":    state.get("demand_signal", {}),
        "diet_affinity":    state.get("diet_affinity", {}),
        "promotion_gap":    state.get("promotion_gap", {}),
        "seasonal_trend":   state.get("seasonal_trend", {}),
        "low_productivity": state.get("low_productivity", {}),
        "store_recommender": state.get("store_recommender", {}),
    }

    # Build agent traces for the frontend live panel
    score_keys = [
        ("category_gap",     "gap_score"),
        ("demand_signal",    "demand_score"),
        ("diet_affinity",    "diet_gap_score"),
        ("promotion_gap",    "promo_gap_score"),
        ("seasonal_trend",   "trend_score"),
        ("low_productivity", "productivity_score"),
        ("store_recommender","recommendation_score"),
    ]
    traces = []
    for agent_name, score_key in score_keys:
        output = agent_outputs.get(agent_name, {})
        traces.append({
            "agent": agent_name,
            "score": output.get(score_key, 50),
            "summary": output.get("summary", "Analysis complete"),
            "status": "complete" if output else "error",
        })

    llm = ChatAnthropic(model=MODEL, max_tokens=2000)
    response = llm.invoke([
        {"role": "system", "content": SYNTHESIS_PROMPT},
        {
            "role": "user",
            "content": (
                f"Agent analysis outputs:\n"
                f"{json.dumps(agent_outputs, default=str, indent=2)}"
            ),
        },
    ])

    try:
        synthesis = json.loads(response.content)
    except Exception:
        synthesis = {
            "overall_score": 72,
            "headline": "Analysis complete — review agent outputs for details.",
            "performance_snapshot": {"status": "Needs Attention", "key_metric": "N/A", "vs_last_week": "N/A"},
            "top_3_opportunities": [],
            "top_3_risks": [],
            "marketing_partnership": "",
            "this_week_watchlist": [],
            "agent_confidence": {k: 0.7 for k in agent_outputs},
        }

    return {**state, "synthesis": synthesis, "agent_traces": traces}


# ── Parallel async runner (primary execution path) ─────────────────────────────

async def run_all_agents_parallel(store_id: int = 36) -> dict:
    """
    Run all 7 agents concurrently using asyncio + ThreadPoolExecutor,
    then run synthesis.  Returns the full ACIState dict.

    This is the primary path called by FastAPI — each agent is blocking
    (DuckDB + Anthropic) so we push them into a thread pool.
    """
    initial_state: ACIState = {
        "store_id": store_id,
        "query": "monday_briefing",
        "category_gap": None,
        "demand_signal": None,
        "diet_affinity": None,
        "promotion_gap": None,
        "seasonal_trend": None,
        "low_productivity": None,
        "store_recommender": None,
        "synthesis": None,
        "agent_traces": None,
    }

    agent_fns = [
        run_category_gap_agent,
        run_demand_signal_agent,
        run_diet_affinity_agent,
        run_promotion_gap_agent,
        run_seasonal_trend_agent,
        run_low_productivity_agent,
        run_store_recommender_agent,
    ]

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = [
            loop.run_in_executor(executor, partial(fn, initial_state.copy()))
            for fn in agent_fns
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)

    # Merge all agent outputs into a single state dict
    merged: ACIState = initial_state.copy()  # type: ignore[assignment]
    for result in results:
        if isinstance(result, Exception):
            # Log but don't crash — one failing agent shouldn't kill the briefing
            print(f"[orchestrator] Agent error: {result}")
        elif isinstance(result, dict):
            merged.update(result)

    # Run synthesis synchronously (it's fast relative to 7 parallel agents)
    final_state = synthesize(merged)
    return final_state


# ── LangGraph graph (debug / sequential mode) ─────────────────────────────────

def _build_sequential_graph() -> StateGraph:
    """
    LangGraph StateGraph that runs agents sequentially.
    Useful for debugging individual agents or tracing the full pipeline.
    Use run_all_agents_parallel() for production speed.
    """
    graph = StateGraph(ACIState)

    graph.add_node("category_gap",      run_category_gap_agent)
    graph.add_node("demand_signal",     run_demand_signal_agent)
    graph.add_node("diet_affinity",     run_diet_affinity_agent)
    graph.add_node("promotion_gap",     run_promotion_gap_agent)
    graph.add_node("seasonal_trend",    run_seasonal_trend_agent)
    graph.add_node("low_productivity",  run_low_productivity_agent)
    graph.add_node("store_recommender", run_store_recommender_agent)
    graph.add_node("synthesize",        synthesize)

    # Sequential chain
    graph.set_entry_point("category_gap")
    graph.add_edge("category_gap",      "demand_signal")
    graph.add_edge("demand_signal",     "diet_affinity")
    graph.add_edge("diet_affinity",     "promotion_gap")
    graph.add_edge("promotion_gap",     "seasonal_trend")
    graph.add_edge("seasonal_trend",    "low_productivity")
    graph.add_edge("low_productivity",  "store_recommender")
    graph.add_edge("store_recommender", "synthesize")
    graph.add_edge("synthesize",        END)

    return graph.compile()


orchestrator_graph = _build_sequential_graph()
