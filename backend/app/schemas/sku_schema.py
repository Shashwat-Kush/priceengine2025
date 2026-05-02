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


def normalize_features(value: Any) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        return {}

    normalized: Dict[str, str] = {}
    for raw_key, raw_val in value.items():
        key = str(raw_key).strip()
        val = str(raw_val).strip()
        if not key or not val:
            continue
        normalized[key[:80]] = val[:220]
    return normalized


class SKUCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=140)
    category: str = Field(default="General", min_length=1, max_length=80)
    demand_scale: str = "medium"
    price_sensitivity: str = "medium"
    festival_sensitivity: str = "medium"
    description: Optional[str] = Field(default=None, max_length=1200)
    features: Dict[str, str] = Field(default_factory=dict)
    image_url: Optional[str] = Field(default=None, max_length=2000)

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

    @field_validator("description", "image_url", mode="before")
    @classmethod
    def _trim_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @field_validator("features", mode="before")
    @classmethod
    def _norm_features(cls, value: Any) -> Dict[str, str]:
        return normalize_features(value)


class SKUUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=140)
    category: Optional[str] = Field(default=None, min_length=1, max_length=80)
    demand_scale: Optional[str] = None
    price_sensitivity: Optional[str] = None
    festival_sensitivity: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=1200)
    features: Optional[Dict[str, str]] = None
    image_url: Optional[str] = Field(default=None, max_length=2000)

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

    @field_validator("description", "image_url", mode="before")
    @classmethod
    def _trim_optional_long_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("features", mode="before")
    @classmethod
    def _norm_optional_features(cls, value: Any) -> Optional[Dict[str, str]]:
        if value is None:
            return None
        return normalize_features(value)


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
        "description": data.get("description"),
        "features": normalize_features(data.get("features")),
        "image_url": data.get("image_url"),
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
    if "features" in updates:
        updates["features"] = normalize_features(updates["features"])
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
        "description": str(doc.get("description", "") or ""),
        "features": normalize_features(doc.get("features")),
        "imageUrl": str(doc.get("image_url", "") or ""),
        "demandScale": to_title_sensitivity(demand_scale),
        "priceSensitivity": to_title_sensitivity(str(doc.get("price_sensitivity", "medium"))),
        "festivalSensitivity": to_title_sensitivity(festival),
    }
