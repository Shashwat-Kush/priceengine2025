from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.catalog_service import get_sku_bundle_scoped, to_engine_record
from app.services.competitor_service import competitor_analysis

router = APIRouter(prefix="/competitor", tags=["Competitor Intelligence"])


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
