from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import normalize_sensitivity


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

    current_price = float(listing.get("current_price", 0.0))
    cost = float(listing.get("cost", 0.0))
    inventory = int(listing.get("inventory", 0))
    daily_demand = float(listing.get("daily_demand", sku.get("base_demand", 0.0)))
    lead_time_days = int(listing.get("lead_time_days", 7))
    storage_cost_per_unit = float(listing.get("storage_cost_per_unit", 5.0))

    price_sensitivity = normalize_sensitivity(str(sku.get("price_sensitivity", "medium")))
    festival_boost = normalize_sensitivity(str(sku.get("festival_boost_potential", "medium")))

    min_comp_price = float(bundle.get("min_comp_price", current_price))
    avg_comp_price = float(bundle.get("avg_comp_price", min_comp_price))

    listing_count = len(bundle.get("listings", []))
    if listing_count >= 2:
        marketplace_strength = "high"
    elif listing_count == 1:
        marketplace_strength = "medium"
    else:
        marketplace_strength = "low"

    return {
        "_id": str(sku.get("_id")),
        "org_id": str(sku.get("org_id", "")),
        "name": sku.get("name", "Unnamed SKU"),
        "category": sku.get("category", "General"),
        "marketplace": listing.get("marketplace", "Amazon"),
        "current_price": current_price,
        "cost": cost,
        "inventory": inventory,
        "daily_demand": daily_demand,
        "lead_time_days": lead_time_days,
        "storage_cost_per_unit": storage_cost_per_unit,
        "price_sensitivity": price_sensitivity,
        "base_demand": float(sku.get("base_demand", daily_demand)),
        "festival_boost_potential": festival_boost,
        "marketplace_strength": marketplace_strength,
        "competitor_price": min_comp_price,
        "min_comp_price": min_comp_price,
        "avg_comp_price": avg_comp_price,
    }
