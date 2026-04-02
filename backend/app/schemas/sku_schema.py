from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.helpers import normalize_sensitivity, to_title_sensitivity, utc_now


def normalize_demand_scale(value: str) -> str:
    normalized = (value or "medium").strip().lower()
    if normalized not in {"low", "medium", "high"}:
        return "medium"
    return normalized


def map_base_demand_to_scale(base_demand: Optional[float]) -> str:
    if base_demand is None:
        return "medium"
    value = float(base_demand)
    if value < 8:
        return "low"
    if value < 18:
        return "medium"
    return "high"


class SKUCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=140)
    category: str = Field(default="General", min_length=1, max_length=80)
    demand_scale: str = "medium"
    price_sensitivity: str = "medium"
    festival_sensitivity: str = "medium"

    @field_validator("id", "name", "category", mode="before")
    @classmethod
    def _trim_text(cls, value: str) -> str:
        return str(value).strip()

    @field_validator("demand_scale", mode="before")
    @classmethod
    def _norm_scale(cls, value: str) -> str:
        return normalize_demand_scale(str(value))

    @field_validator("price_sensitivity", "festival_sensitivity", mode="before")
    @classmethod
    def _norm_sensitivity(cls, value: str) -> str:
        return normalize_sensitivity(str(value))


class SKUUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=140)
    category: Optional[str] = Field(default=None, min_length=1, max_length=80)
    demand_scale: Optional[str] = None
    price_sensitivity: Optional[str] = None
    festival_sensitivity: Optional[str] = None

    @field_validator("name", "category", mode="before")
    @classmethod
    def _trim_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("demand_scale", mode="before")
    @classmethod
    def _norm_optional_scale(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_demand_scale(str(value))

    @field_validator("price_sensitivity", "festival_sensitivity", mode="before")
    @classmethod
    def _norm_optional_sensitivity(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_sensitivity(str(value))


class PriceSimulationRequest(BaseModel):
    price: float = Field(gt=0)
    festivalBoost: bool = Field(default=False, alias="festivalBoost")
    competitorPrice: Optional[float] = Field(default=None, alias="competitorPrice")


def sku_doc_from_create(payload: SKUCreate) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    return {
        "_id": data["id"],
        "name": data["name"],
        "category": data.get("category", "General"),
        "demand_scale": normalize_demand_scale(data.get("demand_scale", "medium")),
        "price_sensitivity": normalize_sensitivity(data.get("price_sensitivity", "medium")),
        "festival_sensitivity": normalize_sensitivity(data.get("festival_sensitivity", "medium")),
        "created_at": now,
        "updated_at": now,
    }


def sku_doc_updates(payload: SKUUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if "demand_scale" in updates:
        updates["demand_scale"] = normalize_demand_scale(str(updates["demand_scale"]))
    if "price_sensitivity" in updates:
        updates["price_sensitivity"] = normalize_sensitivity(str(updates["price_sensitivity"]))
    if "festival_sensitivity" in updates:
        updates["festival_sensitivity"] = normalize_sensitivity(str(updates["festival_sensitivity"]))
    if updates:
        updates["updated_at"] = utc_now()
    return updates


def sku_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    demand_scale = str(doc.get("demand_scale") or map_base_demand_to_scale(doc.get("base_demand")))
    festival = str(doc.get("festival_sensitivity") or doc.get("festival_boost_potential", "medium"))

    return {
        "id": str(doc.get("_id", "")),
        "name": str(doc.get("name", "Unnamed SKU")),
        "category": str(doc.get("category", "General")),
        "demandScale": to_title_sensitivity(demand_scale),
        "priceSensitivity": to_title_sensitivity(str(doc.get("price_sensitivity", "medium"))),
        "festivalSensitivity": to_title_sensitivity(festival),
    }
