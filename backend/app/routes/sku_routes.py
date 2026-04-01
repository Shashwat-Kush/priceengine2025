from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import (
    SKUCreate,
    SKUUpdate,
    sku_doc_from_create,
    sku_doc_updates,
    sku_to_frontend,
)

router = APIRouter(prefix="/skus", tags=["SKU Management"])


@router.get("")
async def list_skus(db: AsyncIOMotorDatabase = Depends(get_database)):
    docs = await db.skus.find().sort("_id", 1).to_list(length=None)
    return [sku_to_frontend(doc) for doc in docs]


@router.get("/{sku_id}")
async def get_sku(sku_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = await db.skus.find_one({"_id": sku_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    return sku_to_frontend(doc)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sku(payload: SKUCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    if await db.skus.find_one({"_id": payload.id}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    doc = sku_doc_from_create(payload)
    await db.skus.insert_one(doc)
    created = await db.skus.find_one({"_id": payload.id})
    return sku_to_frontend(created)


@router.put("/{sku_id}")
async def update_sku(
    sku_id: str,
    payload: SKUUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if not await db.skus.find_one({"_id": sku_id}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    updates = sku_doc_updates(payload)
    if updates:
        await db.skus.update_one({"_id": sku_id}, {"$set": updates})

    updated = await db.skus.find_one({"_id": sku_id})
    return sku_to_frontend(updated)


@router.delete("/{sku_id}")
async def delete_sku(sku_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    deleted = await db.skus.delete_one({"_id": sku_id})
    if deleted.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    return {"deleted": True, "id": sku_id}
