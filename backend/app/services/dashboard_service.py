from app.services.pricing_service import optimize_price
from app.utils.helpers import compute_inventory_status


def _alert_row(
    alert_id: str,
    alert_type: str,
    severity: str,
    sku_id: str,
    sku_name: str,
    message: str,
) -> dict:
    return {
        "id": alert_id,
        "type": alert_type,
        "severity": severity,
        "skuId": sku_id,
        "skuName": sku_name,
        "message": message,
    }


def build_dashboard_payload(skus: list[dict]) -> dict:
    total_revenue = 0.0
    total_profit = 0.0
    missed_profit = 0.0

    recommendations: list[dict] = []
    alerts: list[dict] = []

    low_inventory_count = 0
    undercut_count = 0

    for idx, sku in enumerate(skus, start=1):
        pricing = optimize_price(sku)

        demand = float(sku.get("demand", 0))
        current_price = float(sku.get("price", sku.get("current_price", 0.0)))
        cost = float(sku["cost"])
        inventory = int(sku.get("inventory", 0))
        competitor_price = float(sku.get("min_comp_price", current_price))
        listing_id = str(sku.get("listing_id", ""))

        monthly_revenue = current_price * demand * 30
        monthly_profit = (current_price - cost) * demand * 30

        total_revenue += monthly_revenue
        total_profit += monthly_profit
        missed_profit += max(0.0, pricing["optimalProfit"] - pricing["currentProfit"])

        if pricing["estimatedProfitChange"] > 0:
            reason = (
                "Price above market. Reducing to recommended range can improve conversion."
                if current_price > competitor_price
                else "Current demand can support a better profit-optimized price."
            )
            recommendations.append(
                {
                    "skuId": str(sku["_id"]),
                    "listingId": listing_id,
                    "skuName": sku["name"],
                    "marketplace": sku["marketplace"],
                    "currentPrice": current_price,
                    "recommendedMin": pricing["recommendedMin"],
                    "recommendedMax": pricing["recommendedMax"],
                    "estimatedProfitChange": round(pricing["estimatedProfitChange"], 2),
                    "reason": reason,
                }
            )

        status = compute_inventory_status(inventory, demand)
        if status in {"Critical", "Low"}:
            low_inventory_count += 1
            alerts.append(
                _alert_row(
                    f"alert-low-{idx}",
                    "low_stock",
                    "high" if status == "Critical" else "medium",
                    str(sku["_id"]),
                    sku["name"],
                    f"Inventory is {inventory} units with computed demand {demand:.1f}. Reorder suggested.",
                )
            )

        if current_price > competitor_price:
            undercut_count += 1
            gap = round(current_price - competitor_price, 2)
            alerts.append(
                _alert_row(
                    f"alert-undercut-{idx}",
                    "undercut",
                    "high" if gap > current_price * 0.05 else "medium",
                    str(sku["_id"]),
                    sku["name"],
                    f"Competitor is ₹{gap:.0f} cheaper on average.",
                )
            )

        if str(sku.get("festival_sensitivity", "medium")).lower() == "high" and inventory > demand * 10:
            alerts.append(
                _alert_row(
                    f"alert-fest-{idx}",
                    "festival_opportunity",
                    "low",
                    str(sku["_id"]),
                    sku["name"],
                    "Festival demand potential is high. Consider campaign pricing.",
                )
            )

    recommendations.sort(key=lambda row: row["estimatedProfitChange"], reverse=True)

    return {
        "kpis": {
            "totalRevenue": round(total_revenue, 2),
            "totalProfit": round(total_profit, 2),
            "missedProfit": round(missed_profit, 2),
            "inventoryAlerts": low_inventory_count,
            "undercutAlerts": undercut_count,
        },
        "recommendedActions": recommendations[:8],
        "alerts": alerts[:20],
    }
