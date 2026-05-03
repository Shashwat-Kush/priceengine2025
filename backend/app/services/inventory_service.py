from math import ceil, sqrt


_SERVICE_LEVEL_Z = [
    (0.80, 0.84),
    (0.85, 1.04),
    (0.90, 1.28),
    (0.95, 1.65),
    (0.97, 1.88),
    (0.98, 2.05),
    (0.99, 2.33),
]


def _service_level_to_z(service_level: float) -> float:
    level = max(0.5, min(float(service_level), 0.995))
    for (l1, z1), (l2, z2) in zip(_SERVICE_LEVEL_Z, _SERVICE_LEVEL_Z[1:]):
        if l1 <= level <= l2:
            if l2 == l1:
                return z1
            ratio = (level - l1) / (l2 - l1)
            return z1 + ratio * (z2 - z1)
    return _SERVICE_LEVEL_Z[-1][1]


def inventory_metrics(sku: dict) -> dict:
    inventory = int(sku.get("inventory", 0))
    demand_mean = float(sku.get("demand_mean", sku.get("demand", 0)))
    demand_variance = float(sku.get("demand_variance", 0))
    lead_time_days = int(sku.get("lead_time_days", 0))
    storage_cost_per_unit = float(sku.get("storage_cost_per_unit", 0))
    cost = float(sku.get("cost", 0))
    service_level = float(sku.get("service_level", 0.95))

    effective_demand = max(demand_mean, 0.1)
    days_until_stockout = int(inventory / effective_demand) if effective_demand > 0 else 999

    sigma = sqrt(max(demand_variance, 0.0))
    z_value = _service_level_to_z(service_level)
    safety_stock = z_value * sigma * sqrt(max(lead_time_days, 0))
    reorder_point = (demand_mean * lead_time_days) + safety_stock

    suggested_order_qty = max(0, int(ceil(reorder_point - inventory)))
    stockout_risk = max(0.0, min(1.0, 1 - service_level))

    return {
        "daysUntilStockout": days_until_stockout,
        "reorderPoint": round(reorder_point, 2),
        "safetyStock": round(safety_stock, 2),
        "suggestedOrderQty": suggested_order_qty,
        "storageCostImpact": round(safety_stock * storage_cost_per_unit, 2),
        "orderCost": round(suggested_order_qty * cost, 2),
        "serviceLevel": round(service_level, 3),
        "stockoutRisk": round(stockout_risk, 3),
    }


def group_reorders(rows: list[dict]) -> list[dict]:
    """Group replenishment suggestions into near-term windows for logistics savings."""
    groups: dict[int, dict] = {}

    for row in rows:
        listing = row.get("listing") or {}
        computed = row.get("computed") or {}
        qty = int(row.get("suggestedOrderQty") or 0)
        if qty <= 0:
            continue

        days_to_stockout = int(computed.get("daysToStockout", 0))
        lead_time = int(listing.get("leadTimeDays", 0))
        reorder_in = max(0, days_to_stockout - lead_time)

        window_start = (reorder_in // 3) * 3
        window_end = window_start + 3

        key = window_start
        entry = groups.setdefault(
            key,
            {
                "windowStartDays": window_start,
                "windowEndDays": window_end,
                "skus": [],
                "totalOrderQty": 0,
                "totalOrderCost": 0.0,
                "separateLogisticsCost": 0.0,
                "groupedLogisticsCost": 0.0,
            },
        )

        logistics_cost = float(listing.get("logisticsCostPerOrder", 0.0))
        entry["skus"].append(
            {
                "skuId": row.get("sku", {}).get("id"),
                "skuName": row.get("sku", {}).get("name"),
                "listingId": listing.get("id"),
                "marketplace": listing.get("marketplace"),
                "orderQty": qty,
                "orderCost": float(row.get("orderCost", 0.0)),
                "logisticsCost": logistics_cost,
            }
        )
        entry["totalOrderQty"] += qty
        entry["totalOrderCost"] += float(row.get("orderCost", 0.0))
        entry["separateLogisticsCost"] += logistics_cost
        entry["groupedLogisticsCost"] = max(entry["groupedLogisticsCost"], logistics_cost)

    grouped = []
    for entry in groups.values():
        entry["totalOrderCost"] = round(entry["totalOrderCost"], 2)
        entry["separateLogisticsCost"] = round(entry["separateLogisticsCost"], 2)
        entry["groupedLogisticsCost"] = round(entry["groupedLogisticsCost"], 2)
        entry["estimatedSavings"] = round(
            entry["separateLogisticsCost"] - entry["groupedLogisticsCost"],
            2,
        )
        grouped.append(entry)

    return sorted(grouped, key=lambda row: row["windowStartDays"])
