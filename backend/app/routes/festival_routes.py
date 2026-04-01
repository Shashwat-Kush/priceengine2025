from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.services.catalog_service import list_sku_bundles, to_engine_record
from app.services.demand_service import estimate_demand
from app.utils.helpers import days_until

router = APIRouter(tags=["Festival Engine"])

@router.get("/festivals")
async def get_festival_plan(db: AsyncIOMotorDatabase = Depends(get_database)):
    bundles = await list_sku_bundles(db)
    records = [to_engine_record(bundle) for bundle in bundles]
    festivals = await db.festivals.find().sort("_id", 1).to_list(length=None)

    events = []
    for fest in festivals:
        opportunities = []
        for sku in records:
            current_price = float(sku.get("current_price", 0.0))
            cost = float(sku.get("cost", 0.0))
            min_comp_price = float(sku.get("min_comp_price", current_price))
            avg_comp_price = float(sku.get("avg_comp_price", min_comp_price))
            base_demand = float(sku.get("base_demand", sku.get("daily_demand", 1.0)))
            sensitivity = str(sku.get("price_sensitivity", "medium"))

            suggested_price = round(current_price * (0.95 if float(fest["boost"]) >= 1.5 else 0.97), 2)

            demand_normal = estimate_demand(
                price=current_price,
                base_demand=base_demand,
                price_sensitivity=sensitivity,
                min_comp_price=min_comp_price,
                avg_comp_price=avg_comp_price,
            )
            demand_festival = estimate_demand(
                price=suggested_price,
                base_demand=base_demand,
                price_sensitivity=sensitivity,
                min_comp_price=min_comp_price,
                avg_comp_price=avg_comp_price,
            ) * float(fest["boost"])

            expected_units = int(round(demand_festival * 30))
            inventory_required = expected_units

            current_profit = (current_price - cost) * demand_normal * 30
            festival_profit = (suggested_price - cost) * expected_units
            profit_impact = round(festival_profit - current_profit, 2)

            if profit_impact <= 0:
                continue

            opportunities.append(
                {
                    "skuId": str(sku["_id"]),
                    "skuName": sku["name"],
                    "suggestedPrice": suggested_price,
                    "currentPrice": current_price,
                    "expectedUnits": expected_units,
                    "inventoryRequired": inventory_required,
                    "profitImpact": profit_impact,
                }
            )

        opportunities.sort(key=lambda row: row["profitImpact"], reverse=True)
        events.append(
            {
                "id": fest.get("_id", fest.get("id")),
                "name": fest["name"],
                "date": fest["date"],
                "daysUntil": days_until(fest["date"]),
                "platform": fest["platform"],
                "skuOpportunities": opportunities[:6],
            }
        )

    return events
