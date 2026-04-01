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


def default_seed_skus() -> List[Dict[str, Any]]:
    now = utc_now()
    seed_rows = [
        ("sku-001", "boAt Airdopes 141", "Electronics", "Amazon", 1299, 720, 1199, 42, 6, "high", 7, 12, "high", "high"),
        ("sku-002", "Prestige Iron 1000W", "Appliances", "Flipkart", 849, 490, 820, 18, 4, "medium", 10, 18, "medium", "medium"),
        ("sku-003", "Mamaearth Vitamin C Serum", "Skincare", "Meesho", 349, 130, 299, 210, 22, "high", 5, 4, "high", "medium"),
        ("sku-004", "Bajaj Mixer 500W", "Appliances", "Amazon", 2199, 1380, 2250, 55, 3, "low", 14, 35, "high", "high"),
        ("sku-005", "Lakme Compact Powder", "Beauty", "Flipkart", 189, 78, 175, 8, 14, "high", 4, 3, "medium", "medium"),
        ("sku-006", "Samsung 64GB Pen Drive", "Electronics", "Amazon", 599, 310, 579, 130, 9, "medium", 8, 6, "medium", "high"),
        ("sku-007", "Haldi Kumkum Gift Set", "Gifting", "Meesho", 249, 92, 239, 340, 18, "medium", 3, 2, "high", "high"),
        ("sku-008", "Philips Hair Dryer 1400W", "Personal Care", "Amazon", 1599, 950, 1650, 27, 2, "low", 12, 22, "medium", "high"),
        ("sku-009", "Dove Body Wash 500ml", "Personal Care", "Flipkart", 279, 115, 259, 15, 20, "high", 5, 4, "low", "medium"),
        ("sku-010", "Ceramic Mug Set of 6", "Home & Kitchen", "Meesho", 399, 185, 380, 76, 7, "medium", 6, 8, "medium", "medium"),
        ("sku-011", "Fastrack Analog Watch", "Fashion", "Amazon", 1499, 820, 1399, 34, 4, "high", 10, 15, "high", "high"),
        ("sku-012", "Saffola Honey 500g", "Food & Grocery", "Flipkart", 219, 110, 210, 95, 12, "medium", 4, 3, "low", "medium"),
        ("sku-013", "Noise ColorFit Pro 4", "Electronics", "Amazon", 2999, 1650, 2799, 22, 5, "high", 8, 20, "high", "high"),
        ("sku-014", "Ethnic Kurti Printed", "Fashion", "Meesho", 499, 180, 479, 145, 16, "high", 3, 5, "high", "high"),
        ("sku-015", "Nescafe Classic 200g", "Food & Grocery", "Flipkart", 349, 195, 340, 60, 8, "low", 5, 4, "low", "medium"),
    ]

    docs: List[Dict[str, Any]] = []
    for row in seed_rows:
        (
            sku_id,
            name,
            category,
            marketplace,
            current_price,
            cost,
            competitor_price,
            inventory,
            daily_demand,
            sensitivity,
            lead_time,
            storage_cost,
            festival_boost,
            marketplace_strength,
        ) = row

        docs.append(
            {
                "_id": sku_id,
                "name": name,
                "category": category,
                "marketplace": marketplace,
                "current_price": float(current_price),
                "cost": float(cost),
                "competitor_price": float(competitor_price),
                "inventory": int(inventory),
                "daily_demand": float(daily_demand),
                "price_sensitivity": normalize_sensitivity(sensitivity),
                "lead_time_days": int(lead_time),
                "storage_cost_per_unit": float(storage_cost),
                "base_demand": float(max(daily_demand + 2, daily_demand * 1.2)),
                "festival_boost_potential": normalize_sensitivity(festival_boost),
                "marketplace_strength": normalize_sensitivity(marketplace_strength),
                "created_at": now,
                "updated_at": now,
            }
        )
    return docs
