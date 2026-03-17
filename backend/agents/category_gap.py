"""
CategoryGapAgent
Analyses category performance vs. benchmarks using real Q4 OMNI data.
Identifies low-AGP / high-markdown / low-brand-count categories.
"""
from langchain_anthropic import ChatAnthropic
from db.queries import get_category_gap_heatmap, get_category_performance
import json

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a Category Gap analyst for Albertsons Division 20 (Southern CA).
Analyse the Q4 category sales data provided and identify:
1. Categories with LOW AGP rate (below 25%) — margin concern
2. Categories with HIGH markdown rate (above 15%) — pricing/demand concern
3. Categories with LOW brand count — limited supplier diversity
4. YOY sales DECLINE categories — demand erosion

Return a JSON object with EXACTLY these keys — no markdown, no preamble:
{
  "gap_score": <integer 0-100, higher = more opportunity>,
  "top_gaps": [
    {
      "category": "<category name>",
      "issue": "<one-line issue description>",
      "agp_pct": <float>,
      "mkdn_pct": <float>,
      "recommendation": "<specific action>"
    }
  ],
  "summary": "<2-sentence insight for Monday briefing>"
}
Return ONLY valid JSON."""


def run_category_gap_agent(state: dict) -> dict:
    data = get_category_gap_heatmap()
    perf = get_category_performance(limit=10)

    llm = ChatAnthropic(model=MODEL, max_tokens=1000)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Category gap heatmap (top 15 by gap score):\n"
                f"{json.dumps(data[:15], default=str)}\n\n"
                f"Top 10 categories by Q4 sales:\n"
                f"{json.dumps(perf[:10], default=str)}"
            ),
        },
    ])

    try:
        result = json.loads(response.content)
    except Exception:
        result = {
            "gap_score": 50,
            "top_gaps": [],
            "summary": response.content[:300],
        }

    return {**state, "category_gap": result}
