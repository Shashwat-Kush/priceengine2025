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
    marketplace: str
    current_price: float
    cost: float
    competitor_price: float
    inventory: int
    daily_demand: float
    price_sensitivity: str
    category: str = "General"
    lead_time_days: int = 7
    storage_cost_per_unit: float = 5.0
    base_demand: Optional[float] = None
    festival_boost_potential: str = "medium"
    marketplace_strength: str = "medium"


class SKUUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    marketplace: Optional[str] = None
    current_price: Optional[float] = None
    cost: Optional[float] = None
    competitor_price: Optional[float] = None
    inventory: Optional[int] = None
    daily_demand: Optional[float] = None
    price_sensitivity: Optional[str] = None
    category: Optional[str] = None
    lead_time_days: Optional[int] = None
    storage_cost_per_unit: Optional[float] = None
    base_demand: Optional[float] = None
    festival_boost_potential: Optional[str] = None
    marketplace_strength: Optional[str] = None


class PriceSimulationRequest(BaseModel):
    price: float
    competitorPrice: float = Field(alias="competitorPrice")
    festivalBoost: bool = Field(default=False, alias="festivalBoost")


def sku_doc_from_create(payload: SKUCreate) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    data["_id"] = data.pop("id")
    data["price_sensitivity"] = normalize_sensitivity(data["price_sensitivity"])
    data["festival_boost_potential"] = normalize_sensitivity(data.get("festival_boost_potential", "medium"))
    data["marketplace_strength"] = normalize_sensitivity(data.get("marketplace_strength", "medium"))
    if data.get("base_demand") is None:
        data["base_demand"] = float(data["daily_demand"])
    data["created_at"] = now
    data["updated_at"] = now
    return data


def sku_doc_updates(payload: SKUUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if "price_sensitivity" in updates:
        updates["price_sensitivity"] = normalize_sensitivity(str(updates["price_sensitivity"]))
    if "festival_boost_potential" in updates:
        updates["festival_boost_potential"] = normalize_sensitivity(str(updates["festival_boost_potential"]))
    if "marketplace_strength" in updates:
        updates["marketplace_strength"] = normalize_sensitivity(str(updates["marketplace_strength"]))
    updates["updated_at"] = utc_now()
    return updates


def sku_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    current_price = float(doc["current_price"])
    cost = float(doc["cost"])
    competitor_price = float(doc["competitor_price"])
    daily_demand = float(doc["daily_demand"])

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
    }
