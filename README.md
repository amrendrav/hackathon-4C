# ACI — Assortment Intelligence Platform

> **AI-powered Monday Morning Briefing for Albertsons Division 20 (Southern CA)**
>
> Seven specialist Claude agents run in parallel, analyse real Q4 OMNI retail data, and synthesise actionable assortment recommendations — all delivered in under 90 seconds.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline Flow](#agent-pipeline-flow)
- [Data Flow](#data-flow)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)

---

## Overview

ACI answers the question every category manager asks Monday morning: **"What do I need to fix, add, or drop this week?"**

It does this by running seven specialist AI agents in parallel — each analysing a different lens of the business — then synthesising their outputs into a single prioritised briefing with an overall health score, top 3 opportunities, top 3 risks, and concrete actions.

**Real results from Store 36 (Vons, Southern CA):**
- **Overall score:** 68/100 — "Needs Attention"
- **Headline:** *"You're leaving $142K on the table from broken SKUs while missing $480/week in proven winners"*
- **Top risk:** 4,438 coupons clipped, only 29 redeemed (0.7%) — catastrophic POS integration failure
- **Top opportunity:** Add Peet's French Roast + Illy Whole Bean for $305/week at 30% margin

---

## Architecture

```mermaid
graph TB
    subgraph Client
        UI[Frontend / curl]
    end

    subgraph FastAPI["FastAPI  (port 8000)"]
        API[main.py]
    end

    subgraph Orchestrator["Orchestrator Agent"]
        ORC[orchestrator.py<br/>ThreadPoolExecutor × 7]
        SYN[Synthesizer<br/>Claude claude-sonnet-4-5]
    end

    subgraph Agents["7 Specialist Agents  (parallel)"]
        A1[CategoryGapAgent]
        A2[DemandSignalAgent]
        A3[DietAffinityAgent]
        A4[PromotionGapAgent]
        A5[SeasonalTrendAgent]
        A6[LowProductivityAgent]
        A7[StoreRecommenderAgent]
    end

    subgraph Data["Data Layer"]
        DB[(DuckDB<br/>aci.duckdb<br/>Q4 OMNI data)]
        RAG[(ChromaDB<br/>Product Catalog<br/>303 SKUs)]
    end

    subgraph LLM["Anthropic Claude"]
        CL[claude-sonnet-4-5<br/>per-agent analysis]
        CS[claude-sonnet-4-5<br/>synthesis]
    end

    UI -->|GET /api/monday-briefing| API
    API --> ORC
    ORC -->|asyncio.gather| A1 & A2 & A3 & A4 & A5 & A6 & A7
    A1 & A2 & A3 & A4 & A5 & A6 & A7 -->|DuckDB queries| DB
    A3 -->|semantic search| RAG
    A1 & A2 & A3 & A4 & A5 & A6 & A7 -->|invoke| CL
    ORC -->|merged state| SYN
    SYN -->|invoke| CS
    SYN -->|Monday Briefing JSON| API
    API -->|response| UI
```

---

## Agent Pipeline Flow

```mermaid
sequenceDiagram
    participant C as curl / Frontend
    participant F as FastAPI
    participant O as Orchestrator
    participant DB as DuckDB
    participant LLM as Claude (claude-sonnet-4-5)
    participant S as Synthesizer

    C->>F: GET /api/monday-briefing?store_id=36
    F->>O: run_all_agents_parallel(store_id=36)

    par 7 agents in parallel (ThreadPoolExecutor)
        O->>DB: get_category_gap_heatmap()
        DB-->>O: 82 categories, AGP/markdown data
        O->>LLM: CategoryGap analysis
        LLM-->>O: {gap_score: 73, top_gaps: [...]}

        O->>DB: get_segment_distribution()
        DB-->>O: customer segment data
        O->>LLM: DemandSignal analysis
        LLM-->>O: {demand_score: 72, ...}

        O->>DB: get_diet_flags_summary()
        DB-->>O: diet flag data
        O->>LLM: DietAffinity analysis
        LLM-->>O: {diet_gap_score: 85, ...}

        O->>DB: get_clip_to_redemption_rate()
        DB-->>O: promo performance data
        O->>LLM: PromotionGap analysis
        LLM-->>O: {promo_gap_score: 87, ...}

        O->>DB: get_celebration_demand_by_week()
        DB-->>O: 52-week celebration scores
        O->>LLM: SeasonalTrend analysis
        LLM-->>O: {trend_score: 78, ...}

        O->>DB: get_low_productivity_skus(0.25)
        DB-->>O: bottom-quartile SKUs
        O->>LLM: LowProductivity analysis
        LLM-->>O: {productivity_score: 87, ...}

        O->>DB: get_assortment_gaps_by_store(36)
        DB-->>O: network vs store coverage
        O->>LLM: StoreRecommender analysis
        LLM-->>O: {recommendation_score: 82, ...}
    end

    O->>S: merged state (all 7 outputs)
    S->>LLM: synthesize Monday Briefing
    LLM-->>S: {overall_score, headline, top_3_opportunities, ...}
    S-->>F: ACIState (full briefing + agent traces)
    F-->>C: JSON response (~67s, 26KB)
```

---

## Data Flow

```mermaid
flowchart LR
    subgraph Raw["Raw Data (Day 1)"]
        XL1[Q4 OMNI Sales XLSB]
        XL2[Promo Clip/Redemption XLSB]
        XL3[Customer Segments CSV]
        XL4[Store Coverage XLSB]
        XL5[Celebration Demand CSV]
    end

    subgraph Pipeline["build_pipeline.py"]
        P1[pandas + pyxlsb<br/>parse & clean]
        P2[DuckDB<br/>load tables]
    end

    subgraph DuckDB["aci.duckdb (tables)"]
        T1[category_performance]
        T2[clip_redemption]
        T3[segment_distribution]
        T4[store_coverage]
        T5[celebration_demand]
        T6[products]
        T7[assortment_gaps]
    end

    subgraph RAG["ChromaDB (backend/db/chroma/)"]
        V1[product_catalog<br/>all-MiniLM-L6-v2<br/>303 SKU embeddings]
    end

    subgraph Queries["backend/db/queries.py"]
        Q1[get_category_gap_heatmap]
        Q2[get_clip_to_redemption_rate]
        Q3[get_segment_distribution]
        Q4[get_assortment_gaps_by_store]
        Q5[get_low_productivity_skus]
        Q6[get_celebration_demand_by_week]
        Q7[get_network_vs_store_coverage]
    end

    XL1 & XL2 & XL3 & XL4 & XL5 --> P1 --> P2
    P2 --> T1 & T2 & T3 & T4 & T5 & T6 & T7
    T6 -->|catalog_rag.py| V1
    T1 --> Q1
    T2 --> Q2
    T3 --> Q3
    T4 & T7 --> Q4
    T1 --> Q5
    T5 --> Q6
    T4 --> Q7
```

---

## API Endpoints

| Endpoint | LLM | Latency | Description |
|----------|:---:|---------|-------------|
| `GET /api/health` | — | <100ms | DB connectivity check |
| `GET /api/briefing-summary` | — | <1s | Raw Monday snapshot (sales KPIs) |
| `GET /api/category-gap` | — | <1s | Gap heatmap for 82 categories |
| `GET /api/store-coverage` | — | <1s | Network vs store SKU coverage (15 stores) |
| `GET /api/store-recommendations/{id}` | — | <1s | Add/remove SKU candidates for a store |
| `GET /api/low-productivity-skus` | — | <1s | Bottom-quartile rationalization candidates |
| `GET /api/celebration-demand` | — | <1s | 52-week celebration purchase predictions |
| `GET /api/promo-performance` | — | <1s | Clip-to-redemption rates by banner |
| **`GET /api/monday-briefing`** | **✓** | **60-90s** | **Full AI briefing — all 7 agents + synthesis** |
| `GET /api/agents/{name}` | ✓ | 5-15s | Single agent in isolation |

**Agent names:** `category_gap` · `demand_signal` · `diet_affinity` · `promotion_gap` · `seasonal_trend` · `low_productivity` · `store_recommender`

Full curl examples and real responses → [`docs/api-reference.md`](docs/api-reference.md)

---

## Project Structure

```
hackathon/
├── build_pipeline.py          # Day 1: raw XLSB/CSV → aci.duckdb
├── aci.duckdb                 # DuckDB database (gitignored)
├── start_backend.sh           # Server launcher (sets ACI_DB_PATH)
├── docs/
│   └── api-reference.md       # Full curl playbook + real AI responses
│
└── backend/
    ├── main.py                # FastAPI app, all route handlers
    ├── requirements.txt       # Python dependencies
    ├── .env.example           # Environment variable template
    │
    ├── agents/
    │   ├── orchestrator.py    # Parallel fan-out + synthesis
    │   ├── category_gap.py    # Low-AGP / high-markdown categories
    │   ├── demand_signal.py   # Customer segment velocity trends
    │   ├── diet_affinity.py   # Diet flag gaps (GF, vegan, keto, dairy-free)
    │   ├── promotion_gap.py   # Clip-to-redemption failure analysis
    │   ├── seasonal_trend.py  # Celebration demand + Google Trends
    │   ├── low_productivity.py # Bottom-quartile SKU rationalization
    │   └── store_recommender.py # Network gap → store add/remove
    │
    ├── db/
    │   └── queries.py         # All DuckDB query functions
    │
    ├── rag/
    │   └── catalog_rag.py     # ChromaDB product catalog (semantic search)
    │
    └── tools/
        └── mcp_tools.py       # Action tools: pilot, flag, revenue estimate
```

---

## Quick Start

```bash
# 1. Clone and enter repo
git clone https://github.com/amrendrav/hackathon-4C.git
cd hackathon-4C

# 2. Build the database (requires raw data files in data/)
python build_pipeline.py

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ACI_DB_PATH=/absolute/path/to/aci.duckdb

# 5. (Optional) Build the RAG product catalog index
cd backend && python rag/catalog_rag.py && cd ..

# 6. Start the server
./start_backend.sh
# → Uvicorn running on http://127.0.0.1:8000

# 7. Verify
curl http://localhost:8000/api/health
# → {"status":"ok","service":"ACI","version":"2.0.0","db":"connected"}

# 8. Run Monday Briefing (requires ANTHROPIC_API_KEY)
curl "http://localhost:8000/api/monday-briefing?store_id=36" | python3 -m json.tool
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Anthropic Claude (`claude-sonnet-4-5`) via `langchain-anthropic` |
| **Agent framework** | LangGraph `StateGraph` + `asyncio` ThreadPoolExecutor |
| **API** | FastAPI + Uvicorn |
| **Database** | DuckDB (analytical queries on Q4 OMNI retail data) |
| **Vector search** | ChromaDB + `all-MiniLM-L6-v2` sentence-transformers |
| **Data ingestion** | pandas + pyxlsb + openpyxl |
| **Trend data** | pytrends (Google Trends API fallback) |
| **Language** | Python 3.11+ |
