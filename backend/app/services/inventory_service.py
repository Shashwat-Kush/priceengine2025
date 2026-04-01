from math import ceil


def inventory_metrics(sku: dict) -> dict:
    inventory = int(sku.get("inventory", 0))
    daily_demand = float(sku.get("daily_demand", 0))
    lead_time_days = int(sku.get("lead_time_days", 7))
    storage_cost_per_unit = float(sku.get("storage_cost_per_unit", 0))
    cost = float(sku.get("cost", 0))

    effective_demand = max(daily_demand, 0.1)
    days_until_stockout = int(inventory / effective_demand)
    reorder_point = daily_demand * lead_time_days * 1.2
    suggested_order_qty = max(0, int(ceil(reorder_point * 2 - inventory)))

    return {
        "daysUntilStockout": days_until_stockout,
        "reorderPoint": round(reorder_point),
        "suggestedOrderQty": suggested_order_qty,
        "storageCostImpact": round(suggested_order_qty * storage_cost_per_unit, 2),
        "orderCost": round(suggested_order_qty * cost, 2),
    }
