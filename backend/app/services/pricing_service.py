from datetime import timedelta
from math import inf

from app.services.demand_service import estimate_demand
from app.utils.helpers import utc_now


def _price_step(min_price: int, max_price: int) -> int:
    spread = max_price - min_price
    return max(1, spread // 25)


def optimize_price(sku: dict) -> dict:
    current_price = float(sku["current_price"])
    cost = float(sku["cost"])
    competitor_price = float(sku["competitor_price"])
    base_demand = float(sku.get("base_demand", sku.get("daily_demand", 1)))
    sensitivity = str(sku.get("price_sensitivity", "medium"))

    min_price = max(1, round(current_price * 0.9))
    max_price = max(min_price, round(current_price * 1.1))
    step = _price_step(min_price, max_price)

    best = {"price": current_price, "profit": -inf, "demand": 0.0}
    curve = []

    for price in range(min_price, max_price + 1, step):
        demand = estimate_demand(price, competitor_price, base_demand, sensitivity)
        profit = (price - cost) * demand
        curve.append({"price": price, "profit": round(profit, 2)})
        if profit > best["profit"]:
            best = {"price": price, "profit": profit, "demand": demand}

    current_demand = estimate_demand(
        current_price,
        competitor_price,
        base_demand,
        sensitivity,
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
        "estimatedProfitChange": round(best["profit"] - current_profit, 2),
    }


def simulate_price_change(
    sku: dict,
    price: float,
    competitor_price: float,
    festival_boost: bool,
) -> dict:
    sensitivity = str(sku.get("price_sensitivity", "medium"))
    base_demand = float(sku.get("base_demand", sku.get("daily_demand", 1)))
    demand = estimate_demand(price, competitor_price, base_demand, sensitivity)

    if festival_boost:
        boost_band = str(sku.get("festival_boost_potential", "medium")).lower()
        boost = 1.6 if boost_band == "high" else 1.3 if boost_band == "medium" else 1.1
        demand = demand * boost

    expected_units = int(round(demand * 30))
    revenue = round(float(price) * expected_units, 2)
    profit = round((float(price) - float(sku["cost"])) * expected_units, 2)

    inventory = int(sku.get("inventory", 0))
    days_to_stockout = 999 if demand <= 0 else int(inventory / demand)

    if days_to_stockout >= 999:
        stockout_date = "No stockout risk"
    else:
        stockout_date = (utc_now() + timedelta(days=days_to_stockout)).strftime("%d %b %Y")

    return {
        "expectedUnits": expected_units,
        "revenue": revenue,
        "profit": profit,
        "stockoutDate": stockout_date,
    }
