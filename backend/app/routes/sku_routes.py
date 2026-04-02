from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.sku_schema import (
    SKUCreate,
    SKUUpdate,
    sku_doc_from_create,
    sku_doc_updates,
)
from app.services.catalog_service import (
    build_standard_response,
    get_sku_bundle_scoped,
    list_sku_bundles,
)

router = APIRouter(prefix="/skus", tags=["SKU Management"])


@router.get("")
async def list_skus(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundles = await list_sku_bundles(db, org_id=org_id)
    return [build_standard_response(bundle) for bundle in bundles]


@router.get("/{sku_id}")
async def get_sku(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    return build_standard_response(bundle, include_all_listings=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sku(
    payload: SKUCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    if await db.skus.find_one({"_id": payload.id, "org_id": org_id}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    doc = sku_doc_from_create(payload)
    doc["org_id"] = org_id
    await db.skus.insert_one(doc)

    bundle = await get_sku_bundle_scoped(db, sku_id=payload.id, org_id=org_id)
    if bundle:
        return build_standard_response(bundle, include_all_listings=True)

    return {
        "sku": {
            "id": payload.id,
            "name": payload.name,
            "category": payload.category,
            "demandScale": payload.demand_scale.capitalize(),
            "priceSensitivity": payload.price_sensitivity.capitalize(),
            "festivalSensitivity": payload.festival_sensitivity.capitalize(),
        },
        "listing": None,
        "competitors": [],
        "computed": {
            "demand": 0.0,
            "profit": 0.0,
            "revenue": 0.0,
            "avg_comp_price": 0.0,
            "min_comp_price": 0.0,
            "days_to_stockout": 999,
            "reorder_qty": 0,
        },
        "listings": [],
    }


@router.put("/{sku_id}")
async def update_sku(
    sku_id: str,
    payload: SKUUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    if not await db.skus.find_one({"_id": sku_id, "org_id": org_id}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    updates = sku_doc_updates(payload)
    if updates:
        await db.skus.update_one({"_id": sku_id, "org_id": org_id}, {"$set": updates})

    updated_bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not updated_bundle:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SKU update failed")
    return build_standard_response(updated_bundle, include_all_listings=True)


@router.delete("/{sku_id}")
async def delete_sku(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    listing_ids = [
        str(row["_id"])
        for row in await db.listings.find({"sku_id": sku_id, "org_id": org_id}, {"_id": 1}).to_list(length=None)
    ]

    deleted = await db.skus.delete_one({"_id": sku_id, "org_id": org_id})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    await db.listings.delete_many({"sku_id": sku_id, "org_id": org_id})
    if listing_ids:
        await db.competitors.delete_many({"listing_id": {"$in": listing_ids}, "org_id": org_id})

    return {"deleted": True, "id": sku_id}
