from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.crud_schema import (
    ListingCreate,
    ListingUpdate,
    listing_doc_from_create,
    listing_doc_updates,
    listing_to_frontend,
)

router = APIRouter(prefix="/listings", tags=["Listing Management"])


@router.get("")
async def list_listings(
    sku_id: str | None = Query(default=None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    filters: dict = {"org_id": org_id}
    if sku_id:
        filters["sku_id"] = sku_id

    listings = await db.listings.find(filters).sort("_id", 1).to_list(length=None)
    return [listing_to_frontend(row) for row in listings]


@router.get("/by-sku/{sku_id}")
async def get_listings_by_sku(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    if not await db.skus.find_one({"_id": sku_id, "org_id": org_id}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    listings = await db.listings.find({"sku_id": sku_id, "org_id": org_id}).sort("_id", 1).to_list(length=None)
    return [listing_to_frontend(row) for row in listings]


@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    listing = await db.listings.find_one({"_id": listing_id, "org_id": org_id})
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing_to_frontend(listing)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    if not await db.skus.find_one({"_id": payload.sku_id, "org_id": org_id}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    listing_doc = listing_doc_from_create(payload, org_id=org_id)
    if await db.listings.find_one({"_id": listing_doc["_id"]}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Listing ID already exists")

    await db.listings.insert_one(listing_doc)
    return listing_to_frontend(listing_doc)


@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    payload: ListingUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    listing = await db.listings.find_one({"_id": listing_id, "org_id": org_id})
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    updates = listing_doc_updates(payload)
    if "sku_id" in updates:
        if not await db.skus.find_one({"_id": updates["sku_id"], "org_id": org_id}, {"_id": 1}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target SKU does not belong to organization")

    if updates:
        await db.listings.update_one({"_id": listing_id, "org_id": org_id}, {"$set": updates})

    updated = await db.listings.find_one({"_id": listing_id, "org_id": org_id})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Listing update failed")
    return listing_to_frontend(updated)


@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])

    deleted = await db.listings.delete_one({"_id": listing_id, "org_id": org_id})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    await db.competitors.delete_many({"listing_id": listing_id, "org_id": org_id})
    return {"deleted": True, "id": listing_id}