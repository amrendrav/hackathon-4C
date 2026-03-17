# ACI — Assortment Intelligence Platform
## API Reference & Curl Playbook

**Base URL:** `http://localhost:8000`
**Stack:** FastAPI + DuckDB + LangGraph + Claude (claude-sonnet-4-5)
**Division:** Albertsons Division 20 — Southern

---

## Setup

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ACI_DB_PATH=/Users/amrendravimal/workspace/hackathon/aci.duckdb

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start server
./start_backend.sh
# → Uvicorn running on http://127.0.0.1:8000
```

---

## Endpoints

### 1. Health Check

**No LLM · <100ms**

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "ACI",
  "version": "2.0.0",
  "db": "connected"
}
```

---

### 2. Monday Briefing Summary *(DuckDB only)*

**No LLM · <1s**

```bash
curl http://localhost:8000/api/briefing-summary
```

**Response:**
```json
{
  "sales_health": {
    "total_sales": 132898075.0,
    "sales_vs_ly": 10177668.0,
    "avg_agp_pct": 126.1,
    "avg_markdown_pct": 10.1,
    "active_categories": 82
  },
  "top_gainers": [
    { "category": "8407 - BERRIES",   "sales_change": 731776.65,  "agp_pct": 39.0 },
    { "category": "4205 - NOVELTIES", "sales_change": 441445.81,  "agp_pct": 1617.4 },
    { "category": "8419 - CHERRIES",  "sales_change": 366901.75,  "agp_pct": 20.1 }
  ],
  "top_decliners": [
    { "category": "8476 - FRESH CUT",              "sales_change": -853261.98, "markdown_pct": 12.9 },
    { "category": "8404 - AVOCADO",                "sales_change": -406083.75, "markdown_pct": 50.3 },
    { "category": "4801 - FROZEN MEALS SINGLE SERVE","sales_change": -317981.99, "markdown_pct": 6.2 }
  ],
  "coverage_gaps": [
    { "store_id": 3622, "region": "Southern CA", "store_size_tier": "Small",  "gap_skus": 188.0 },
    { "store_id": 3624, "region": "Northern TX",  "store_size_tier": "Small",  "gap_skus": 179.0 },
    { "store_id": 2706, "region": "Southern CA", "store_size_tier": "Medium", "gap_skus": 136.0 }
  ],
  "clip_stats": {
    "total_clips": 4439,
    "unique_offers": 4421
  }
}
```

---

### 3. Category Gap Heatmap *(DuckDB only)*

**No LLM · <1s**

```bash
curl "http://localhost:8000/api/category-gap?limit=5"
```

| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 30 | Max rows in `performance` list |

**Response (truncated to top 3):**
```json
{
  "heatmap": [
    {
      "category": "8499 - PRODUCE SUPPLIES/MATERIALS",
      "group_name": "84 - FRESH PRODUCE",
      "total_sales": 15.36,
      "agp_pct": -26767.0,
      "markdown_pct": 0.0,
      "brand_count": 1,
      "gap_score": 10776.8
    },
    {
      "category": "8414 - STONE FRUIT",
      "group_name": "84 - FRESH PRODUCE",
      "total_sales": 27752.91,
      "agp_pct": -40.3,
      "markdown_pct": 0.1,
      "brand_count": 11,
      "gap_score": 86.1
    },
    {
      "category": "4610 - FROZEN JUICE SMOOTHIE",
      "group_name": "46 - FROZEN JUICE",
      "total_sales": 42235.82,
      "agp_pct": 4.6,
      "markdown_pct": 35.6,
      "brand_count": 5,
      "gap_score": 78.7
    }
  ],
  "performance": [
    {
      "category": "4201 - PACKAGED ICE CREAM",
      "subclass": "42010201 - PACKAGED ICE CREAM M-S TRADITIONAL",
      "total_sales": 4313292.41,
      "sales_change": 55995.99,
      "agp_pct": 1536.9,
      "markdown_pct": 39.9,
      "total_units": 686216.0,
      "brand_count": 13,
      "category_role": "Trip Driver"
    }
  ]
}
```

---

### 4. Network vs Store SKU Coverage *(DuckDB only)*

**No LLM · <1s**

```bash
curl http://localhost:8000/api/store-coverage
```

**Response (all 15 stores):**
```json
{
  "data": [
    { "store_id": 3622, "region": "Southern CA", "store_size_tier": "Small",  "banner": "Albertsons", "network_skus": 303, "carried_skus": 115.0, "gap_skus": 188.0, "coverage_pct": 38.0 },
    { "store_id": 3624, "region": "Northern TX",  "store_size_tier": "Small",  "banner": "Albertsons", "network_skus": 303, "carried_skus": 124.0, "gap_skus": 179.0, "coverage_pct": 40.9 },
    { "store_id": 2706, "region": "Southern CA", "store_size_tier": "Medium", "banner": "Albertsons", "network_skus": 303, "carried_skus": 167.0, "gap_skus": 136.0, "coverage_pct": 55.1 },
    { "store_id": 38,   "region": "Northern TX",  "store_size_tier": "Medium", "banner": "Albertsons", "network_skus": 303, "carried_skus": 168.0, "gap_skus": 135.0, "coverage_pct": 55.4 },
    { "store_id": 37,   "region": "Gulf Coast",   "store_size_tier": "Medium", "banner": "Albertsons", "network_skus": 303, "carried_skus": 183.0, "gap_skus": 120.0, "coverage_pct": 60.4 },
    { "store_id": 36,   "region": "Southern CA", "store_size_tier": "Large",  "banner": "Vons",        "network_skus": 303, "carried_skus": 217.0, "gap_skus": 86.0,  "coverage_pct": 71.6 },
    { "store_id": 3621, "region": "Northern TX",  "store_size_tier": "Large",  "banner": "Albertsons", "network_skus": 303, "carried_skus": 237.0, "gap_skus": 66.0,  "coverage_pct": 78.2 }
  ]
}
```

---

### 5. Store Add/Remove Recommendations *(DuckDB only)*

**No LLM · <1s**

```bash
curl http://localhost:8000/api/store-recommendations/36
```

| Path Param | Description |
|------------|-------------|
| `store_id` | Store number (e.g. 36 = Vons Southern CA Large) |

**Response:**
```json
{
  "store_id": 36,
  "add": [
    {
      "upc_id": 78535702560,
      "upc_dsc": "Peets Coff Frnch Rst Dark Rst Grnd Coff Bag",
      "category_nm": "Coffee",
      "sub_class_nm": "Coffee Prepack Ground Premium",
      "brand": "Peets",
      "own_brands_ind": false,
      "total_sales": 173.72,
      "agp_pct": 30.0
    },
    {
      "upc_id": 73341100009,
      "upc_dsc": "Illy Normale Whole Bean Coffee",
      "category_nm": "Coffee",
      "sub_class_nm": "Coffee Canisters Ground Specialty -Ns",
      "brand": "Illy",
      "own_brands_ind": false,
      "total_sales": 173.72,
      "agp_pct": 30.0
    },
    {
      "upc_id": 20120700000,
      "upc_dsc": "Beef Ribeye Steak Boneless",
      "category_nm": "Conventional Beef",
      "sub_class_nm": "Conv Beef Select Value Cut",
      "brand": "Random Weight/Lac Unassigned",
      "own_brands_ind": false,
      "total_sales": 90.63,
      "agp_pct": 30.0
    }
  ],
  "remove": [
    {
      "upc_id": 85739400610,
      "upc_dsc": "Little Leaf Farms Crispy Green Leaf",
      "category_nm": "Salads Packaged",
      "sub_class_nm": "Salads Pkgd Green House Boxed Leafy Greens",
      "brand": "Little Leaf Farms",
      "is_carried": true
    },
    {
      "upc_id": 5100016721,
      "upc_dsc": "Campbells Healthy Request Homestyle Chicken Noodle Soup",
      "category_nm": "Condensed Soup",
      "brand": "Campbells",
      "is_carried": true
    }
  ]
}
```

---

### 6. Low Productivity SKUs *(DuckDB only)*

**No LLM · <1s**

```bash
curl "http://localhost:8000/api/low-productivity-skus?bottom_pct=0.25"
```

| Param | Default | Description |
|-------|---------|-------------|
| `bottom_pct` | 0.25 | Bottom percentile threshold (0.25 = bottom 25%) |

**Response (first 2 of 30):**
```json
{
  "data": [
    {
      "category": "9993 - NON-SPECIFIED PRODUCE",
      "subclass": "99930000 - NON-SPECIFIED PRODUCE",
      "brand": "RANDOM WEIGHT/LAC",
      "item_role": null,
      "category_role": "Basket Builder",
      "total_sales": -103221.18,
      "agp_pct": 0.0,
      "markdown_pct": 0.0,
      "total_units": 0.0,
      "sales_pct_rank": 0.0,
      "productivity_flag": "Watch"
    },
    {
      "category": "8408 - CITRUS",
      "subclass": "84080201 - CITRUS MANDARIN BAG",
      "brand": "WONDERFUL",
      "item_role": "SSKVI",
      "category_role": "Trip Driver",
      "total_sales": -11.98,
      "agp_pct": 43.1,
      "markdown_pct": 0.0,
      "total_units": -2.0,
      "sales_pct_rank": 0.0,
      "productivity_flag": "Monitor"
    }
  ]
}
```

---

### 7. Celebration Demand by Fiscal Week *(DuckDB only)*

**No LLM · <1s**

```bash
curl http://localhost:8000/api/celebration-demand
```

**Response (first 3 of 52 weeks):**
```json
{
  "data": [
    { "fiscal_week_id": 202541, "avg_celebration_score": 0.088, "households": 2, "birthday_households": 0.0, "anniversary_households": 0.0 },
    { "fiscal_week_id": 202540, "avg_celebration_score": 0.084, "households": 2, "birthday_households": 0.0, "anniversary_households": 0.0 },
    { "fiscal_week_id": 202532, "avg_celebration_score": 0.825, "households": 2, "birthday_households": 0.0, "anniversary_households": 0.0 }
  ]
}
```

---

### 8. Promo Performance / Clip-to-Redemption *(DuckDB only)*

**No LLM · <1s**

```bash
curl http://localhost:8000/api/promo-performance
```

**Response:**
```json
{
  "data": [
    { "division_id": 34, "banner_nm": "SAFEWAY",     "offer_type": "C", "total_clips": 3574, "total_redemptions": 14, "redemption_rate_pct": 0.4 },
    { "division_id": 20, "banner_nm": "ALBERTSONS",  "offer_type": "C", "total_clips": 159,  "total_redemptions": 8,  "redemption_rate_pct": 5.0 },
    { "division_id": 19, "banner_nm": "ALBERTSONS",  "offer_type": "C", "total_clips": 9,    "total_redemptions": 4,  "redemption_rate_pct": 44.4 },
    { "division_id": 20, "banner_nm": "TOMTHUMB",    "offer_type": "C", "total_clips": 8,    "total_redemptions": 1,  "redemption_rate_pct": 12.5 }
  ]
}
```

---

### 9. Monday Briefing — Full AI Analysis *(LLM · ~20-30s)*

**Runs all 7 agents in parallel + synthesis via Claude**

```bash
curl "http://localhost:8000/api/monday-briefing?store_id=36"
```

| Param | Default | Description |
|-------|---------|-------------|
| `store_id` | 36 | Target store for store-specific agents |

**Real response (captured 2026-03-17, store_id=36, elapsed=67.5s):**

```json
{
  "store_id": 36,
  "query": "monday_briefing",
  "synthesis": {
    "overall_score": 68,
    "headline": "You're leaving $142K on the table from broken SKUs while missing $480/week in proven winners — fix the bleeding, then fill the gaps.",
    "performance_snapshot": {
      "status": "Needs Attention",
      "key_metric": "87% promotion effectiveness gap with 0.4% coupon redemption vs. 4,400+ clips",
      "vs_last_week": "Celebration shopping dropped 81% (0.469→0.088) — shift strategy to wellness routine"
    },
    "top_3_opportunities": [
      {
        "title": "Capture $479/week from 5 Proven Gap SKUs",
        "impact": "$25K annual revenue lift from premium coffee (Peets/Illy) and high-velocity beef/fresh cut",
        "agent": "store_recommender",
        "action": "Add Peets French Roast, Illy Whole Bean, Ribeye Steak, Own Brand Red Onion Diced, and Tostitos Queso to Store 36 this week"
      },
      {
        "title": "Unlock Wellness Trend Wave (88 Index Kombucha)",
        "impact": "15-20% SKU expansion in kombucha, plant protein, gluten-free aligns with 10.5 avg plant items/customer",
        "agent": "seasonal_trend + diet_affinity",
        "action": "Launch kombucha endcap Monday; certify existing GF items by Friday; add 3 oat milk yogurt SKUs to dairy set"
      },
      {
        "title": "Fix Tropical Fruit Margin Crisis ($1.17M at 3.2% AGP)",
        "impact": "Cost-plus reset could recover 8-10 margin points = $94-117K annual profit improvement",
        "agent": "category_gap",
        "action": "Implement EDLP pricing on top 10 tropical SKUs by Wednesday; shift promotions to loyalty points to protect margin"
      }
    ],
    "top_3_risks": [
      {
        "title": "Catastrophic Coupon Failure Burning Customer Trust",
        "severity": "High",
        "agent": "promotion_gap",
        "action": "URGENT: Call IT Monday AM — audit POS redemption logic where 4,000+ clips yielded 14 redemptions; escalate if not resolved by Wednesday"
      },
      {
        "title": "Dead SKU Portfolio Draining -$142K Annually",
        "severity": "High",
        "agent": "low_productivity",
        "action": "Remove 2 catch-all SKUs (9993 Produce, 9959 Frozen) this week — systemic shrink/write-offs masking operational failures"
      },
      {
        "title": "Cherry/Stone Fruit Procurement Timebomb (35% Markdown, -40.3% AGP)",
        "severity": "Medium",
        "agent": "category_gap",
        "action": "Cut Q1 cherry orders 20% immediately; suspend stone fruit until supplier contracts renegotiated"
      }
    ],
    "marketing_partnership": "Launch 'Wellness Monday' promotion — bundle kombucha + plant protein + organic produce with 3x loyalty points; test personalized Meat/Deli offers for 6 whitespace categories with ZERO digital coverage",
    "this_week_watchlist": [
      "SAFEWAY Div 34/25 coupon redemption rates (must hit >5% floor)",
      "Tropical Fruit AGP post-EDLP reset (target 11-13%)",
      "Store 36 premium coffee velocity after Peets/Illy add",
      "Frozen Juice Smoothie markdown rate (reduce 35.6%→20%)"
    ],
    "agent_confidence": {
      "category_gap": 0.91,
      "demand_signal": 0.78,
      "diet_affinity": 0.64,
      "promotion_gap": 0.93,
      "seasonal_trend": 0.82,
      "low_productivity": 0.95,
      "store_recommender": 0.87
    }
  },
  "agent_traces": [
    { "agent": "category_gap",     "score": 73, "status": "complete" },
    { "agent": "demand_signal",    "score": 72, "status": "complete" },
    { "agent": "diet_affinity",    "score": 85, "status": "complete" },
    { "agent": "promotion_gap",    "score": 87, "status": "complete" },
    { "agent": "seasonal_trend",   "score": 78, "status": "complete" },
    { "agent": "low_productivity", "score": 87, "status": "complete" },
    { "agent": "store_recommender","score": 82, "status": "complete" }
  ],
  "elapsed_seconds": 67.55
}
```

> **Note:** Requires `ANTHROPIC_API_KEY` in `backend/.env`. Typical latency 60-90s (7 parallel LLM calls + synthesis). Per-agent output available in the full response alongside `synthesis`.

---

### 10. Single Agent Runner *(LLM · ~5-10s each)*

**Run one agent in isolation**

```bash
# category_gap
curl "http://localhost:8000/api/agents/category_gap?store_id=36"

# demand_signal
curl "http://localhost:8000/api/agents/demand_signal?store_id=36"

# diet_affinity
curl "http://localhost:8000/api/agents/diet_affinity?store_id=36"

# promotion_gap
curl "http://localhost:8000/api/agents/promotion_gap?store_id=36"

# seasonal_trend
curl "http://localhost:8000/api/agents/seasonal_trend?store_id=36"

# low_productivity
curl "http://localhost:8000/api/agents/low_productivity?store_id=36"

# store_recommender
curl "http://localhost:8000/api/agents/store_recommender?store_id=36"
```

| Param | Default | Valid values |
|-------|---------|-------------|
| `store_id` | 36 | Any store_id from `/api/store-coverage` |
| *(path)* `agent_name` | — | `category_gap`, `demand_signal`, `diet_affinity`, `promotion_gap`, `seasonal_trend`, `low_productivity`, `store_recommender` |

**Real responses (captured 2026-03-17):**

#### `category_gap`
```json
{
  "store_id": 36,
  "query": "category_gap",
  "category_gap": {
    "gap_score": 73,
    "top_gaps": [
      {
        "category": "8499 - PRODUCE SUPPLIES/MATERIALS",
        "issue": "Extreme negative AGP (-26,767%) indicates severe cost structure problem",
        "agp_pct": -26767.0,
        "mkdn_pct": 0.0,
        "recommendation": "Immediately audit costing/pricing structure; single-brand dependency requires backup supplier evaluation"
      },
      {
        "category": "8415 - TROPICAL FRUIT",
        "issue": "High-volume category ($1.17M) with extremely low AGP (3.2%) and elevated markdown (19.5%)",
        "agp_pct": 3.2,
        "mkdn_pct": 19.5,
        "recommendation": "Renegotiate supplier terms for top sellers; implement dynamic pricing to reduce waste-driven markdowns"
      },
      {
        "category": "8414 - STONE FRUIT",
        "issue": "Negative AGP (-40.3%) signals below-cost selling across 11 brands",
        "agp_pct": -40.3,
        "mkdn_pct": 0.1,
        "recommendation": "Emergency price floor implementation; evaluate seasonality-driven shrink and recalibrate order quantities"
      }
    ],
    "summary": "Three categories require urgent intervention: Produce Supplies has catastrophic -26,767% AGP indicating a systemic cost error, Stone Fruit is selling at -40% gross profit destroying value on every unit, and Tropical Fruit's $1.17M revenue base is being eroded by 3.2% AGP and 19.5% markdown dependency."
  }
}
```

#### `demand_signal`
```json
{
  "store_id": 36,
  "query": "demand_signal",
  "demand_signal": {
    "demand_score": 72,
    "segment_insights": [
      {
        "segment": "FAMILY FOCUSED",
        "trend": "Growing",
        "category_affinity": "Coffee and Value Proteins",
        "action": "Expand mainstream coffee pods and value-pack beef offerings to capture Price Driven shoppers seeking Easy Shopping convenience"
      },
      {
        "segment": "CONVENIENTLY FRESH",
        "trend": "Stable",
        "category_affinity": "Fresh Cut and Premium Coffee",
        "action": "Maintain quality-driven ready-to-eat fresh items; consider premium coffee subscriptions for Quality-Driven Easy Eating preference"
      },
      {
        "segment": "CONVENIENCE SEEKERS",
        "trend": "Growing",
        "category_affinity": "Coffee Pods and Frozen Prepared",
        "action": "Increase breadth in premium coffee and frozen meal solutions to satisfy Quality-Driven shoppers across multiple need states"
      }
    ],
    "high_velocity_categories": ["Coffee", "Conventional Beef", "Fresh Cut", "Salty Snacks"],
    "emerging_trends": ["Plant-based proteins", "Specialty coffee", "Convenience meal solutions"],
    "summary": "Store 36 serves 4 primary segments all trending toward premium convenience and coffee. The demand signal is strongest for premium coffee (Peets, Illy gap confirmed by $173/wk network data) and fresh cut vegetables. Families and convenience seekers represent the highest growth vectors requiring immediate assortment action."
  }
}
```

#### `diet_affinity`
```json
{
  "store_id": 36,
  "query": "diet_affinity",
  "diet_affinity": {
    "diet_gap_score": 85,
    "gaps": [
      {
        "diet": "gluten_free",
        "customer_demand": "0% flagged but 10.5 avg plant-based items purchased suggests latent demand",
        "catalog_gap": "Zero gluten-free certified SKUs in catalog despite 21% of consumers actively avoiding gluten",
        "opportunity": "Launch own-brand GF lines in Salty Snacks, Ready-to-Serve Soups, and Condensed Soups"
      },
      {
        "diet": "dairy_free",
        "customer_demand": "High protein purchases (2,222 avg items) indicates protein-focused shoppers seeking dairy alternatives",
        "catalog_gap": "No dairy-free alternatives in Refrigerated Yogurt (4 SKUs all dairy-based)",
        "opportunity": "Add oat/coconut/almond yogurt alternatives and plant-based creamers — fastest growing dairy segments"
      },
      {
        "diet": "keto",
        "customer_demand": "0% flagged customers despite keto being 5% of US population",
        "catalog_gap": "Keto catalog weighted toward carb-heavy items rather than true keto options",
        "opportunity": "Introduce keto-certified product line: low-carb bread alternatives, sugar-free condiments, cheese crisps"
      }
    ],
    "summary": "Critical diet certification gap: zero gluten-free, dairy-free, or keto-certified SKUs in catalog despite 10.5 average plant-based items per customer transaction. Customers are already buying plant-forward but the store isn't meeting dietary restriction needs. Immediate certification labeling and 3-5 new diet-friendly SKUs per segment would capture this high-value demand."
  }
}
```

#### `promotion_gap`
```json
{
  "store_id": 36,
  "query": "promotion_gap",
  "promotion_gap": {
    "promo_gap_score": 87,
    "underperforming_offers": [
      {
        "offer_type": "Manufacturer Coupon (Type C)",
        "total_clips": 4438,
        "redemption_rate_pct": 0.7,
        "issue": "Catastrophic failure: 4,438 clips yielding only 29 redemptions. Likely POS integration issues.",
        "fix": "URGENT: Audit POS coupon acceptance logic with IT. Simplify manufacturer coupon terms and add in-app redemption instructions."
      },
      {
        "offer_type": "SAFEWAY Division 34 Coupons",
        "total_clips": 3574,
        "redemption_rate_pct": 0.4,
        "issue": "Massive clip volume but near-zero redemption suggests technical malfunction or geo-targeting errors.",
        "fix": "Investigate Division 34 offer serving logic. Verify offers are geographically restricted to active SAFEWAY stores."
      }
    ],
    "whitespace_categories": ["Meat & Seafood", "Deli & Prepared Foods", "Bakery", "Baby Care & Products", "Pet Care", "Wine & Beer"],
    "summary": "Critical promotion failure detected: 4,438 manufacturer coupons clipped but only 29 redeemed (0.7% rate) signals systemic POS integration breakdown. Simultaneously, 8 high-value categories including Meat, Deli, and Pet Care have zero digital offer coverage, representing massive untapped revenue opportunity for CPG partnerships."
  }
}
```

#### `seasonal_trend`
```json
{
  "store_id": 36,
  "query": "seasonal_trend",
  "seasonal_trend": {
    "trend_score": 78,
    "upcoming_spikes": [
      {
        "week": "202541",
        "celebration_score": 0.088,
        "category": "Bakery & Party Supplies",
        "signal": "Post-holiday normalization; prepare for Columbus Day (Oct 14) rebound",
        "confidence": 0.72
      },
      {
        "week": "202542",
        "celebration_score": 0.45,
        "category": "Seasonal Decor & Candy",
        "signal": "Halloween preparation window begins mid-October; expect scores to climb toward 0.8+",
        "confidence": 0.85
      }
    ],
    "trending_now": [
      { "keyword": "kombucha", "trend_index": 88, "related_category": "Beverages - Functional Drinks" },
      { "keyword": "plant based protein", "trend_index": 81, "related_category": "Natural Foods" },
      { "keyword": "air fryer meals", "trend_index": 75, "related_category": "Frozen Prepared Foods" }
    ],
    "summary": "Post-celebration dip (0.088 score vs 0.46 baseline) signals shift from party to routine shopping — lead with wellness and convenience vs. party supplies. Halloween window opening in weeks 202542-202545 will drive 3-4x celebration score increase; stock seasonal candy/decor now. Kombucha (88 trend index) and plant protein (81) represent growing health trends to capitalize on immediately."
  }
}
```

#### `low_productivity`
```json
{
  "store_id": 36,
  "query": "low_productivity",
  "low_productivity": {
    "productivity_score": 87,
    "flagged_skus": [
      {
        "brand": "RANDOM WEIGHT/LAC",
        "category": "9993 - NON-SPECIFIED PRODUCE",
        "total_sales": -103221.18,
        "agp_pct": 0.0,
        "risk_level": "High Risk",
        "removal_rationale": "Massive negative sales impact (-$103K) with zero margin. Catch-all code masking returns/waste.",
        "replacement_suggestion": "Eliminate entirely. Implement proper produce tracking to prevent catch-all SKU usage."
      },
      {
        "brand": "RANDOM WEIGHT/LAC",
        "category": "9959 - NON-SPECIFIED FROZEN FOODS",
        "total_sales": -38885.02,
        "agp_pct": 0.0,
        "risk_level": "High Risk",
        "removal_rationale": "Loss leader (-$38.9K) with zero margin. Non-specified catch-all drains profitability.",
        "replacement_suggestion": "Remove immediately. Add premium frozen meal kits or plant-based proteins."
      }
    ],
    "total_sales_at_risk": -142139.66,
    "shelf_space_opportunity": "Removing 14 non-performing SKUs frees ~18-24 linear feet for high-margin organic produce and premium frozen innovations.",
    "summary": "Immediate action required on 14 SKUs draining $142K annually, with two non-specified catch-all codes accounting for 99% of losses. Removal creates 18-24 feet for high-margin organic produce and premium frozen innovations."
  }
}
```

#### `store_recommender`
```json
{
  "store_id": 36,
  "query": "store_recommender",
  "store_recommender": {
    "store_id": 36,
    "recommendation_score": 82,
    "add_recommendations": [
      {
        "upc_dsc": "Peets Coff Frnch Rst Dark Rst Grnd Coff Bag",
        "brand": "Peets",
        "category": "Coffee",
        "rationale": "Top network performer with $173.72 weekly sales. CA heritage brand with high loyalty in Southern CA affluent markets. 30% margin.",
        "expected_weekly_sales": 28.5,
        "segment_fit": "Premium coffee enthusiasts, CA-native brand loyalists"
      },
      {
        "upc_dsc": "Illy Normale Whole Bean Coffee",
        "brand": "Illy",
        "category": "Coffee",
        "rationale": "$173.72 weekly network sales, 30% margin. Fills whole bean specialty gap for discerning customers.",
        "expected_weekly_sales": 27.0,
        "segment_fit": "Specialty coffee connoisseurs, whole bean brewers"
      },
      {
        "upc_dsc": "Beef Ribeye Steak Boneless",
        "brand": "Random Weight/Lac Unassigned",
        "category": "Conventional Beef",
        "rationale": "$90.63 network sales. Premium cut with high margin; essential for weekend grilling destination.",
        "expected_weekly_sales": 45.0,
        "segment_fit": "Weekend grillers, special occasion meal planners"
      }
    ],
    "remove_recommendations": [
      {
        "upc_dsc": "Stonyfield Blueberry Apple Carrot Pouch Yogurt",
        "rationale": "Niche flavor in oversaturated kids organic segment. Free space for core flavors with higher velocity."
      },
      {
        "upc_dsc": "A-1 Steak Sauce",
        "rationale": "Legacy brand declining. Replace with trending chimichurri, Korean BBQ, or gourmet sauces."
      }
    ],
    "net_revenue_impact": "+$450-500 estimated weekly revenue increase",
    "summary": "Store 36 should immediately add 5 critical gap SKUs led by premium coffee (Peets, Illy) and key proteins/convenience items. Remove 3 redundant/declining SKUs to optimize shelf productivity."
  }
}
```

> **Note:** Requires `ANTHROPIC_API_KEY` in `backend/.env`.

---

## Quick Reference

| Endpoint | LLM | Latency | Key Output |
|----------|-----|---------|------------|
| `GET /api/health` | No | <100ms | DB connectivity |
| `GET /api/briefing-summary` | No | <1s | $132M sales, top gainers/decliners |
| `GET /api/category-gap` | No | <1s | Gap heatmap, 82 categories |
| `GET /api/store-coverage` | No | <1s | 15 stores, coverage 38–78% |
| `GET /api/store-recommendations/{id}` | No | <1s | Add/remove SKU candidates |
| `GET /api/low-productivity-skus` | No | <1s | Bottom-quartile rationalization |
| `GET /api/celebration-demand` | No | <1s | 52-week celebration predictions |
| `GET /api/promo-performance` | No | <1s | Clip-to-redemption by banner |
| `GET /api/monday-briefing` | **Yes** | 15-30s | Full AI briefing, all 7 agents |
| `GET /api/agents/{name}` | **Yes** | 5-10s | Single agent output |
