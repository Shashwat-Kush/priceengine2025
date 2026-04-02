from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.crud_schema import (
    FestivalCreate,
    FestivalUpdate,
    festival_doc_from_create,
    festival_doc_updates,
    festival_to_frontend,
)
from app.services.catalog_service import list_sku_bundles, to_engine_record
from app.services.demand_service import estimate_demand
from app.utils.helpers import days_until

router = APIRouter(tags=["Festival Engine"])


@router.get("/festivals/catalog")
async def list_festival_catalog(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    festivals = await db.festivals.find({"org_id": org_id}).sort("date", 1).to_list(length=None)
    return [festival_to_frontend(row) for row in festivals]


@router.post("/festivals/catalog", status_code=status.HTTP_201_CREATED)
async def create_festival(
    payload: FestivalCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    doc = festival_doc_from_create(payload, org_id=org_id)
    if await db.festivals.find_one({"_id": doc["_id"]}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Festival ID already exists")

    await db.festivals.insert_one(doc)
    return festival_to_frontend(doc)


@router.put("/festivals/catalog/{festival_id}")
async def update_festival(
    festival_id: str,
    payload: FestivalUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    festival = await db.festivals.find_one({"_id": festival_id, "org_id": org_id})
    if not festival:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festival not found")

    updates = festival_doc_updates(payload)
    if updates:
        await db.festivals.update_one({"_id": festival_id, "org_id": org_id}, {"$set": updates})

    updated = await db.festivals.find_one({"_id": festival_id, "org_id": org_id})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Festival update failed")
    return festival_to_frontend(updated)


@router.delete("/festivals/catalog/{festival_id}")
async def delete_festival(
    festival_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    deleted = await db.festivals.delete_one({"_id": festival_id, "org_id": org_id})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Festival not found")
    return {"deleted": True, "id": festival_id}

@router.get("/festivals")
async def get_festival_plan(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundles = await list_sku_bundles(db, org_id=org_id)
    records = [to_engine_record(bundle) for bundle in bundles]
    festivals = await db.festivals.find({"org_id": org_id}).sort("_id", 1).to_list(length=None)

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
