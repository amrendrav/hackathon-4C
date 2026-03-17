"""
StoreAssortmentRecommenderAgent — the star agent.
Recommends specific SKU adds and removes per store.
Tells a Category Manager exactly which 5 SKUs to ADD and 3 to REMOVE.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_assortment_gaps_by_store, get_network_vs_store_coverage
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Store Assortment Recommender for Albertsons.
Your job is to give a Category Manager specific, actionable SKU decisions for a store.

For ADD recommendations: explain WHY this SKU belongs (demand signal, segment fit, gap filling).
For REMOVE recommendations: explain WHY this SKU should go (low velocity, margin drain, better alternatives available).

Return ONLY valid JSON with EXACTLY these keys:
{
  "store_id": <int>,
  "recommendation_score": <integer 0-100, confidence level>,
  "add_recommendations": [
    {
      "upc_dsc": "<product description>",
      "brand": "<brand>",
      "category": "<category>",
      "rationale": "<why add this — specific demand signal>",
      "expected_weekly_sales": <float>,
      "segment_fit": "<which customer segment this serves>"
    }
  ],
  "remove_recommendations": [
    {
      "upc_dsc": "<product description>",
      "brand": "<brand>",
      "category": "<category>",
      "removal_rationale": "<why remove — specific performance issue>",
      "shelf_space_freed": "<estimated linear feet or facing count>"
    }
  ],
  "net_revenue_impact": "<estimated weekly revenue change from these moves>",
  "summary": "<2-sentence recommendation summary>"
}"""


def run_store_recommender_agent(state: dict) -> dict:
    store_id = state.get("store_id", 36)

    # First get network coverage to understand this store's position
    coverage = get_network_vs_store_coverage()
    gaps = get_assortment_gaps_by_store(store_id)

    # Find this store's coverage stats
    store_coverage = next(
        (s for s in coverage if s["store_id"] == store_id), {}
    )

    llm = ChatAnthropic(model=MODEL, max_tokens=1500)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Store {store_id} coverage stats:\n"
                f"{json.dumps(store_coverage, default=str)}\n\n"
                f"Network coverage context (all stores sorted by coverage %):\n"
                f"{json.dumps(coverage[:5], default=str)}\n\n"
                f"SKUs this store is MISSING (top 5 by network sales):\n"
                f"{json.dumps(gaps['add'], default=str)}\n\n"
                f"SKUs this store IS CARRYING (sample for removal analysis):\n"
                f"{json.dumps(gaps['remove'], default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "store_id": store_id,
            "recommendation_score": 50,
            "add_recommendations": gaps["add"][:5],
            "remove_recommendations": gaps["remove"][:3],
            "net_revenue_impact": "Analysis pending",
            "summary": response.content[:300],
        }

    return {**state, "store_recommender": result}
