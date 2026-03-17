"""
PromotionGapAgent
Finds categories with poor promotion ROI or no promotion coverage.
Identifies clip-to-redemption gaps and marketing whitespace.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_promotion_coverage, get_clip_to_redemption_rate
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Promotion Effectiveness analyst for Albertsons.
Analyse clip and redemption data to find where promotions are failing or missing.

Identify:
1. Offer types with LOW redemption rates (<20%) despite high clip counts — promotion mismatch
2. Categories with NO digital offer coverage — marketing whitespace
3. Customer segments not being targeted by current promotions
4. Recommended marketing partnership actions for category managers

Return ONLY valid JSON with EXACTLY these keys:
{
  "promo_gap_score": <integer 0-100, higher = more gap>,
  "underperforming_offers": [
    {
      "offer_type": "<type>",
      "total_clips": <int>,
      "redemption_rate_pct": <float>,
      "issue": "<root cause or hypothesis>",
      "fix": "<recommended action>"
    }
  ],
  "whitespace_categories": ["<category>"],
  "marketing_actions": ["<action item>"],
  "summary": "<2-sentence insight for Monday briefing>"
}"""


def run_promotion_gap_agent(state: dict) -> dict:
    coverage = get_promotion_coverage()
    clip_rate = get_clip_to_redemption_rate()

    llm = ChatAnthropic(model=MODEL, max_tokens=800)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Offer coverage by type and category (top 10):\n"
                f"{json.dumps(coverage[:10], default=str)}\n\n"
                f"Clip-to-redemption rates by banner and offer type:\n"
                f"{json.dumps(clip_rate, default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "promo_gap_score": 50,
            "underperforming_offers": [],
            "whitespace_categories": [],
            "marketing_actions": [],
            "summary": response.content[:300],
        }

    return {**state, "promotion_gap": result}
