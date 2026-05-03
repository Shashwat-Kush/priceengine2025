from datetime import date, datetime, timedelta
from math import inf

from app.services.demand_service import adjust_demand_from_base
from app.services.forecast_service import forecast_base_demand
from app.services.inventory_service import inventory_metrics
from app.utils.helpers import compute_competitor_risk, compute_margin_pct, normalize_sensitivity, utc_now


def _price_step(min_price: int, max_price: int) -> int:
    spread = max_price - min_price
    return max(1, spread // 25)


def _price_band(current_price: float, sensitivity: str) -> tuple[int, int]:
    normalized = normalize_sensitivity(sensitivity)
    band = 0.08 if normalized == "low" else 0.18 if normalized == "high" else 0.10
    min_price = max(1, round(current_price * (1 - band)))
    max_price = max(min_price, round(current_price * (1 + band)))
    return min_price, max_price


def _service_level_candidates(base_level: float) -> list[float]:
    base = max(0.5, min(float(base_level), 0.99))
    candidates = {round(base, 2)}
    for offset in (-0.07, -0.04, -0.02, 0.02, 0.04):
        candidates.add(round(max(0.6, min(base + offset, 0.99)), 2))
    return sorted(candidates)


def _lifecycle_multiplier(launch_date: str | None) -> float:
    if not launch_date:
        return 1.0
    try:
        parsed = date.fromisoformat(str(launch_date))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(str(launch_date)).date()
        except ValueError:
            return 1.0

    days = (date.today() - parsed).days
    if days < 30:
        return 1.05
    if days < 90:
        return 1.0
    if days < 180:
        return 0.97
    if days < 365:
        return 0.93
    return 0.9


def optimize_price(sku: dict) -> dict:
    current_price = float(sku.get("price", sku.get("current_price", 0.0)))
    cost = float(sku["cost"])
    min_comp_price = float(sku.get("min_comp_price", current_price))
    avg_comp_price = float(sku.get("avg_comp_price", min_comp_price))
    sensitivity = str(sku.get("price_sensitivity", "medium"))
    festival_multiplier = 1.0
    service_level = float(sku.get("service_level", 0.95))
    storage_cost_per_unit = float(sku.get("storage_cost_per_unit", 0.0))
    logistics_cost_per_order = float(sku.get("logistics_cost_per_order", 150.0))
    min_margin_pct = float(sku.get("min_margin_pct", 5.0))

    min_price, max_price = _price_band(current_price, sensitivity)
    min_margin_price = cost / max(0.01, (1 - (min_margin_pct / 100)))
    min_price = max(min_price, round(min_margin_price))
    lifecycle_multiplier = _lifecycle_multiplier(sku.get("launch_date") or sku.get("launchDate"))
    max_price = max(min_price, round(max_price * lifecycle_multiplier))
    step = _price_step(min_price, max_price)

    forecast = forecast_base_demand(
        sku=sku,
        listing=sku,
        price=current_price,
        competitor_price=min_comp_price,
    )
    base_mean = float(forecast["mean"])
    base_variance = float(forecast["variance"])

    best = {
        "price": current_price,
        "profit": -inf,
        "demand": 0.0,
        "serviceLevel": service_level,
        "safetyStock": 0.0,
        "reorderPoint": 0.0,
        "stockoutRisk": 0.0,
        "holdingCost": 0.0,
        "logisticsCost": 0.0,
        "stockoutPenalty": 0.0,
        "demandVariance": 0.0,
    }
    curve = []

    service_levels = _service_level_candidates(service_level)

    for price in range(min_price, max_price + 1, step):
        best_profit_for_price = -inf
        best_snapshot = None
        for sl in service_levels:
            demand, demand_variance = adjust_demand_from_base(
                base_mean=base_mean,
                base_variance=base_variance,
                price=price,
                price_sensitivity=sensitivity,
                avg_comp_price=avg_comp_price,
                min_comp_price=min_comp_price,
                festival_multiplier=festival_multiplier,
            )
            metrics = inventory_metrics(
                {
                    "inventory": int(sku.get("inventory", 0)),
                    "demand_mean": demand,
                    "demand_variance": demand_variance,
                    "lead_time_days": int(sku.get("lead_time_days", 0)),
                    "storage_cost_per_unit": storage_cost_per_unit,
                    "cost": cost,
                    "service_level": sl,
                }
            )

            gross_profit = (price - cost) * demand
            holding_cost = float(metrics["safetyStock"]) * storage_cost_per_unit
            logistics_cost = logistics_cost_per_order if demand > 0 else 0.0
            stockout_penalty = gross_profit * float(metrics["stockoutRisk"])
            net_profit = gross_profit - holding_cost - logistics_cost - stockout_penalty

            if net_profit > best_profit_for_price:
                best_profit_for_price = net_profit
                best_snapshot = {
                    "demand": demand,
                    "demandVariance": demand_variance,
                    "serviceLevel": sl,
                    "safetyStock": metrics["safetyStock"],
                    "reorderPoint": metrics["reorderPoint"],
                    "stockoutRisk": metrics["stockoutRisk"],
                    "holdingCost": holding_cost,
                    "logisticsCost": logistics_cost,
                    "stockoutPenalty": stockout_penalty,
                }

        if best_snapshot is None:
            continue

        curve.append({"price": price, "profit": round(best_profit_for_price, 2)})
        if best_profit_for_price > best["profit"]:
            best = {
                "price": price,
                "profit": best_profit_for_price,
                **best_snapshot,
            }

    current_demand, current_variance = adjust_demand_from_base(
        base_mean=base_mean,
        base_variance=base_variance,
        price=current_price,
        price_sensitivity=sensitivity,
        avg_comp_price=avg_comp_price,
        min_comp_price=min_comp_price,
        festival_multiplier=festival_multiplier,
    )
    current_metrics = inventory_metrics(
        {
            "inventory": int(sku.get("inventory", 0)),
            "demand_mean": current_demand,
            "demand_variance": current_variance,
            "lead_time_days": int(sku.get("lead_time_days", 0)),
            "storage_cost_per_unit": storage_cost_per_unit,
            "cost": cost,
            "service_level": service_level,
        }
    )
    current_gross_profit = (current_price - cost) * current_demand
    current_holding_cost = float(current_metrics["safetyStock"]) * storage_cost_per_unit
    current_logistics_cost = logistics_cost_per_order if current_demand > 0 else 0.0
    current_stockout_penalty = current_gross_profit * float(current_metrics["stockoutRisk"])
    current_profit = current_gross_profit - current_holding_cost - current_logistics_cost - current_stockout_penalty

    range_padding = step * 2
    recommended_min = max(min_price, int(best["price"] - range_padding))
    recommended_max = min(max_price, int(best["price"] + range_padding))

    competitor_gap = round(current_price - min_comp_price, 2)

    return {
        "currentPrice": current_price,
        "currentProfit": round(current_profit, 2),
        "optimalPrice": round(best["price"], 2),
        "optimalProfit": round(best["profit"], 2),
        "recommendedMin": recommended_min,
        "recommendedMax": recommended_max,
        "profitCurve": curve,
        "estimatedDemand": round(best["demand"], 2),
        "demandVariance": round(best["demandVariance"], 2),
        "minCompPrice": round(min_comp_price, 2),
        "avgCompPrice": round(avg_comp_price, 2),
        "estimatedProfitChange": round(best["profit"] - current_profit, 2),
        "impliedMarginPct": compute_margin_pct(best["price"], cost),
        "serviceLevel": round(best["serviceLevel"], 3),
        "safetyStock": round(best["safetyStock"], 2),
        "reorderPoint": round(best["reorderPoint"], 2),
        "stockoutRisk": round(best["stockoutRisk"], 3),
        "holdingCost": round(best["holdingCost"], 2),
        "logisticsCost": round(best["logisticsCost"], 2),
        "stockoutPenalty": round(best["stockoutPenalty"], 2),
        "competitorGap": competitor_gap,
        "competitorRisk": compute_competitor_risk(current_price, min_comp_price, sensitivity),
        "festivalMultiplier": festival_multiplier,
        "lifecycleMultiplier": lifecycle_multiplier,
        "forecastSource": forecast["source"],
    }


def simulate_price_change(
    sku: dict,
    price: float,
    competitor_price: float | None,
    festival_boost: bool,
    service_level: float | None = None,
) -> dict:
    sensitivity = str(sku.get("price_sensitivity", "medium"))
    default_min_comp = float(sku.get("min_comp_price", sku.get("avg_comp_price", 0.0)))
    min_comp_price = float(competitor_price) if competitor_price is not None else default_min_comp
    avg_comp_price = float(sku.get("avg_comp_price", min_comp_price))

    storage_cost_per_unit = float(sku.get("storage_cost_per_unit", 0.0))
    logistics_cost_per_order = float(sku.get("logistics_cost_per_order", 150.0))
    chosen_service_level = float(service_level) if service_level is not None else float(sku.get("service_level", 0.95))

    festival_sensitivity = str(sku.get("festival_sensitivity", "medium")).lower()
    if festival_boost:
        festival_multiplier = 1.45 if festival_sensitivity == "high" else 1.25 if festival_sensitivity == "medium" else 1.1
    else:
        festival_multiplier = 1.0

    forecast = forecast_base_demand(
        sku=sku,
        listing=sku,
        price=price,
        competitor_price=min_comp_price,
    )
    base_mean = float(forecast["mean"])
    base_variance = float(forecast["variance"])
    demand, demand_variance = adjust_demand_from_base(
        base_mean=base_mean,
        base_variance=base_variance,
        price=price,
        price_sensitivity=sensitivity,
        avg_comp_price=avg_comp_price,
        min_comp_price=min_comp_price,
        festival_multiplier=festival_multiplier,
    )

    expected_units = int(round(demand * 30))
    revenue = round(float(price) * demand * 30, 2)
    gross_profit = (float(price) - float(sku["cost"])) * demand * 30

    metrics = inventory_metrics(
        {
            "inventory": int(sku.get("inventory", 0)),
            "demand_mean": demand,
            "demand_variance": demand_variance,
            "lead_time_days": int(sku.get("lead_time_days", 0)),
            "storage_cost_per_unit": storage_cost_per_unit,
            "cost": float(sku["cost"]),
            "service_level": chosen_service_level,
        }
    )

    holding_cost = float(metrics["safetyStock"]) * storage_cost_per_unit
    logistics_cost = logistics_cost_per_order if demand > 0 else 0.0
    stockout_penalty = gross_profit * float(metrics["stockoutRisk"])
    net_profit = gross_profit - holding_cost - logistics_cost - stockout_penalty

    inventory = int(sku.get("inventory", 0))
    days_to_stockout = metrics["daysUntilStockout"]

    if days_to_stockout >= 999:
        stockout_date = "No stockout risk"
    else:
        stockout_date = (utc_now() + timedelta(days=days_to_stockout)).strftime("%d %b %Y")

    return {
        "expectedUnits": expected_units,
        "demand": round(demand, 2),
        "revenue": revenue,
        "profit": round(net_profit, 2),
        "stockoutDate": stockout_date,
        "serviceLevel": round(chosen_service_level, 3),
        "safetyStock": metrics["safetyStock"],
        "reorderPoint": metrics["reorderPoint"],
        "stockoutRisk": metrics["stockoutRisk"],
        "holdingCost": round(holding_cost, 2),
        "logisticsCost": round(logistics_cost, 2),
        "stockoutPenalty": round(stockout_penalty, 2),
        "forecastSource": forecast["source"],
    }
