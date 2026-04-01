from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.inventory_service import inventory_metrics

router = APIRouter(tags=["Inventory Planning"])


@router.get("/inventory")
async def get_inventory(db: AsyncIOMotorDatabase = Depends(get_database)):
    docs = await db.skus.find().sort("_id", 1).to_list(length=None)

    rows = []
    for doc in docs:
        sku = sku_to_frontend(doc)
        metrics = inventory_metrics(doc)
        rows.append({
            **sku,
            **metrics,
        })

    return rows
