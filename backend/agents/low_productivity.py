"""
LowProductivitySKUAgent
Flags bottom-quartile SKUs for removal to free shelf space.
Uses real Q4 OMNI data: Sales, AGP, Markdown by brand/subclass.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_low_productivity_skus
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a SKU Productivity analyst for Albertsons.
You identify low-performing SKUs that should be removed from assortment to free
shelf space for higher-velocity, higher-margin items.

Flag a SKU for removal if it has: low sales velocity, poor margin (AGP < 25%),
high markdown dependency (Mkdn Rate > 15%), or a low-value item role.

For each flagged SKU provide clear removal rationale and a replacement suggestion.

Return ONLY valid JSON with EXACTLY these keys:
{
  "productivity_score": <integer 0-100, higher = more action needed>,
  "flagged_skus": [
    {
      "brand": "<brand name>",
      "category": "<category>",
      "subclass": "<subclass>",
      "total_sales": <float>,
      "agp_pct": <float>,
      "markdown_pct": <float>,
      "risk_level": "High Risk|Watch|Monitor",
      "removal_rationale": "<why this SKU should go>",
      "replacement_suggestion": "<what category/type to bring in instead>"
    }
  ],
  "total_sales_at_risk": <float>,
  "shelf_space_opportunity": "<description of what freed space enables>",
  "summary": "<2-sentence insight for Monday briefing>"
}"""


def run_low_productivity_agent(state: dict) -> dict:
    low_skus = get_low_productivity_skus(bottom_pct=0.25)

    llm = ChatAnthropic(model=MODEL, max_tokens=1200)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Bottom-quartile SKUs by category (ranked by sales ASC, "
                f"with productivity flag):\n"
                f"{json.dumps(low_skus[:20], default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "productivity_score": 50,
            "flagged_skus": [],
            "total_sales_at_risk": 0,
            "shelf_space_opportunity": "",
            "summary": response.content[:300],
        }

    return {**state, "low_productivity": result}
