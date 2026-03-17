"""
DietAffinityAgent
Finds unmet dietary demand: customers hold diet flags but catalog has gaps.
Crosses customer demand signals with SKU catalog coverage.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_diet_flags_summary, get_diet_vs_catalog_gap
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Dietary Affinity analyst for Albertsons.
You cross-reference what customers WANT (diet preference flags) with what the
catalog OFFERS (SKU count and brand coverage by category).

Analyse the diet preference data and catalog coverage. Identify:
1. Diet flags with HIGH customer count but LOW SKU coverage — biggest opportunity
2. Categories missing key dietary certifications or options
3. Own-brand (private label) gaps for diet-specific product lines

Return ONLY valid JSON with EXACTLY these keys:
{
  "diet_gap_score": <integer 0-100, higher = more opportunity>,
  "gaps": [
    {
      "diet": "vegetarian|vegan|keto|gluten_free|dairy_free",
      "customer_demand": "<N customers or percentage>",
      "catalog_gap": "<description of the gap>",
      "opportunity": "<specific SKU or category action>"
    }
  ],
  "top_opportunity": "<single most impactful diet gap in one sentence>",
  "summary": "<2-sentence insight for Monday briefing>"
}"""


def run_diet_affinity_agent(state: dict) -> dict:
    diet_summary = get_diet_flags_summary()
    catalog_veg = get_diet_vs_catalog_gap("vegetarian")
    catalog_vegan = get_diet_vs_catalog_gap("vegan")
    catalog_keto = get_diet_vs_catalog_gap("keto")

    # Combine catalog data — each call returns same product data with different label
    catalog_combined = {
        "vegetarian_catalog": catalog_veg[:8],
        "vegan_catalog": catalog_vegan[:8],
        "keto_catalog": catalog_keto[:8],
    }

    llm = ChatAnthropic(model=MODEL, max_tokens=800)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Diet preference flags (customer demand side):\n"
                f"{json.dumps(diet_summary, default=str)}\n\n"
                f"Catalog SKU coverage by category (supply side):\n"
                f"{json.dumps(catalog_combined, default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "diet_gap_score": 50,
            "gaps": [],
            "top_opportunity": "",
            "summary": response.content[:300],
        }

    return {**state, "diet_affinity": result}
