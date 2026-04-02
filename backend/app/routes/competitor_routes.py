from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.crud_schema import (
    CompetitorCreate,
    CompetitorUpdate,
    competitor_doc_from_create,
    competitor_doc_updates,
    competitor_to_frontend,
)
from app.schemas.sku_schema import sku_to_frontend
from app.services.catalog_service import get_sku_bundle_scoped, to_engine_record
from app.services.competitor_service import competitor_analysis

router = APIRouter(prefix="/competitor", tags=["Competitor Intelligence"])


@router.get("/by-sku/{sku_id}")
async def list_competitors_for_sku(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    if not await db.skus.find_one({"_id": sku_id, "org_id": org_id}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    listing_rows = await db.listings.find(
        {"sku_id": sku_id, "org_id": org_id},
        {"_id": 1, "marketplace": 1},
    ).to_list(length=None)
    listing_ids = [str(row["_id"]) for row in listing_rows]
    marketplace_by_listing = {
        str(row["_id"]): str(row.get("marketplace", "")) for row in listing_rows
    }
    if not listing_ids:
        return []

    competitors = await db.competitors.find(
        {"listing_id": {"$in": listing_ids}, "org_id": org_id}
    ).sort("_id", 1).to_list(length=None)

    rows = []
    for comp in competitors:
        rows.append(
            {
                **competitor_to_frontend(comp),
                "skuId": sku_id,
                "marketplace": marketplace_by_listing.get(str(comp.get("listing_id", "")), ""),
            }
        )
    return rows


@router.get("/list/{listing_id}")
async def list_competitors_for_listing(
    listing_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    listing = await db.listings.find_one({"_id": listing_id, "org_id": org_id}, {"_id": 1})
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    competitors = await db.competitors.find(
        {"listing_id": listing_id, "org_id": org_id}
    ).sort("_id", 1).to_list(length=None)
    return [competitor_to_frontend(row) for row in competitors]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_competitor(
    payload: CompetitorCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    listing = await db.listings.find_one({"_id": payload.listing_id, "org_id": org_id}, {"_id": 1})
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    doc = competitor_doc_from_create(payload, org_id=org_id)
    if await db.competitors.find_one({"_id": doc["_id"]}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Competitor ID already exists")

    await db.competitors.insert_one(doc)
    return competitor_to_frontend(doc)


@router.put("/{competitor_id}")
async def update_competitor(
    competitor_id: str,
    payload: CompetitorUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    competitor = await db.competitors.find_one({"_id": competitor_id, "org_id": org_id})
    if not competitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    updates = competitor_doc_updates(payload)
    if "listing_id" in updates:
        if not await db.listings.find_one({"_id": updates["listing_id"], "org_id": org_id}, {"_id": 1}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target listing does not belong to organization")

    if updates:
        await db.competitors.update_one({"_id": competitor_id, "org_id": org_id}, {"$set": updates})

    updated = await db.competitors.find_one({"_id": competitor_id, "org_id": org_id})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Competitor update failed")
    return competitor_to_frontend(updated)


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    deleted = await db.competitors.delete_one({"_id": competitor_id, "org_id": org_id})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return {"deleted": True, "id": competitor_id}


@router.get("/{sku_id}")
async def get_competitor_view(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    engine_record = to_engine_record(bundle)
    analysis = competitor_analysis(
        engine_record=engine_record,
        listing=bundle.get("primary_listing") or {},
        competitors=bundle.get("primary_competitors", []),
    )
    return {
        "sku": sku_to_frontend(engine_record),
        "history": analysis["history"],
        "undercutFrequency": analysis["undercutFrequency"],
        "risk": analysis["risk"],
    }
