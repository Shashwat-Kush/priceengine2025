from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.dashboard_service import build_dashboard_payload

router = APIRouter(tags=["Dashboard Aggregation"])


@router.get("/dashboard")
async def get_dashboard(db: AsyncIOMotorDatabase = Depends(get_database)):
    skus = await db.skus.find().to_list(length=None)
    return build_dashboard_payload(skus)


@router.get("/portfolio")
async def get_portfolio(db: AsyncIOMotorDatabase = Depends(get_database)):
    skus = await db.skus.find().to_list(length=None)

    rows = []
    for doc in skus:
        sku = sku_to_frontend(doc)
        sensitivity = sku["priceSensitivity"]
        sensitivity_num = 3 if sensitivity == "High" else 2 if sensitivity == "Medium" else 1
        profit = round((sku["currentPrice"] - sku["cost"]) * sku["dailyDemand"] * 30, 2)
        rows.append(
            {
                "skuId": sku["id"],
                "name": " ".join(sku["name"].split(" ")[:2]),
                "margin": sku["margin"],
                "priceSensitivity": sensitivity_num,
                "profit": profit,
                "marketplace": sku["marketplace"],
            }
        )

    return rows
