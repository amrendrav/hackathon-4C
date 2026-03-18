"""
PromotionGapAgent
Finds categories with poor promotion ROI or no promotion coverage.
Identifies clip-to-redemption gaps and marketing whitespace.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_promotion_coverage, get_clip_to_redemption_rate
import json

def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences and preamble."""
    import json as _json, re as _re
    text = text.strip()
    # Direct parse
    try:
        return _json.loads(text)
    except Exception:
        pass
    # Extract from ```json ... ``` or ``` ... ``` fence
    m = _re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if m:
        return _json.loads(m.group(1).strip())
    # Find first { ... } block
    m = _re.search(r"\{[\s\S]+\}", text)
    if m:
        return _json.loads(m.group(0))
    raise ValueError(f"No JSON found in response: {text[:200]}")


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

    llm = ChatAnthropic(model=MODEL, max_tokens=2000)
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
        result = _parse_json(response.content)
    except Exception:
        result = {
            "promo_gap_score": 50,
            "underperforming_offers": [],
            "whitespace_categories": [],
            "marketing_actions": [],
            "summary": response.content[:300],
        }

    return {**state, "promotion_gap": result}
