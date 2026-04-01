from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.utils.helpers import (
    compute_competitor_risk,
    compute_inventory_status,
    compute_margin_pct,
    normalize_sensitivity,
    to_title_sensitivity,
    utc_now,
)


class SKUCreate(BaseModel):
    id: str
    name: str
    category: str = "General"
    base_demand: Optional[float] = None
    price_sensitivity: str = "medium"
    festival_boost_potential: str = "medium"

    # Backward-compatible listing fields for phase-1 frontend/API stability.
    marketplace: str = "Amazon"
    current_price: float = 0.0
    cost: float = 0.0
    competitor_price: Optional[float] = None
    inventory: int = 0
    daily_demand: float = 0.0
    lead_time_days: int = 7
    storage_cost_per_unit: float = 5.0


class SKUUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    category: Optional[str] = None
    base_demand: Optional[float] = None
    price_sensitivity: Optional[str] = None
    festival_boost_potential: Optional[str] = None

    # Optional listing updates (applied to primary listing).
    marketplace: Optional[str] = None
    current_price: Optional[float] = None
    cost: Optional[float] = None
    competitor_price: Optional[float] = None
    inventory: Optional[int] = None
    daily_demand: Optional[float] = None
    lead_time_days: Optional[int] = None
    storage_cost_per_unit: Optional[float] = None


class PriceSimulationRequest(BaseModel):
    price: float
    competitorPrice: float = Field(alias="competitorPrice")
    festivalBoost: bool = Field(default=False, alias="festivalBoost")


def sku_doc_from_create(payload: SKUCreate) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    return {
        "_id": data["id"],
        "name": data["name"],
        "category": data.get("category", "General"),
        "base_demand": float(data.get("base_demand") or data.get("daily_demand") or 0.0),
        "price_sensitivity": normalize_sensitivity(data.get("price_sensitivity", "medium")),
        "festival_boost_potential": normalize_sensitivity(data.get("festival_boost_potential", "medium")),
        "created_at": now,
        "updated_at": now,
    }


def listing_doc_from_create(payload: SKUCreate, org_id: str, sku_id: str) -> Dict[str, Any]:
    now = utc_now()
    return {
        "_id": f"lst-{sku_id}-{payload.marketplace.strip().lower() or 'marketplace'}",
        "sku_id": sku_id,
        "org_id": org_id,
        "marketplace": payload.marketplace,
        "current_price": float(payload.current_price),
        "cost": float(payload.cost),
        "inventory": int(payload.inventory),
        "daily_demand": float(payload.daily_demand),
        "lead_time_days": int(payload.lead_time_days),
        "storage_cost_per_unit": float(payload.storage_cost_per_unit),
        "created_at": now,
        "updated_at": now,
    }


def competitor_docs_from_price(listing_id: str, org_id: str, competitor_price: Optional[float]) -> list[Dict[str, Any]]:
    if competitor_price is None:
        return []

    now = utc_now()
    base = float(competitor_price)
    return [
        {
            "_id": f"cmp-{listing_id}-1",
            "listing_id": listing_id,
            "org_id": org_id,
            "name": "Competitor 1",
            "price": round(base * 0.99, 2),
            "rating": 4.1,
            "shipping_days": 2,
            "last_updated": now,
        },
        {
            "_id": f"cmp-{listing_id}-2",
            "listing_id": listing_id,
            "org_id": org_id,
            "name": "Competitor 2",
            "price": round(base * 1.01, 2),
            "rating": 3.9,
            "shipping_days": 3,
            "last_updated": now,
        },
    ]


def sku_doc_updates(payload: SKUUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    allowed = {"name", "category", "base_demand", "price_sensitivity", "festival_boost_potential"}
    updates = {key: value for key, value in updates.items() if key in allowed}

    if "price_sensitivity" in updates:
        updates["price_sensitivity"] = normalize_sensitivity(str(updates["price_sensitivity"]))
    if "festival_boost_potential" in updates:
        updates["festival_boost_potential"] = normalize_sensitivity(str(updates["festival_boost_potential"]))
    if updates:
        updates["updated_at"] = utc_now()
    return updates


def listing_doc_updates(payload: SKUUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    allowed = {
        "marketplace",
        "current_price",
        "cost",
        "inventory",
        "daily_demand",
        "lead_time_days",
        "storage_cost_per_unit",
    }
    listing_updates = {key: value for key, value in updates.items() if key in allowed}
    if listing_updates:
        listing_updates["updated_at"] = utc_now()
    return listing_updates


def sku_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    current_price = float(doc.get("current_price", 0.0))
    cost = float(doc.get("cost", 0.0))
    competitor_price = float(doc.get("competitor_price", current_price))
    daily_demand = float(doc.get("daily_demand", doc.get("base_demand", 0.0)))

    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name", "Unnamed SKU"),
        "category": doc.get("category", "General"),
        "marketplace": doc.get("marketplace", "Amazon"),
        "currentPrice": current_price,
        "cost": cost,
        "competitorPrice": competitor_price,
        "inventory": int(doc.get("inventory", 0)),
        "dailyDemand": daily_demand,
        "priceSensitivity": to_title_sensitivity(doc.get("price_sensitivity", "medium")),
        "competitorRisk": compute_competitor_risk(
            current_price,
            competitor_price,
            str(doc.get("price_sensitivity", "medium")),
        ),
        "inventoryStatus": compute_inventory_status(int(doc.get("inventory", 0)), daily_demand),
        "margin": compute_margin_pct(current_price, cost),
        "leadTimeDays": int(doc.get("lead_time_days", 7)),
        "storageCostPerUnit": float(doc.get("storage_cost_per_unit", 5.0)),
        "baseDemand": float(doc.get("base_demand", daily_demand)),
        "festivalBoostPotential": to_title_sensitivity(doc.get("festival_boost_potential", "medium")),
        "marketplaceStrength": to_title_sensitivity(doc.get("marketplace_strength", "medium")),
        # Backward-compatible snake_case keys for consumers expecting backend-native shape.
        "current_price": current_price,
        "competitor_price": competitor_price,
    }
