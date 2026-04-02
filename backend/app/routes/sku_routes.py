from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.sku_schema import (
    SKUCreate,
    SKUUpdate,
    competitor_docs_from_price,
    listing_doc_from_create,
    listing_doc_updates,
    sku_doc_from_create,
    sku_doc_updates,
    sku_to_frontend,
)
from app.services.catalog_service import (
    get_sku_bundle_scoped,
    list_sku_bundles,
    to_engine_record,
)

router = APIRouter(prefix="/skus", tags=["SKU Management"])


@router.get("")
async def list_skus(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundles = await list_sku_bundles(db, org_id=org_id)
    return [sku_to_frontend(to_engine_record(bundle)) for bundle in bundles]


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
    return sku_to_frontend(to_engine_record(bundle))


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

    listing_doc = listing_doc_from_create(payload, org_id=org_id, sku_id=payload.id)
    await db.listings.insert_one(listing_doc)

    competitor_docs = competitor_docs_from_price(
        listing_id=str(listing_doc["_id"]),
        org_id=org_id,
        competitor_price=payload.competitor_price,
    )
    if competitor_docs:
        await db.competitors.insert_many(competitor_docs)

    bundle = await get_sku_bundle_scoped(db, sku_id=payload.id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SKU creation failed")
    return sku_to_frontend(to_engine_record(bundle))


@router.put("/{sku_id}")
async def update_sku(
    sku_id: str,
    payload: SKUUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    updates = sku_doc_updates(payload)
    if updates:
        await db.skus.update_one({"_id": sku_id, "org_id": org_id}, {"$set": updates})

    primary_listing = bundle.get("primary_listing")
    listing_updates = listing_doc_updates(payload)
    if primary_listing and listing_updates:
        await db.listings.update_one(
            {"_id": primary_listing["_id"], "org_id": org_id},
            {"$set": listing_updates},
        )

    if payload.competitor_price is not None and primary_listing:
        first_comp = await db.competitors.find_one(
            {"listing_id": primary_listing["_id"], "org_id": org_id},
            sort=[("_id", 1)],
        )
        if first_comp:
            await db.competitors.update_one(
                {"_id": first_comp["_id"], "org_id": org_id},
                {"$set": {"price": float(payload.competitor_price)}},
            )
        else:
            docs = competitor_docs_from_price(
                listing_id=str(primary_listing["_id"]),
                org_id=org_id,
                competitor_price=payload.competitor_price,
            )
            if docs:
                await db.competitors.insert_many(docs)

    updated_bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not updated_bundle:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SKU update failed")
    return sku_to_frontend(to_engine_record(updated_bundle))


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
