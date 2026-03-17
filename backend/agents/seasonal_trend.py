"""
SeasonalTrendAgent
Combines celebration purchase predictions with Google Trends signals.
Surfaces upcoming demand spikes and trending categories.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_celebration_demand_by_week
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Seasonal Demand analyst for Albertsons.
Analyse celebration prediction scores and search trend data. Identify:
1. Upcoming weeks with HIGH celebration probability — stock-up signals
2. Categories trending UP on Google Trends — emerging consumer demand
3. Seasonal patterns to prepare for in the next 2-4 weeks
4. Recommended assortment and inventory actions

Return ONLY valid JSON with EXACTLY these keys:
{
  "trend_score": <integer 0-100, higher = more urgency>,
  "upcoming_spikes": [
    {
      "week": "<fiscal_week_id>",
      "celebration_score": <float>,
      "category": "<recommended category to stock>",
      "signal": "<what's driving the spike>",
      "confidence": <float 0-1>
    }
  ],
  "trending_now": [
    {
      "keyword": "<search term>",
      "trend_index": <int 0-100>,
      "related_category": "<Albertsons category>"
    }
  ],
  "actions": ["<specific action for next 2 weeks>"],
  "summary": "<2-sentence insight for Monday briefing>"
}"""

# Static trend fallback (used when pytrends is rate-limited)
TREND_FALLBACK = {
    "organic produce": 72,
    "frozen meals": 58,
    "plant based protein": 81,
    "greek yogurt": 65,
    "kombucha": 88,
    "gluten free": 74,
    "meal prep": 69,
}


def _get_google_trends() -> dict:
    """Attempt pytrends fetch; fall back to static signals if rate-limited."""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=360)
        kw_list = list(TREND_FALLBACK.keys())[:5]
        pt.build_payload(kw_list, timeframe="now 3-m", geo="US-CA")
        interest = pt.interest_over_time()
        return {
            kw: int(interest[kw].mean()) if kw in interest.columns else TREND_FALLBACK[kw]
            for kw in kw_list
        }
    except Exception:
        return TREND_FALLBACK


def run_seasonal_trend_agent(state: dict) -> dict:
    celebration = get_celebration_demand_by_week()
    trend_data = _get_google_trends()

    llm = ChatAnthropic(model=MODEL, max_tokens=800)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Celebration purchase predictions by fiscal week (most recent first):\n"
                f"{json.dumps(celebration[:10], default=str)}\n\n"
                f"Google Trends interest (CA, last 3 months, 0-100 scale):\n"
                f"{json.dumps(trend_data, default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "trend_score": 50,
            "upcoming_spikes": [],
            "trending_now": [],
            "actions": [],
            "summary": response.content[:300],
        }

    return {**state, "seasonal_trend": result}
