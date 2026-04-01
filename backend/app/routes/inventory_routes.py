from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.catalog_service import list_sku_bundles, to_engine_record
from app.services.inventory_service import inventory_metrics

router = APIRouter(tags=["Inventory Planning"])


@router.get("/inventory")
async def get_inventory(db: AsyncIOMotorDatabase = Depends(get_database)):
    bundles = await list_sku_bundles(db)

    rows = []
    for bundle in bundles:
        engine_record = to_engine_record(bundle)
        sku = sku_to_frontend(engine_record)
        metrics = inventory_metrics(engine_record)
        rows.append({
            **sku,
            **metrics,
        })

    return rows
