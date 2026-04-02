from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.services.catalog_service import build_standard_response, list_sku_bundles, to_engine_record
from app.services.dashboard_service import build_dashboard_payload

router = APIRouter(tags=["Dashboard Aggregation"])


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundles = await list_sku_bundles(db, org_id=org_id)

    records = []
    for bundle in bundles:
        sku_doc = bundle.get("sku", {})
        listings = bundle.get("listings", [])
        competitors_by_listing = bundle.get("competitors_by_listing", {})
        for listing in listings:
            lid = str(listing.get("_id", ""))
            listing_bundle = {
                "sku": sku_doc,
                "primary_listing": listing,
                "primary_competitors": competitors_by_listing.get(lid, []),
            }
            record = to_engine_record(listing_bundle)
            record["listing_id"] = lid
            records.append(record)

    return build_dashboard_payload(records)


@router.get("/portfolio")
async def get_portfolio(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user=Depends(get_current_user),
):
    org_id = str(current_user["org_id"])
    bundles = await list_sku_bundles(db, org_id=org_id)

    rows = []
    for bundle in bundles:
        response = build_standard_response(bundle, include_all_listings=True)
        sku = response["sku"]
        sensitivity = sku["priceSensitivity"]
        sensitivity_num = 3 if sensitivity == "High" else 2 if sensitivity == "Medium" else 1

        for row in response.get("listings", []):
            listing = row.get("listing", {})
            computed = row.get("computed", {})
            price = float(listing.get("price", 0.0))
            cost = float(listing.get("cost", 0.0))
            margin = 0.0 if price <= 0 else round(((price - cost) / price) * 100, 1)
            profit = round(float(computed.get("profit", 0.0)) * 30, 2)

            rows.append(
                {
                    "skuId": sku["id"],
                    "name": " ".join(sku["name"].split(" ")[:2]),
                    "margin": margin,
                    "priceSensitivity": sensitivity_num,
                    "profit": profit,
                    "marketplace": listing.get("marketplace", "Amazon"),
                }
            )

    return rows
