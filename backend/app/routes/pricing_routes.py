from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import PriceSimulationRequest
from app.services.pricing_service import optimize_price, simulate_price_change

router = APIRouter(prefix="/pricing", tags=["Pricing Engine"])


@router.get("/{sku_id}")
async def get_pricing_analysis(sku_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    sku = await db.skus.find_one({"_id": sku_id})
    if not sku:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    pricing = optimize_price(sku)
    return {
        "skuId": sku_id,
        **pricing,
    }


@router.post("/simulate/{sku_id}")
async def simulate_pricing_scenario(
    sku_id: str,
    payload: PriceSimulationRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    sku = await db.skus.find_one({"_id": sku_id})
    if not sku:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    return simulate_price_change(
        sku=sku,
        price=payload.price,
        competitor_price=payload.competitorPrice,
        festival_boost=payload.festivalBoost,
    )
