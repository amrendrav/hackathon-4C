"""
DemandSignalAgent
Analyses customer segment demand vs. current assortment velocity.
Surfaces which segments are underserved and where basket attachment is highest.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_segment_distribution, get_transaction_velocity
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Demand Signal analyst for Albertsons.
Customer segments available include: ORGANIC LIVING, CONVENIENTLY FRESH,
CONVENIENCE SEEKERS, FAMILY FOCUSED, HEALTHIER ALTERNATIVES.

Analyse the segment and transaction velocity data to identify:
1. Which segments are GROWING — need more assortment support
2. Categories with HIGH basket attachment — strategic importance
3. eCommerce vs. in-store demand split and implications
4. Any segment-category mismatches — segment demand not met by current assortment

Return ONLY valid JSON with EXACTLY these keys:
{
  "demand_score": <integer 0-100>,
  "segment_insights": [
    {
      "segment": "<segment name>",
      "trend": "Growing|Stable|Declining",
      "category_affinity": "<top category for this segment>",
      "action": "<recommended assortment action>"
    }
  ],
  "basket_leaders": [
    {"category": "<name>", "avg_basket": <float>}
  ],
  "ecom_share_pct": <float>,
  "summary": "<2-sentence insight for Monday briefing>"
}"""


def run_demand_signal_agent(state: dict) -> dict:
    segments = get_segment_distribution()
    velocity = get_transaction_velocity()

    llm = ChatAnthropic(model=MODEL, max_tokens=1000)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer segments:\n{json.dumps(segments, default=str)}\n\n"
                f"Transaction velocity (top 10 by sales):\n"
                f"{json.dumps(velocity[:10], default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "demand_score": 50,
            "segment_insights": [],
            "basket_leaders": [],
            "ecom_share_pct": 0,
            "summary": response.content[:300],
        }

    return {**state, "demand_signal": result}
