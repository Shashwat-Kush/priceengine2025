from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.schemas.sku_schema import sku_to_frontend
from app.services.catalog_service import (
    competitor_to_response,
    compute_listing_metrics,
    listing_to_response,
    list_sku_bundles,
)
from app.services.inventory_service import group_reorders, inventory_metrics

router = APIRouter(tags=["Inventory Planning"])


async def _build_inventory_rows(db: AsyncIOMotorDatabase, org_id: str) -> list[dict]:
    bundles = await list_sku_bundles(db, org_id=org_id)
    rows = []
    for bundle in bundles:
        sku_doc = bundle.get("sku", {})
        listings = bundle.get("listings", [])
        competitors_by_listing = bundle.get("competitors_by_listing", {})

        for listing in sorted(
            listings,
            key=lambda row: (str(row.get("marketplace", "")).lower(), str(row.get("_id", ""))),
        ):
            lid = str(listing.get("_id", ""))
            listing_competitors = competitors_by_listing.get(lid, [])
            listing_computed = compute_listing_metrics(sku_doc, listing, listing_competitors)
            listing_response = listing_to_response(listing)

            computed = {
                "demand": listing_computed["demand"],
                "demand_mean": listing_computed["demand_mean"],
                "demand_variance": listing_computed["demand_variance"],
                "profit": listing_computed["profit"],
                "revenue": listing_computed["revenue"],
                "margin_pct": listing_computed["margin_pct"],
                "avg_comp_price": listing_computed["avg_comp_price"],
                "min_comp_price": listing_computed["min_comp_price"],
                "days_to_stockout": listing_computed["days_to_stockout"],
                "reorder_qty": listing_computed["reorder_qty"],
                "reorder_point": listing_computed["reorder_point"],
                "safety_stock": listing_computed["safety_stock"],
                "service_level": listing_computed["service_level"],
                "stockout_risk": listing_computed["stockout_risk"],
                "holding_cost": listing_computed["holding_cost"],
                "logistics_cost": listing_computed["logistics_cost"],
                "stockout_penalty": listing_computed["stockout_penalty"],
                "forecast_source": listing_computed["forecast_source"],
            }

            metrics = inventory_metrics(
                {
                    "inventory": listing_response.get("inventory", 0),
                    "demand_mean": computed.get("demand", 0),
                    "demand_variance": computed.get("demand_variance", 0),
                    "lead_time_days": listing_response.get("leadTimeDays", 0),
                    "storage_cost_per_unit": listing_response.get("storageCostPerUnit", 0),
                    "cost": listing_response.get("cost", 0),
                    "service_level": listing_response.get("serviceLevel", 0.95),
                }
            )

            rows.append(
                {
                    "sku": sku_to_frontend(sku_doc),
                    "listing": listing_response,
                    "competitors": [competitor_to_response(row) for row in listing_competitors],
                    "computed": {
                        "demand": computed["demand"],
                        "demandMean": computed["demand_mean"],
                        "demandVariance": computed["demand_variance"],
                        "profit": computed["profit"],
                        "revenue": computed["revenue"],
                        "marginPct": computed["margin_pct"],
                        "avgCompPrice": computed["avg_comp_price"],
                        "minCompPrice": computed["min_comp_price"],
                        "daysToStockout": computed["days_to_stockout"],
                        "reorderQty": computed["reorder_qty"],
                        "reorderPoint": computed["reorder_point"],
                        "safetyStock": computed["safety_stock"],
                        "serviceLevel": computed["service_level"],
                        "stockoutRisk": computed["stockout_risk"],
                        "holdingCost": computed["holding_cost"],
                        "logisticsCost": computed["logistics_cost"],
                        "stockoutPenalty": computed["stockout_penalty"],
                        "forecastSource": computed["forecast_source"],
                    },
                    "inventory": listing_response.get("inventory", 0),
                    "orderCost": metrics["orderCost"],
                    "storageCostImpact": metrics["storageCostImpact"],
                    "reorderPoint": metrics["reorderPoint"],
                    "suggestedOrderQty": metrics["suggestedOrderQty"],
                    "safetyStock": metrics["safetyStock"],
                    "serviceLevel": metrics["serviceLevel"],
                    "stockoutRisk": metrics["stockoutRisk"],
                }
            )

    return rows


@router.get("/inventory")
async def get_inventory(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    return await _build_inventory_rows(db, org_id=org_id)


@router.get("/inventory/grouping")
async def get_inventory_grouping(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    rows = await _build_inventory_rows(db, org_id=org_id)
    return group_reorders(rows)
