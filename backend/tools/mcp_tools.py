"""
MCP-style action tools for the ACI platform.

These tools are callable by agents and can be exposed as MCP tools
for front-end action buttons.

Functions:
  get_category_gaps(category_id)              — raw gap data from DuckDB
  estimate_revenue_loss(category, gap_pct, avg_basket) — weekly + annual $$ impact
  advance_to_pilot(supplier_id, store_cluster, sku_count) — mock pilot creation
  flag_sku_for_removal(upc_id, store_id, reason) — removal flag mock
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import duckdb

from db.queries import get_category_gap_heatmap, get_assortment_gaps_by_store


# ── Tool 1: Raw category gap data ───────────────────────────────────────────

def get_category_gaps(category_id: Optional[str] = None) -> dict:
    """
    Return category gap data from DuckDB.

    Args:
        category_id: Optional category name filter (case-insensitive partial match).
                     If None, returns the full heatmap.

    Returns:
        dict with keys:
          gaps      — list of gap rows
          category  — filter applied (or "all")
          count     — number of rows returned
    """
    heatmap = get_category_gap_heatmap()

    if category_id:
        filtered = [
            row for row in heatmap
            if category_id.lower() in str(row.get("category_nm", "")).lower()
        ]
    else:
        filtered = heatmap

    return {
        "gaps": filtered,
        "category": category_id or "all",
        "count": len(filtered),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Tool 2: Revenue loss estimator ──────────────────────────────────────────

def estimate_revenue_loss(
    category: str,
    gap_pct: float,
    avg_basket: float = 45.0,
    weekly_traffic: int = 2500,
) -> dict:
    """
    Estimate revenue opportunity from closing a category assortment gap.

    Args:
        category:       Category name (informational only)
        gap_pct:        Assortment gap as a decimal (e.g. 0.35 = 35% of network SKUs missing)
        avg_basket:     Average transaction basket value in $ (default: $45)
        weekly_traffic: Estimated weekly store traffic (default: 2,500 trips)

    Returns:
        dict with weekly_loss_usd, annual_loss_usd, methodology, assumptions
    """
    if not (0.0 <= gap_pct <= 1.0):
        return {"error": "gap_pct must be between 0.0 and 1.0"}

    # Conservative model: 2% of shoppers would buy missing items per 10% gap
    conversion_rate = gap_pct * 0.20          # shoppers influenced by gap
    weekly_lost_trips = weekly_traffic * conversion_rate
    weekly_loss = weekly_lost_trips * avg_basket * 0.15  # 15% incremental spend

    annual_loss = weekly_loss * 52

    return {
        "category": category,
        "gap_pct": round(gap_pct * 100, 1),
        "weekly_loss_usd": round(weekly_loss, 2),
        "annual_loss_usd": round(annual_loss, 2),
        "methodology": "Gap × conversion rate × average basket × incremental spend rate",
        "assumptions": {
            "avg_basket_usd": avg_basket,
            "weekly_traffic": weekly_traffic,
            "conversion_rate_pct": round(conversion_rate * 100, 1),
            "incremental_spend_rate": "15%",
        },
        "confidence": "medium" if gap_pct < 0.5 else "low",
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Tool 3: Advance to pilot ─────────────────────────────────────────────────

def advance_to_pilot(
    supplier_id: str,
    store_cluster: str,
    sku_count: int,
    pilot_weeks: int = 8,
) -> dict:
    """
    Mock: Create a new assortment pilot with the given supplier.

    In production this would POST to the Category Management system.
    For the hackathon, returns a realistic-looking pilot record.

    Args:
        supplier_id:    Supplier identifier (e.g. "SUP-1234")
        store_cluster:  Store cluster name (e.g. "Southern CA Urban" or "36,41,58")
        sku_count:      Number of SKUs to pilot
        pilot_weeks:    Pilot duration in weeks (default: 8)

    Returns:
        dict with pilot_id, status, timeline, and next actions
    """
    if sku_count < 1 or sku_count > 50:
        return {"error": "sku_count must be between 1 and 50"}

    pilot_id = f"PIL-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    return {
        "pilot_id": pilot_id,
        "status": "created",
        "supplier_id": supplier_id,
        "store_cluster": store_cluster,
        "sku_count": sku_count,
        "pilot_weeks": pilot_weeks,
        "timeline": {
            "created_at": now.isoformat(),
            "review_by": f"Week {pilot_weeks // 2} checkpoint",
            "decision_date": f"{pilot_weeks} weeks from creation",
        },
        "next_actions": [
            f"Notify supplier {supplier_id} to prepare {sku_count} SKUs for reset",
            "Schedule planogram revision with store ops",
            f"Set {pilot_weeks // 2}-week check-in with category manager",
            "Configure velocity tracking alert in CAO system",
        ],
        "success_criteria": {
            "min_velocity_units_per_week": 3,
            "min_margin_pct": 28,
            "shopper_repeat_rate_pct": 25,
        },
        "created_by": "ACI Platform",
        "division": "Division 20 — Southern",
    }


# ── Tool 4: Flag SKU for removal ─────────────────────────────────────────────

def flag_sku_for_removal(
    upc_id: str,
    store_id: int,
    reason: str,
    replacement_upc: Optional[str] = None,
) -> dict:
    """
    Mock: Flag a SKU for removal from a store's assortment.

    In production this would write to the Category Management queue.
    For the hackathon, returns a realistic-looking removal ticket.

    Args:
        upc_id:          UPC identifier (e.g. "0001234567890")
        store_id:        Store number (e.g. 36)
        reason:          Removal reason — one of:
                         "low_velocity", "margin_drain", "planogram_reset",
                         "supplier_discontinue", "better_alternative"
        replacement_upc: Optional UPC of the replacement SKU

    Returns:
        dict with ticket_id, status, and workflow steps
    """
    valid_reasons = {
        "low_velocity", "margin_drain", "planogram_reset",
        "supplier_discontinue", "better_alternative",
    }
    if reason not in valid_reasons:
        return {
            "error": f"Invalid reason. Must be one of: {sorted(valid_reasons)}"
        }

    ticket_id = f"REM-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    result = {
        "ticket_id": ticket_id,
        "status": "pending_review",
        "upc_id": upc_id,
        "store_id": store_id,
        "reason": reason,
        "workflow": [
            {"step": 1, "action": "Category Manager review", "due": "3 business days"},
            {"step": 2, "action": "Store director notification", "due": "5 business days"},
            {"step": 3, "action": "Planogram update", "due": "Next reset cycle"},
            {"step": 4, "action": "Inventory clearance", "due": "4 weeks"},
        ],
        "created_at": now.isoformat(),
        "created_by": "ACI Platform",
    }

    if replacement_upc:
        result["replacement_upc"] = replacement_upc
        result["workflow"].insert(2, {
            "step": "2b",
            "action": f"Verify replacement SKU {replacement_upc} is on order",
            "due": "Before planogram update",
        })

    return result


# ── MCP tool registry ─────────────────────────────────────────────────────────

TOOLS = {
    "get_category_gaps": get_category_gaps,
    "estimate_revenue_loss": estimate_revenue_loss,
    "advance_to_pilot": advance_to_pilot,
    "flag_sku_for_removal": flag_sku_for_removal,
}

TOOL_SCHEMAS = [
    {
        "name": "get_category_gaps",
        "description": "Retrieve raw category gap data from DuckDB. Optionally filter by category name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category_id": {
                    "type": "string",
                    "description": "Partial category name to filter (optional). E.g. 'frozen', 'dairy'."
                }
            },
        },
    },
    {
        "name": "estimate_revenue_loss",
        "description": "Estimate weekly and annual revenue opportunity from closing an assortment gap.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category name (informational)"},
                "gap_pct": {"type": "number", "description": "Assortment gap as decimal (e.g. 0.35 = 35%)"},
                "avg_basket": {"type": "number", "description": "Average basket value in USD (default: 45)"},
                "weekly_traffic": {"type": "integer", "description": "Estimated weekly store trips (default: 2500)"},
            },
            "required": ["category", "gap_pct"],
        },
    },
    {
        "name": "advance_to_pilot",
        "description": "Create a new SKU pilot with a supplier for a store cluster. Returns a pilot ID and next steps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "supplier_id": {"type": "string", "description": "Supplier identifier"},
                "store_cluster": {"type": "string", "description": "Store cluster name or comma-separated store IDs"},
                "sku_count": {"type": "integer", "description": "Number of SKUs to pilot (1-50)"},
                "pilot_weeks": {"type": "integer", "description": "Pilot duration in weeks (default: 8)"},
            },
            "required": ["supplier_id", "store_cluster", "sku_count"],
        },
    },
    {
        "name": "flag_sku_for_removal",
        "description": "Flag a SKU for removal from a store's assortment. Creates a review ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "upc_id": {"type": "string", "description": "UPC identifier"},
                "store_id": {"type": "integer", "description": "Store number"},
                "reason": {
                    "type": "string",
                    "enum": ["low_velocity", "margin_drain", "planogram_reset",
                             "supplier_discontinue", "better_alternative"],
                    "description": "Reason for removal",
                },
                "replacement_upc": {"type": "string", "description": "Optional replacement SKU UPC"},
            },
            "required": ["upc_id", "store_id", "reason"],
        },
    },
]


def call_tool(tool_name: str, **kwargs) -> dict:
    """Dispatch a tool call by name."""
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}. Available: {list(TOOLS)}"}
    return TOOLS[tool_name](**kwargs)


if __name__ == "__main__":
    # Quick smoke-test
    print("=== get_category_gaps (frozen) ===")
    print(json.dumps(get_category_gaps("frozen"), indent=2, default=str))

    print("\n=== estimate_revenue_loss ===")
    print(json.dumps(estimate_revenue_loss("Frozen Meals", 0.35), indent=2))

    print("\n=== advance_to_pilot ===")
    print(json.dumps(advance_to_pilot("SUP-9921", "Southern CA Urban", 8), indent=2))

    print("\n=== flag_sku_for_removal ===")
    print(json.dumps(flag_sku_for_removal("7874203001", 36, "low_velocity"), indent=2))
