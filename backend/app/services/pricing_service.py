from datetime import timedelta
from math import inf

from app.services.demand_service import estimate_demand
from app.utils.helpers import utc_now


def _price_step(min_price: int, max_price: int) -> int:
    spread = max_price - min_price
    return max(1, spread // 25)


def optimize_price(sku: dict) -> dict:
    current_price = float(sku.get("price", sku.get("current_price", 0.0)))
    cost = float(sku["cost"])
    min_comp_price = float(sku.get("min_comp_price", current_price))
    avg_comp_price = float(sku.get("avg_comp_price", min_comp_price))
    demand_scale = str(sku.get("demand_scale", "medium"))
    sensitivity = str(sku.get("price_sensitivity", "medium"))
    festival_multiplier = 1.0

    min_price = max(1, round(current_price * 0.9))
    max_price = max(min_price, round(current_price * 1.1))
    step = _price_step(min_price, max_price)

    best = {"price": current_price, "profit": -inf, "demand": 0.0}
    curve = []

    for price in range(min_price, max_price + 1, step):
        demand = estimate_demand(
            price=price,
            demand_scale=demand_scale,
            price_sensitivity=sensitivity,
            avg_comp_price=avg_comp_price,
            min_comp_price=min_comp_price,
            festival_multiplier=festival_multiplier,
        )
        profit = (price - cost) * demand
        curve.append({"price": price, "profit": round(profit, 2)})
        if profit > best["profit"]:
            best = {"price": price, "profit": profit, "demand": demand}

    current_demand = estimate_demand(
        price=current_price,
        demand_scale=demand_scale,
        price_sensitivity=sensitivity,
        avg_comp_price=avg_comp_price,
        min_comp_price=min_comp_price,
        festival_multiplier=festival_multiplier,
    )
    current_profit = (current_price - cost) * current_demand

    range_padding = step * 2
    recommended_min = max(min_price, int(best["price"] - range_padding))
    recommended_max = min(max_price, int(best["price"] + range_padding))

    return {
        "currentPrice": current_price,
        "currentProfit": round(current_profit, 2),
        "optimalPrice": round(best["price"], 2),
        "optimalProfit": round(best["profit"], 2),
        "recommendedMin": recommended_min,
        "recommendedMax": recommended_max,
        "profitCurve": curve,
        "estimatedDemand": round(best["demand"], 2),
        "minCompPrice": round(min_comp_price, 2),
        "avgCompPrice": round(avg_comp_price, 2),
        "estimatedProfitChange": round(best["profit"] - current_profit, 2),
    }


def simulate_price_change(
    sku: dict,
    price: float,
    competitor_price: float | None,
    festival_boost: bool,
) -> dict:
    sensitivity = str(sku.get("price_sensitivity", "medium"))
    demand_scale = str(sku.get("demand_scale", "medium"))
    default_min_comp = float(sku.get("min_comp_price", sku.get("avg_comp_price", 0.0)))
    min_comp_price = float(competitor_price) if competitor_price is not None else default_min_comp
    avg_comp_price = float(sku.get("avg_comp_price", min_comp_price))

    festival_sensitivity = str(sku.get("festival_sensitivity", "medium")).lower()
    if festival_boost:
        festival_multiplier = 1.45 if festival_sensitivity == "high" else 1.25 if festival_sensitivity == "medium" else 1.1
    else:
        festival_multiplier = 1.0

    demand = estimate_demand(
        price=price,
        demand_scale=demand_scale,
        price_sensitivity=sensitivity,
        avg_comp_price=avg_comp_price,
        min_comp_price=min_comp_price,
        festival_multiplier=festival_multiplier,
    )

    expected_units = int(round(demand * 30))
    revenue = round(float(price) * demand * 30, 2)
    profit = round((float(price) - float(sku["cost"])) * demand * 30, 2)

    inventory = int(sku.get("inventory", 0))
    days_to_stockout = 999 if demand <= 0 else int(inventory / demand)

    if days_to_stockout >= 999:
        stockout_date = "No stockout risk"
    else:
        stockout_date = (utc_now() + timedelta(days=days_to_stockout)).strftime("%d %b %Y")

    return {
        "expectedUnits": expected_units,
        "demand": round(demand, 2),
        "revenue": revenue,
        "profit": profit,
        "stockoutDate": stockout_date,
    }
