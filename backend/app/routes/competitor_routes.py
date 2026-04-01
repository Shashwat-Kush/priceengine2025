from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.competitor_service import competitor_analysis

router = APIRouter(prefix="/competitor", tags=["Competitor Intelligence"])


@router.get("/{sku_id}")
async def get_competitor_view(sku_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    sku = await db.skus.find_one({"_id": sku_id})
    if not sku:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    analysis = competitor_analysis(sku)
    return {
        "sku": sku_to_frontend(sku),
        "history": analysis["history"],
        "undercutFrequency": analysis["undercutFrequency"],
        "risk": analysis["risk"],
    }
