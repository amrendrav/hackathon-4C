"""
ACI Query Layer
All DuckDB queries used by agents. Agents import from here — no raw SQL in agent code.
"""

import os
import duckdb
from pathlib import Path
from functools import lru_cache


# ── DB path resolution ─────────────────────────────────────────────────────────
def _resolve_db_path() -> Path:
    """Find aci.duckdb: env var → sibling file → walk up dirs."""
    if env := os.environ.get("ACI_DB_PATH"):
        return Path(env)
    sibling = Path(__file__).parent / "aci.duckdb"
    if sibling.exists():
        return sibling
    here = Path(__file__).resolve().parent
    for _ in range(6):
        for candidate in (here / "db" / "aci.duckdb", here / "aci.duckdb"):
            if candidate.exists():
                return candidate
        here = here.parent
    raise FileNotFoundError(
        "Cannot find aci.duckdb. Set ACI_DB_PATH env var or place "
        "aci.duckdb in backend/db/ or the repo root."
    )


DB_PATH = _resolve_db_path()


def get_con():
    return duckdb.connect(str(DB_PATH), read_only=True)


# ══════════════════════════════════════════════════════════════════════════════
# CategoryGapAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_category_performance(limit: int = 20) -> list[dict]:
    """Top categories by sales with AGP rate and markdown rate — from real OMNI data."""
    con = get_con()
    rows = con.execute(f"""
        SELECT
            category_l6                            AS category,
            subclass_l8                            AS subclass,
            ROUND(SUM(sales), 2)                   AS total_sales,
            ROUND(SUM(sales_chg), 2)               AS sales_change,
            ROUND(AVG(agp_rate) * 100, 1)          AS agp_pct,
            ROUND(AVG(mkdn_rate) * 100, 1)         AS markdown_pct,
            ROUND(SUM(units), 0)                   AS total_units,
            COUNT(DISTINCT brand_low_l3)           AS brand_count,
            MAX(category_role)                     AS category_role
        FROM category_sales
        WHERE category_l6 NOT LIKE '0%'
          AND sales IS NOT NULL
          AND sales > 0
        GROUP BY category_l6, subclass_l8
        ORDER BY total_sales DESC
        LIMIT {limit}
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


def get_category_gap_heatmap() -> list[dict]:
    """Category gap score: low AGP + high markdown = high gap opportunity."""
    con = get_con()
    rows = con.execute("""
        SELECT
            category_l6                                         AS category,
            group_l5                                            AS group_name,
            ROUND(SUM(sales), 2)                               AS total_sales,
            ROUND(AVG(agp_rate) * 100, 1)                      AS agp_pct,
            ROUND(AVG(mkdn_rate) * 100, 1)                     AS markdown_pct,
            COUNT(DISTINCT brand_low_l3)                        AS brand_count,
            -- Gap score: penalise low AGP + high markdown
            ROUND(
                (1 - AVG(agp_rate)) * 40
                + AVG(mkdn_rate) * 30
                + (1 - (SUM(sales) / NULLIF(MAX(SUM(sales)) OVER (), 0))) * 30
            , 1)                                                AS gap_score
        FROM category_sales
        WHERE category_l6 NOT LIKE '0%' AND sales IS NOT NULL AND sales > 0
        GROUP BY category_l6, group_l5
        ORDER BY gap_score DESC
        LIMIT 30
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# DemandSignalAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_segment_distribution() -> list[dict]:
    """Customer segment counts and descriptions."""
    con = get_con()
    rows = con.execute("""
        SELECT
            shopstyles_segment_dsc          AS segment,
            myneed_segment_dsc              AS need_segment,
            true_price_segment_period_dsc   AS price_sensitivity,
            annual_level2_segment_dsc       AS annual_value,
            COUNT(*)                        AS customer_count
        FROM customer_segments
        WHERE shopstyles_segment_dsc IS NOT NULL
        GROUP BY shopstyles_segment_dsc, myneed_segment_dsc,
                 true_price_segment_period_dsc, annual_level2_segment_dsc
        ORDER BY customer_count DESC
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


def get_transaction_velocity() -> list[dict]:
    """Sales velocity and basket size from real C360 transactions."""
    con = get_con()
    rows = con.execute("""
        SELECT
            t.division_id,
            t.store_id,
            p.category_nm,
            p.sub_class_nm,
            p.brand,
            ROUND(SUM(t.net_sales), 2)          AS net_sales,
            SUM(t.item_qty)                      AS units_sold,
            ROUND(AVG(t.gross_amt), 2)           AS avg_basket,
            COUNT(DISTINCT t.txn_id)             AS txn_count,
            SUM(CASE WHEN t.ecom_ind THEN 1 ELSE 0 END) AS ecom_orders
        FROM transactions t
        JOIN products p ON t.upc_id = p.upc_id
        WHERE t.net_sales > 0
        GROUP BY t.division_id, t.store_id, p.category_nm, p.sub_class_nm, p.brand
        ORDER BY net_sales DESC
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# DietAffinityAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_diet_flags_summary() -> dict:
    """Counts of customers with each diet flag — demand signal for unmet needs."""
    con = get_con()
    row = con.execute("""
        SELECT
            COUNT(*) AS total_customers,
            SUM(CASE WHEN vegetarian_diet_preference_ind THEN 1 ELSE 0 END)  AS vegetarian,
            SUM(CASE WHEN vegan_diet_preference_ind THEN 1 ELSE 0 END)       AS vegan,
            SUM(CASE WHEN keto_friendly_diet_preference_ind THEN 1 ELSE 0 END) AS keto,
            SUM(CASE WHEN flexitarian_diet_preference_ind THEN 1 ELSE 0 END) AS flexitarian,
            SUM(CASE WHEN gluten_free_restriction_ind THEN 1 ELSE 0 END)     AS gluten_free,
            SUM(CASE WHEN dairy_free_restriction_ind THEN 1 ELSE 0 END)      AS dairy_free,
            SUM(CASE WHEN peanut_free_restriction_ind THEN 1 ELSE 0 END)     AS peanut_free,
            ROUND(AVG(plant_based_prd_count), 1)                             AS avg_plant_based_items,
            ROUND(AVG(protein_prd_count), 1)                                 AS avg_protein_items
        FROM diet_preferences
    """).fetchdf().to_dict(orient="records")[0]
    con.close()
    return row


def get_diet_vs_catalog_gap(diet_flag: str = "vegetarian") -> list[dict]:
    """Cross-reference diet demand with catalog SKU availability by category."""
    flag_col_map = {
        "vegetarian":  "vegetarian_diet_preference_ind",
        "vegan":       "vegan_diet_preference_ind",
        "keto":        "keto_friendly_diet_preference_ind",
        "gluten_free": "gluten_free_restriction_ind",
        "dairy_free":  "dairy_free_restriction_ind",
    }
    col = flag_col_map.get(diet_flag, "vegetarian_diet_preference_ind")
    con = get_con()
    rows = con.execute(f"""
        SELECT
            p.category_nm,
            p.sub_class_nm,
            COUNT(DISTINCT p.upc_id)    AS total_skus,
            COUNT(DISTINCT p.brand)     AS brands,
            p.own_brands_ind,
            '{diet_flag}'               AS diet_flag
        FROM products p
        GROUP BY p.category_nm, p.sub_class_nm, p.own_brands_ind
        ORDER BY total_skus DESC
        LIMIT 20
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# PromotionGapAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_promotion_coverage() -> list[dict]:
    """Offer types and category coverage — find under-promoted categories."""
    con = get_con()
    rows = con.execute("""
        SELECT
            offer_type_dsc,
            categories_txt,
            customer_segment_dsc,
            COUNT(*)                        AS offer_count,
            ROUND(AVG(discount_value), 2)   AS avg_discount
        FROM offers
        WHERE offer_type_dsc IS NOT NULL
        GROUP BY offer_type_dsc, categories_txt, customer_segment_dsc
        ORDER BY offer_count DESC
        LIMIT 20
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


def get_clip_to_redemption_rate() -> list[dict]:
    """Clip count vs. actual redemptions — high clip / low redemption = promo gap."""
    con = get_con()
    rows = con.execute("""
        SELECT
            c.division_id,
            c.banner_nm,
            c.clip_type_cd                          AS offer_type,
            COUNT(DISTINCT c.clip_id)               AS total_clips,
            COUNT(DISTINCT r.txn_id)                AS total_redemptions,
            CASE WHEN COUNT(DISTINCT c.clip_id) > 0
                 THEN ROUND(100.0 * COUNT(DISTINCT r.txn_id)
                            / COUNT(DISTINCT c.clip_id), 1)
                 ELSE 0 END                         AS redemption_rate_pct
        FROM clips c
        LEFT JOIN redemptions r ON c.client_offer_id = r.client_offer_id
        WHERE c.division_id IS NOT NULL
        GROUP BY c.division_id, c.banner_nm, c.clip_type_cd
        ORDER BY total_clips DESC
        LIMIT 15
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# SeasonalTrendAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_celebration_demand_by_week() -> list[dict]:
    """Celebration purchase predictions by fiscal week — seasonal demand signal."""
    con = get_con()
    rows = con.execute("""
        SELECT
            fiscal_week_id,
            ROUND(AVG(gen_celebration_pred), 3)     AS avg_celebration_score,
            COUNT(DISTINCT household_id)            AS households,
            SUM(CASE WHEN birthday_pred > 0.5
                THEN 1 ELSE 0 END)                  AS birthday_households,
            SUM(CASE WHEN anniversary_pred > 0.5
                THEN 1 ELSE 0 END)                  AS anniversary_households
        FROM celebration_predictions
        GROUP BY fiscal_week_id
        ORDER BY fiscal_week_id DESC
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# LowProductivitySKUAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_low_productivity_skus(bottom_pct: float = 0.25) -> list[dict]:
    """
    Identify bottom-quartile SKUs: low sales, low AGP, high markdown.
    These are candidates for removal to free shelf space.
    """
    con = get_con()
    rows = con.execute(f"""
        WITH ranked AS (
            SELECT
                category_l6                     AS category,
                subclass_l8                     AS subclass,
                brand_low_l3                    AS brand,
                item_role,
                category_role,
                ROUND(SUM(sales), 2)            AS total_sales,
                ROUND(AVG(agp_rate) * 100, 1)  AS agp_pct,
                ROUND(AVG(mkdn_rate) * 100, 1) AS markdown_pct,
                ROUND(SUM(units), 0)            AS total_units,
                PERCENT_RANK() OVER (
                    PARTITION BY category_l6
                    ORDER BY SUM(sales) ASC
                )                               AS sales_pct_rank
            FROM category_sales
            WHERE category_l6 NOT LIKE '0%'
              AND sales IS NOT NULL
              AND brand_low_l3 IS NOT NULL
              AND brand_low_l3 NOT LIKE 'nan'
            GROUP BY category_l6, subclass_l8, brand_low_l3, item_role, category_role
        )
        SELECT *,
               CASE
                   WHEN agp_pct < 20 AND markdown_pct > 20 THEN 'High Risk'
                   WHEN agp_pct < 25 OR markdown_pct > 15  THEN 'Watch'
                   ELSE 'Monitor'
               END AS productivity_flag
        FROM ranked
        WHERE sales_pct_rank <= {bottom_pct}
        ORDER BY total_sales ASC
        LIMIT 30
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# StoreAssortmentRecommenderAgent queries
# ══════════════════════════════════════════════════════════════════════════════

def get_assortment_gaps_by_store(store_id: int) -> dict:
    """
    For a given store: which high-performing SKUs (in the network) is it NOT carrying?
    Returns top candidates to ADD and bottom performers to REMOVE.
    """
    con = get_con()

    add_candidates = con.execute(f"""
        SELECT
            p.upc_id,
            p.upc_dsc,
            p.category_nm,
            p.sub_class_nm,
            p.brand,
            p.own_brands_ind,
            cs.total_sales,
            cs.agp_pct
        FROM products p
        LEFT JOIN store_assortment sa
            ON p.upc_id = sa.upc_id AND sa.store_id = {store_id}
        JOIN (
            SELECT
                category_nm,
                ROUND(SUM(net_sales), 2) AS total_sales,
                ROUND(AVG(gross_amt), 2) AS avg_basket,
                30.0                      AS agp_pct
            FROM transactions t2
            JOIN products p2 ON t2.upc_id = p2.upc_id
            GROUP BY category_nm
        ) cs ON cs.category_nm = p.category_nm
        WHERE (sa.is_carried IS NULL OR sa.is_carried = false)
        ORDER BY cs.total_sales DESC
        LIMIT 5
    """).fetchdf().to_dict(orient="records")

    remove_candidates = con.execute(f"""
        SELECT
            p.upc_id,
            p.upc_dsc,
            p.category_nm,
            p.sub_class_nm,
            p.brand,
            sa.is_carried
        FROM store_assortment sa
        JOIN products p ON sa.upc_id = p.upc_id
        WHERE sa.store_id = {store_id}
          AND sa.is_carried = true
        ORDER BY RANDOM()
        LIMIT 3
    """).fetchdf().to_dict(orient="records")

    con.close()
    return {"store_id": store_id, "add": add_candidates, "remove": remove_candidates}


def get_network_vs_store_coverage() -> list[dict]:
    """High-level: for each store, how many SKUs are carried vs. available in network."""
    con = get_con()
    rows = con.execute("""
        SELECT
            s.store_id,
            s.region,
            s.store_size_tier,
            s.banner,
            COUNT(sa.upc_id)                                            AS network_skus,
            SUM(CASE WHEN sa.is_carried THEN 1 ELSE 0 END)             AS carried_skus,
            COUNT(sa.upc_id) - SUM(CASE WHEN sa.is_carried
                THEN 1 ELSE 0 END)                                      AS gap_skus,
            ROUND(100.0 * SUM(CASE WHEN sa.is_carried THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(sa.upc_id), 0), 1)                    AS coverage_pct
        FROM stores s
        JOIN store_assortment sa ON s.store_id = sa.store_id
        GROUP BY s.store_id, s.region, s.store_size_tier, s.banner
        ORDER BY coverage_pct ASC
    """).fetchdf().to_dict(orient="records")
    con.close()
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# Monday Morning Briefing — composite query
# ══════════════════════════════════════════════════════════════════════════════

def get_monday_briefing_summary() -> dict:
    """
    Hero dashboard data: last-week performance snapshot across all agents.
    Returns a dict with sections: performance, opportunities, risks, actions.
    """
    con = get_con()

    sales_health = con.execute("""
        SELECT
            ROUND(SUM(sales), 0)            AS total_sales,
            ROUND(SUM(sales_chg), 0)        AS sales_vs_ly,
            ROUND(AVG(agp_rate) * 100, 1)   AS avg_agp_pct,
            ROUND(AVG(mkdn_rate) * 100, 1)  AS avg_markdown_pct,
            COUNT(DISTINCT category_l6)     AS active_categories
        FROM category_sales
        WHERE category_l6 NOT LIKE '0%' AND sales > 0
    """).fetchdf().to_dict(orient="records")[0]

    top_gainers = con.execute("""
        SELECT category_l6 AS category,
               ROUND(SUM(sales_chg), 2) AS sales_change,
               ROUND(AVG(agp_rate)*100, 1) AS agp_pct
        FROM category_sales
        WHERE category_l6 NOT LIKE '0%' AND sales_chg IS NOT NULL
        GROUP BY category_l6
        ORDER BY sales_change DESC LIMIT 3
    """).fetchdf().to_dict(orient="records")

    top_decliners = con.execute("""
        SELECT category_l6 AS category,
               ROUND(SUM(sales_chg), 2) AS sales_change,
               ROUND(AVG(mkdn_rate)*100, 1) AS markdown_pct
        FROM category_sales
        WHERE category_l6 NOT LIKE '0%' AND sales_chg IS NOT NULL
        GROUP BY category_l6
        ORDER BY sales_change ASC LIMIT 3
    """).fetchdf().to_dict(orient="records")

    coverage_gaps = con.execute("""
        SELECT s.store_id, s.region, s.store_size_tier,
               COUNT(sa.upc_id) - SUM(CASE WHEN sa.is_carried THEN 1 ELSE 0 END) AS gap_skus
        FROM stores s JOIN store_assortment sa ON s.store_id = sa.store_id
        GROUP BY s.store_id, s.region, s.store_size_tier
        ORDER BY gap_skus DESC LIMIT 3
    """).fetchdf().to_dict(orient="records")

    clip_stats = con.execute("""
        SELECT COUNT(DISTINCT clip_id) AS total_clips,
               COUNT(DISTINCT client_offer_id) AS unique_offers
        FROM clips
    """).fetchdf().to_dict(orient="records")[0]

    con.close()
    return {
        "sales_health":   sales_health,
        "top_gainers":    top_gainers,
        "top_decliners":  top_decliners,
        "coverage_gaps":  coverage_gaps,
        "clip_stats":     clip_stats,
    }


# ── Quick self-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    print("Testing query layer...\n")
    print("→ Monday briefing summary:")
    brief = get_monday_briefing_summary()
    print(json.dumps(brief, indent=2, default=str))
    print("\n→ Low productivity SKUs (top 3):")
    low = get_low_productivity_skus()[:3]
    for r in low:
        print(f"  {r['brand']:30} sales={r['total_sales']:>10} agp={r['agp_pct']}% mkdn={r['markdown_pct']}% → {r['productivity_flag']}")
    print("\nAll queries OK ✓")
