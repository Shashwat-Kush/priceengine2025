from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.services.demand_service import estimate_demand
from app.utils.helpers import days_until

router = APIRouter(tags=["Festival Engine"])

FESTIVAL_CATALOG = [
    {
        "id": "festival-diwali",
        "name": "Diwali",
        "date": "2026-10-20",
        "boost": 1.4,
        "platform": ["Amazon", "Flipkart", "Meesho"],
    },
    {
        "id": "festival-big-billion-days",
        "name": "Big Billion Days",
        "date": "2026-04-14",
        "boost": 1.6,
        "platform": ["Flipkart"],
    },
    {
        "id": "festival-independence-day-sale",
        "name": "Independence Day Sale",
        "date": "2026-08-15",
        "boost": 1.3,
        "platform": ["Amazon", "Flipkart"],
    },
]


@router.get("/festivals")
async def get_festival_plan(db: AsyncIOMotorDatabase = Depends(get_database)):
    skus = await db.skus.find().to_list(length=None)

    events = []
    for fest in FESTIVAL_CATALOG:
        opportunities = []
        for sku in skus:
            current_price = float(sku["current_price"])
            cost = float(sku["cost"])
            competitor_price = float(sku["competitor_price"])
            base_demand = float(sku.get("base_demand", sku.get("daily_demand", 1)))
            sensitivity = str(sku.get("price_sensitivity", "medium"))

            suggested_price = round(current_price * (0.95 if fest["boost"] >= 1.5 else 0.97), 2)

            demand_normal = estimate_demand(current_price, competitor_price, base_demand, sensitivity)
            demand_festival = estimate_demand(
                suggested_price,
                competitor_price,
                base_demand,
                sensitivity,
            ) * fest["boost"]

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
                "id": fest["id"],
                "name": fest["name"],
                "date": fest["date"],
                "daysUntil": days_until(fest["date"]),
                "platform": fest["platform"],
                "skuOpportunities": opportunities[:6],
            }
        )

    return events
