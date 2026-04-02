from math import ceil


def inventory_metrics(sku: dict) -> dict:
    inventory = int(sku.get("inventory", 0))
    demand = float(sku.get("demand", 0))
    lead_time_days = int(sku.get("lead_time_days", 0))
    storage_cost_per_unit = float(sku.get("storage_cost_per_unit", 0))
    cost = float(sku.get("cost", 0))

    effective_demand = max(demand, 0.1)
    days_until_stockout = int(inventory / effective_demand)
    safety_buffer = max(2.0, demand * 2)
    reorder_point = (demand * lead_time_days) + safety_buffer
    suggested_order_qty = max(0, int(ceil(reorder_point - inventory)))

    return {
        "daysUntilStockout": days_until_stockout,
        "reorderPoint": round(reorder_point),
        "suggestedOrderQty": suggested_order_qty,
        "storageCostImpact": round(suggested_order_qty * storage_cost_per_unit, 2),
        "orderCost": round(suggested_order_qty * cost, 2),
    }
