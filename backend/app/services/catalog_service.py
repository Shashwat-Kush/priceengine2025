from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.sku_schema import map_base_demand_to_scale, sku_to_frontend
from app.services.demand_service import adjust_demand_from_base
from app.services.forecast_service import forecast_base_demand
from app.services.inventory_service import inventory_metrics
from app.utils.helpers import compute_margin_pct, normalize_sensitivity


def _marketplace_priority(marketplace: str) -> int:
    normalized = (marketplace or "").strip().lower()
    if normalized == "amazon":
        return 0
    if normalized == "flipkart":
        return 1
    return 9


def _group_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        row_key = str(row.get(key, ""))
        grouped.setdefault(row_key, []).append(row)
    return grouped


def _aggregate_competitor_prices(competitors: List[Dict[str, Any]], fallback: float) -> tuple[float, float]:
    if not competitors:
        return fallback, fallback

    prices = [float(row.get("price", fallback)) for row in competitors]
    min_price = min(prices)
    avg_price = round(sum(prices) / len(prices), 2)
    return min_price, avg_price


def _listing_price(listing: Dict[str, Any]) -> float:
    return float(listing.get("price", listing.get("current_price", 0.0)))


def listing_to_response(listing: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(listing.get("_id", "")),
        "skuId": str(listing.get("sku_id", "")),
        "marketplace": str(listing.get("marketplace", "Amazon")),
        "price": _listing_price(listing),
        "cost": float(listing.get("cost", 0.0)),
        "inventory": int(listing.get("inventory", 0)),
        "leadTimeDays": int(listing.get("lead_time_days", 0)),
        "storageCostPerUnit": float(listing.get("storage_cost_per_unit", 0.0)),
        "serviceLevel": float(listing.get("service_level", 0.95)),
        "logisticsCostPerOrder": float(listing.get("logistics_cost_per_order", 150.0)),
        "minMarginPct": float(listing.get("min_margin_pct", 5.0)),
    }


def competitor_to_response(competitor: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(competitor.get("_id", "")),
        "listingId": str(competitor.get("listing_id", "")),
        "name": str(competitor.get("name", "Competitor")),
        "price": float(competitor.get("price", 0.0)),
        "rating": float(competitor.get("rating", 0.0)),
        "shippingDays": int(competitor.get("shipping_days", 0)),
    }


def _festival_multiplier_from_sensitivity(value: str) -> float:
    normalized = normalize_sensitivity(value)
    if normalized == "high":
        return 1.45
    if normalized == "low":
        return 1.10
    return 1.25


def compute_listing_metrics(
    sku: Dict[str, Any],
    listing: Dict[str, Any],
    competitors: List[Dict[str, Any]],
    festival_multiplier: Optional[float] = None,
) -> Dict[str, Any]:
    price = _listing_price(listing)
    cost = float(listing.get("cost", 0.0))
    inventory = int(listing.get("inventory", 0))
    lead_time_days = int(listing.get("lead_time_days", 0))
    service_level = float(listing.get("service_level", 0.95))
    logistics_cost_per_order = float(listing.get("logistics_cost_per_order", 150.0))

    min_comp_price, avg_comp_price = _aggregate_competitor_prices(competitors, price)

    price_sensitivity = normalize_sensitivity(str(sku.get("price_sensitivity", "medium")))
    festival_sensitivity = normalize_sensitivity(
        str(sku.get("festival_sensitivity") or sku.get("festival_boost_potential", "medium"))
    )

    effective_festival_multiplier = (
        float(festival_multiplier)
        if festival_multiplier is not None
        else _festival_multiplier_from_sensitivity(festival_sensitivity)
    )

    forecast = forecast_base_demand(
        sku=sku,
        listing=listing,
        price=price,
        competitor_price=min_comp_price,
    )
    base_mean = float(forecast["mean"])
    base_variance = float(forecast["variance"])

    demand, demand_variance = adjust_demand_from_base(
        base_mean=base_mean,
        base_variance=base_variance,
        price=price,
        price_sensitivity=price_sensitivity,
        avg_comp_price=avg_comp_price,
        min_comp_price=min_comp_price,
        festival_multiplier=effective_festival_multiplier,
    )

    revenue = round(price * demand, 2)
    gross_profit = (price - cost) * demand

    metrics = inventory_metrics(
        {
            "inventory": inventory,
            "demand_mean": demand,
            "demand_variance": demand_variance,
            "lead_time_days": lead_time_days,
            "storage_cost_per_unit": float(listing.get("storage_cost_per_unit", 0.0)),
            "cost": cost,
            "service_level": service_level,
        }
    )

    holding_cost = float(metrics["safetyStock"]) * float(listing.get("storage_cost_per_unit", 0.0))
    logistics_cost = logistics_cost_per_order if demand > 0 else 0.0
    stockout_penalty = gross_profit * float(metrics["stockoutRisk"])
    net_profit = gross_profit - holding_cost - logistics_cost - stockout_penalty

    return {
        "demand": round(demand, 2),
        "demand_mean": round(base_mean, 2),
        "demand_variance": round(demand_variance, 2),
        "revenue": round(revenue, 2),
        "profit": round(net_profit, 2),
        "margin_pct": compute_margin_pct(price, cost),
        "avg_comp_price": round(avg_comp_price, 2),
        "min_comp_price": round(min_comp_price, 2),
        "days_to_stockout": metrics["daysUntilStockout"],
        "reorder_qty": metrics["suggestedOrderQty"],
        "reorder_point": metrics["reorderPoint"],
        "safety_stock": metrics["safetyStock"],
        "service_level": metrics["serviceLevel"],
        "stockout_risk": metrics["stockoutRisk"],
        "holding_cost": round(holding_cost, 2),
        "logistics_cost": round(logistics_cost, 2),
        "stockout_penalty": round(stockout_penalty, 2),
        "forecast_source": forecast["source"],
    }


def choose_primary_listing(listings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not listings:
        return None

    return sorted(
        listings,
        key=lambda row: (
            _marketplace_priority(str(row.get("marketplace", ""))),
            str(row.get("_id", "")),
        ),
    )[0]


async def list_sku_bundles(db: AsyncIOMotorDatabase, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
    sku_filter: Dict[str, Any] = {}
    if org_id:
        sku_filter["org_id"] = org_id

    skus = await db.skus.find(sku_filter).sort("_id", 1).to_list(length=None)
    sku_ids = [str(row.get("_id")) for row in skus]

    listings: List[Dict[str, Any]] = []
    competitors: List[Dict[str, Any]] = []

    if sku_ids:
        listing_filter: Dict[str, Any] = {"sku_id": {"$in": sku_ids}}
        if org_id:
            listing_filter["org_id"] = org_id

        listings = await db.listings.find(listing_filter).to_list(length=None)
        listing_ids = [str(row.get("_id")) for row in listings]
        if listing_ids:
            competitor_filter: Dict[str, Any] = {"listing_id": {"$in": listing_ids}}
            if org_id:
                competitor_filter["org_id"] = org_id
            competitors = await db.competitors.find(competitor_filter).to_list(length=None)

    listings_by_sku = _group_by(listings, "sku_id")
    competitors_by_listing = _group_by(competitors, "listing_id")

    bundles: List[Dict[str, Any]] = []
    for sku in skus:
        sku_id = str(sku.get("_id"))
        sku_listings = listings_by_sku.get(sku_id, [])
        primary_listing = choose_primary_listing(sku_listings)

        primary_competitors: List[Dict[str, Any]] = []
        if primary_listing is not None:
            primary_competitors = competitors_by_listing.get(str(primary_listing.get("_id")), [])

        fallback_price = float(primary_listing.get("current_price", 0.0)) if primary_listing else 0.0
        min_comp_price, avg_comp_price = _aggregate_competitor_prices(primary_competitors, fallback_price)

        bundles.append(
            {
                "sku": sku,
                "listings": sku_listings,
                "primary_listing": primary_listing,
                "primary_competitors": primary_competitors,
                "competitors_by_listing": {
                    str(listing.get("_id")): competitors_by_listing.get(str(listing.get("_id")), [])
                    for listing in sku_listings
                },
                "min_comp_price": min_comp_price,
                "avg_comp_price": avg_comp_price,
            }
        )

    return bundles


async def get_sku_bundle(db: AsyncIOMotorDatabase, sku_id: str) -> Optional[Dict[str, Any]]:
    return await get_sku_bundle_scoped(db, sku_id=sku_id, org_id=None)


async def get_sku_bundle_scoped(
    db: AsyncIOMotorDatabase,
    sku_id: str,
    org_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    sku_filter: Dict[str, Any] = {"_id": sku_id}
    if org_id:
        sku_filter["org_id"] = org_id

    sku = await db.skus.find_one(sku_filter)
    if not sku:
        return None

    listing_filter: Dict[str, Any] = {"sku_id": sku_id}
    if org_id:
        listing_filter["org_id"] = org_id

    listings = await db.listings.find(listing_filter).to_list(length=None)
    primary_listing = choose_primary_listing(listings)

    competitors: List[Dict[str, Any]] = []
    competitors_by_listing: Dict[str, List[Dict[str, Any]]] = {}
    listing_ids = [str(row.get("_id")) for row in listings]
    if listing_ids:
        competitor_filter: Dict[str, Any] = {"listing_id": {"$in": listing_ids}}
        if org_id:
            competitor_filter["org_id"] = org_id
        competitors = await db.competitors.find(competitor_filter).to_list(length=None)
        competitors_by_listing = _group_by(competitors, "listing_id")

    primary_competitors: List[Dict[str, Any]] = []
    if primary_listing is not None:
        primary_competitors = competitors_by_listing.get(str(primary_listing.get("_id")), [])

    fallback_price = float(primary_listing.get("current_price", 0.0)) if primary_listing else 0.0
    min_comp_price, avg_comp_price = _aggregate_competitor_prices(primary_competitors, fallback_price)

    return {
        "sku": sku,
        "listings": listings,
        "primary_listing": primary_listing,
        "primary_competitors": primary_competitors,
        "competitors_by_listing": {
            str(listing.get("_id")): competitors_by_listing.get(str(listing.get("_id")), [])
            for listing in listings
        },
        "min_comp_price": min_comp_price,
        "avg_comp_price": avg_comp_price,
    }


def to_engine_record(bundle: Dict[str, Any]) -> Dict[str, Any]:
    sku = bundle["sku"]
    listing = bundle.get("primary_listing") or {}
    competitors = bundle.get("primary_competitors", [])
    computed = compute_listing_metrics(sku, listing, competitors) if listing else {
        "demand": 0.0,
        "demand_mean": 0.0,
        "demand_variance": 0.0,
        "revenue": 0.0,
        "profit": 0.0,
        "margin_pct": 0.0,
        "avg_comp_price": 0.0,
        "min_comp_price": 0.0,
        "days_to_stockout": 999,
        "reorder_qty": 0,
        "reorder_point": 0.0,
        "safety_stock": 0.0,
        "service_level": float(listing.get("service_level", 0.95)),
        "stockout_risk": 0.0,
        "holding_cost": 0.0,
        "logistics_cost": 0.0,
        "stockout_penalty": 0.0,
        "forecast_source": "heuristic",
    }

    return {
        "_id": str(sku.get("_id", "")),
        "org_id": str(sku.get("org_id", "")),
        "name": str(sku.get("name", "Unnamed SKU")),
        "category": str(sku.get("category", "General")),
        "demand_scale": str(sku.get("demand_scale") or map_base_demand_to_scale(sku.get("base_demand"))),
        "price_sensitivity": normalize_sensitivity(str(sku.get("price_sensitivity", "medium"))),
        "festival_sensitivity": normalize_sensitivity(
            str(sku.get("festival_sensitivity") or sku.get("festival_boost_potential", "medium"))
        ),
        "marketplace": str(listing.get("marketplace", "Amazon")),
        "price": _listing_price(listing),
        "cost": float(listing.get("cost", 0.0)),
        "inventory": int(listing.get("inventory", 0)),
        "lead_time_days": int(listing.get("lead_time_days", 0)),
        "storage_cost_per_unit": float(listing.get("storage_cost_per_unit", 0.0)),
        "service_level": float(listing.get("service_level", 0.95)),
        "logistics_cost_per_order": float(listing.get("logistics_cost_per_order", 150.0)),
        "min_margin_pct": float(listing.get("min_margin_pct", 5.0)),
        "demand": computed["demand"],
        "revenue": computed["revenue"],
        "profit": computed["profit"],
        "margin_pct": computed["margin_pct"],
        "avg_comp_price": computed["avg_comp_price"],
        "min_comp_price": computed["min_comp_price"],
        "days_to_stockout": computed["days_to_stockout"],
        "reorder_point": computed["reorder_point"],
        "safety_stock": computed["safety_stock"],
        "service_level": computed["service_level"],
        "stockout_risk": computed["stockout_risk"],
        "holding_cost": computed["holding_cost"],
        "logistics_cost": computed["logistics_cost"],
        "stockout_penalty": computed["stockout_penalty"],
        "forecast_source": computed["forecast_source"],
    }


def build_standard_response(
    bundle: Dict[str, Any],
    include_all_listings: bool = False,
) -> Dict[str, Any]:
    sku_doc = bundle["sku"]
    primary_listing = bundle.get("primary_listing") or {}
    primary_competitors = bundle.get("primary_competitors", [])

    computed = (
        compute_listing_metrics(sku_doc, primary_listing, primary_competitors)
        if primary_listing
        else {
            "demand": 0.0,
            "demand_mean": 0.0,
            "demand_variance": 0.0,
            "revenue": 0.0,
            "profit": 0.0,
            "margin_pct": 0.0,
            "avg_comp_price": 0.0,
            "min_comp_price": 0.0,
            "days_to_stockout": 999,
            "reorder_qty": 0,
            "reorder_point": 0.0,
            "safety_stock": 0.0,
            "service_level": float(primary_listing.get("service_level", 0.95)),
            "stockout_risk": 0.0,
            "holding_cost": 0.0,
            "logistics_cost": 0.0,
            "stockout_penalty": 0.0,
            "forecast_source": "heuristic",
        }
    )

    response: Dict[str, Any] = {
        "sku": sku_to_frontend(sku_doc),
        "listing": listing_to_response(primary_listing) if primary_listing else None,
        "competitors": [competitor_to_response(row) for row in primary_competitors],
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
    }

    if include_all_listings:
        listings = bundle.get("listings", [])
        competitors_by_listing = bundle.get("competitors_by_listing", {})
        listing_rows = []
        for listing in listings:
            lid = str(listing.get("_id", ""))
            listing_competitors = competitors_by_listing.get(lid, [])
            listing_computed = compute_listing_metrics(sku_doc, listing, listing_competitors)
            listing_rows.append(
                {
                    "listing": listing_to_response(listing),
                    "competitors": [competitor_to_response(row) for row in listing_competitors],
                    "computed": {
                        "demand": listing_computed["demand"],
                        "demandMean": listing_computed["demand_mean"],
                        "demandVariance": listing_computed["demand_variance"],
                        "profit": listing_computed["profit"],
                        "revenue": listing_computed["revenue"],
                        "marginPct": listing_computed["margin_pct"],
                        "avgCompPrice": listing_computed["avg_comp_price"],
                        "minCompPrice": listing_computed["min_comp_price"],
                        "daysToStockout": listing_computed["days_to_stockout"],
                        "reorderQty": listing_computed["reorder_qty"],
                        "reorderPoint": listing_computed["reorder_point"],
                        "safetyStock": listing_computed["safety_stock"],
                        "serviceLevel": listing_computed["service_level"],
                        "stockoutRisk": listing_computed["stockout_risk"],
                        "holdingCost": listing_computed["holding_cost"],
                        "logisticsCost": listing_computed["logistics_cost"],
                        "stockoutPenalty": listing_computed["stockout_penalty"],
                        "forecastSource": listing_computed["forecast_source"],
                    },
                }
            )
        response["listings"] = listing_rows

    return response
