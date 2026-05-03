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
from app.services.catalog_service import compute_listing_metrics, list_sku_bundles
from app.services.demand_service import adjust_demand_from_base
from app.services.forecast_service import forecast_base_demand
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
    festivals = await db.festivals.find({"org_id": org_id}).sort("_id", 1).to_list(length=None)

    events = []
    for fest in festivals:
        allowed_platforms = {str(p).strip().lower() for p in fest.get("platform", []) if str(p).strip()}
        opportunities = []
        for bundle in bundles:
            sku_doc = bundle.get("sku", {})
            listings = bundle.get("listings", [])
            competitors_by_listing = bundle.get("competitors_by_listing", {})

            for listing in listings:
                marketplace = str(listing.get("marketplace", "")).strip()
                if allowed_platforms and marketplace.lower() not in allowed_platforms:
                    continue

                current_price = float(listing.get("price", listing.get("current_price", 0.0)))
                cost = float(listing.get("cost", 0.0))
                lid = str(listing.get("_id", ""))
                listing_competitors = competitors_by_listing.get(lid, [])

                current_metrics = compute_listing_metrics(
                    sku_doc,
                    listing,
                    listing_competitors,
                    festival_multiplier=1.0,
                )
                min_comp_price = float(current_metrics["min_comp_price"])
                avg_comp_price = float(current_metrics["avg_comp_price"])

                suggested_price = round(current_price * (0.95 if float(fest["boost"]) >= 1.5 else 0.97), 2)
                forecast = forecast_base_demand(
                    sku=sku_doc,
                    listing=listing,
                    price=suggested_price,
                    competitor_price=min_comp_price,
                )
                demand_festival, _ = adjust_demand_from_base(
                    base_mean=float(forecast["mean"]),
                    base_variance=float(forecast["variance"]),
                    price=suggested_price,
                    price_sensitivity=str(sku_doc.get("price_sensitivity", "medium")),
                    avg_comp_price=avg_comp_price,
                    min_comp_price=min_comp_price,
                    festival_multiplier=float(fest["boost"]),
                )

                expected_units = int(round(demand_festival * 30))
                inventory_required = expected_units

                current_profit = float(current_metrics["profit"]) * 30
                festival_profit = (suggested_price - cost) * expected_units
                profit_impact = round(festival_profit - current_profit, 2)

                if profit_impact <= 0:
                    continue

                opportunities.append(
                    {
                        "skuId": str(sku_doc.get("_id", "")),
                        "listingId": lid,
                        "marketplace": marketplace,
                        "skuName": sku_doc.get("name", "Unnamed SKU"),
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
