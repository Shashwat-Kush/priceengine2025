from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.sku_schema import PriceSimulationRequest
from app.services.catalog_service import build_standard_response, get_sku_bundle_scoped, to_engine_record
from app.services.pricing_service import optimize_price, simulate_price_change

router = APIRouter(prefix="/pricing", tags=["Pricing Engine"])


@router.get("/{sku_id}")
async def get_pricing_analysis(
    sku_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    engine_record = to_engine_record(bundle)
    pricing = optimize_price(engine_record)
    return {
        **build_standard_response(bundle),
        "optimization": pricing,
    }


@router.post("/simulate/{sku_id}")
async def simulate_pricing_scenario(
    sku_id: str,
    payload: PriceSimulationRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundle = await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=org_id)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

    engine_record = to_engine_record(bundle)
    return simulate_price_change(
        sku=engine_record,
        price=payload.price,
        competitor_price=payload.competitorPrice,
        festival_boost=payload.festivalBoost,
    )
