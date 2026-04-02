from datetime import date, datetime, timezone
from typing import Any, Dict, List


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_sensitivity(value: str) -> str:
    normalized = (value or "medium").strip().lower()
    if normalized not in {"high", "medium", "low"}:
        return "medium"
    return normalized


def to_title_sensitivity(value: str) -> str:
    return normalize_sensitivity(value).capitalize()


def compute_margin_pct(current_price: float, cost: float) -> float:
    if current_price <= 0:
        return 0.0
    return round(((current_price - cost) / current_price) * 100, 1)


def compute_inventory_status(inventory: int, daily_demand: float) -> str:
    if inventory <= 0:
        return "Critical"
    demand = max(daily_demand, 0.1)
    days_left = inventory / demand
    if days_left <= 2:
        return "Critical"
    if days_left <= 7:
        return "Low"
    if days_left >= 45:
        return "Overstock"
    return "Healthy"


def compute_competitor_risk(current_price: float, competitor_price: float, sensitivity: str) -> str:
    if competitor_price <= 0:
        return "Low"
    sensitivity_norm = normalize_sensitivity(sensitivity)

    if current_price > competitor_price * 1.03:
        return "High"
    if current_price > competitor_price:
        return "Medium"
    if sensitivity_norm == "high" and current_price >= competitor_price * 0.98:
        return "Medium"
    return "Low"


def days_until(date_str: str) -> int:
    target = date.fromisoformat(date_str)
    today = date.today()
    return max((target - today).days, 0)


def default_seed_payload(org_id: str) -> Dict[str, List[Dict[str, Any]]]:
    now = utc_now()
    seed_suffix = (org_id or "org").replace("org-", "")[:8] or "org"

    sku_rows = [
        ("sku-001", "boAt Airdopes 141", "Electronics", "medium", "high", "high"),
        ("sku-002", "Prestige Iron 1000W", "Appliances", "low", "medium", "medium"),
        ("sku-003", "Mamaearth Vitamin C Serum", "Skincare", "high", "high", "high"),
        ("sku-004", "Bajaj Mixer 500W", "Appliances", "low", "low", "high"),
        ("sku-005", "Lakme Compact Powder", "Beauty", "high", "high", "medium"),
    ]

    skus: List[Dict[str, Any]] = []
    listings: List[Dict[str, Any]] = []
    competitors: List[Dict[str, Any]] = []

    for idx, row in enumerate(sku_rows, start=1):
        base_sku_id, name, category, demand_scale, sensitivity, fest_sensitivity = row
        sku_id = f"{base_sku_id}-{seed_suffix}"
        skus.append(
            {
                "_id": sku_id,
                "org_id": org_id,
                "name": name,
                "category": category,
                "demand_scale": demand_scale,
                "price_sensitivity": normalize_sensitivity(sensitivity),
                "festival_sensitivity": normalize_sensitivity(fest_sensitivity),
                "created_at": now,
                "updated_at": now,
            }
        )

        # Two listings per SKU for phase-1 marketplace separation.
        amazon_listing_id = f"lst-{sku_id}-amazon"
        flipkart_listing_id = f"lst-{sku_id}-flipkart"

        base_price = 300 + idx * 210
        base_cost = round(base_price * 0.58, 2)
        base_inventory = 25 + idx * 9

        listings.append(
            {
                "_id": amazon_listing_id,
                "sku_id": sku_id,
                "org_id": org_id,
                "marketplace": "Amazon",
                "price": float(base_price),
                "cost": float(base_cost),
                "inventory": int(base_inventory),
                "lead_time_days": 7,
                "storage_cost_per_unit": 10.0,
                "created_at": now,
                "updated_at": now,
            }
        )
        listings.append(
            {
                "_id": flipkart_listing_id,
                "sku_id": sku_id,
                "org_id": org_id,
                "marketplace": "Flipkart",
                "price": float(round(base_price * 0.97, 2)),
                "cost": float(round(base_cost * 0.99, 2)),
                "inventory": int(max(6, base_inventory - 8)),
                "lead_time_days": 8,
                "storage_cost_per_unit": 9.0,
                "created_at": now,
                "updated_at": now,
            }
        )

        for listing_id, list_price in [
            (amazon_listing_id, float(base_price)),
            (flipkart_listing_id, float(round(base_price * 0.97, 2))),
        ]:
            competitor_count = 3 if listing_id.endswith("amazon") else 2
            for c_idx in range(competitor_count):
                shift = (c_idx - 1) * 0.03
                competitors.append(
                    {
                        "_id": f"cmp-{listing_id}-{c_idx + 1}",
                        "listing_id": listing_id,
                        "org_id": org_id,
                        "name": f"Competitor {c_idx + 1}",
                        "price": float(round(list_price * (1.0 + shift), 2)),
                        "rating": float(round(3.8 + (c_idx * 0.4), 1)),
                        "shipping_days": int(2 + c_idx),
                        "last_updated": now,
                    }
                )

    festivals = [
        {
            "_id": f"festival-diwali-{seed_suffix}",
            "org_id": org_id,
            "name": "Diwali",
            "date": "2026-10-20",
            "boost": 1.4,
            "platform": ["Amazon", "Flipkart"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": f"festival-big-billion-days-{seed_suffix}",
            "org_id": org_id,
            "name": "Big Billion Days",
            "date": "2026-04-14",
            "boost": 1.6,
            "platform": ["Flipkart"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": f"festival-independence-day-sale-{seed_suffix}",
            "org_id": org_id,
            "name": "Independence Day Sale",
            "date": "2026-08-15",
            "boost": 1.3,
            "platform": ["Amazon", "Flipkart"],
            "created_at": now,
            "updated_at": now,
        },
    ]

    return {
        "skus": skus,
        "listings": listings,
        "competitors": competitors,
        "festivals": festivals,
    }
