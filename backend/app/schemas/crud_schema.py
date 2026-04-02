from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.helpers import utc_now


class ListingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(default=None, min_length=3, max_length=160)
    sku_id: str = Field(min_length=1, max_length=120)
    marketplace: str = Field(min_length=2, max_length=40)
    current_price: float = Field(gt=0)
    cost: float = Field(ge=0)
    inventory: int = Field(ge=0)
    daily_demand: float = Field(ge=0)
    lead_time_days: int = Field(ge=1, le=180)
    storage_cost_per_unit: float = Field(ge=0)

    @field_validator("id", "sku_id", mode="before")
    @classmethod
    def _trim_ids(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("marketplace", mode="before")
    @classmethod
    def _trim_marketplace(cls, value: str) -> str:
        return str(value).strip()


class ListingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku_id: Optional[str] = Field(default=None, min_length=1, max_length=120)
    marketplace: Optional[str] = Field(default=None, min_length=2, max_length=40)
    current_price: Optional[float] = Field(default=None, gt=0)
    cost: Optional[float] = Field(default=None, ge=0)
    inventory: Optional[int] = Field(default=None, ge=0)
    daily_demand: Optional[float] = Field(default=None, ge=0)
    lead_time_days: Optional[int] = Field(default=None, ge=1, le=180)
    storage_cost_per_unit: Optional[float] = Field(default=None, ge=0)

    @field_validator("sku_id", "marketplace", mode="before")
    @classmethod
    def _trim_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()


class CompetitorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(default=None, min_length=3, max_length=160)
    listing_id: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=2, max_length=120)
    price: float = Field(gt=0)
    rating: float = Field(default=4.0, ge=0, le=5)
    shipping_days: int = Field(default=3, ge=0, le=30)

    @field_validator("id", "listing_id", "name", mode="before")
    @classmethod
    def _trim_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()


class CompetitorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: Optional[str] = Field(default=None, min_length=1, max_length=160)
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    price: Optional[float] = Field(default=None, gt=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    shipping_days: Optional[int] = Field(default=None, ge=0, le=30)

    @field_validator("listing_id", "name", mode="before")
    @classmethod
    def _trim_optional_comp_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()


class FestivalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(default=None, min_length=3, max_length=160)
    name: str = Field(min_length=2, max_length=120)
    date: date
    boost: float = Field(ge=1.0, le=5.0)
    platform: List[str] = Field(min_length=1, max_length=6)

    @field_validator("id", "name", mode="before")
    @classmethod
    def _trim_festival_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("platform")
    @classmethod
    def _normalize_platform(cls, value: List[str]) -> List[str]:
        cleaned = [entry.strip() for entry in value if entry and entry.strip()]
        if not cleaned:
            raise ValueError("platform must include at least one marketplace")
        return cleaned


class FestivalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    date: Optional[date] = None
    boost: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    platform: Optional[List[str]] = Field(default=None, min_length=1, max_length=6)

    @field_validator("name", mode="before")
    @classmethod
    def _trim_optional_festival_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("platform")
    @classmethod
    def _normalize_optional_platform(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        cleaned = [entry.strip() for entry in value if entry and entry.strip()]
        if not cleaned:
            raise ValueError("platform must include at least one marketplace")
        return cleaned


def generate_listing_id(sku_id: str, marketplace: str, org_id: str) -> str:
    market_slug = marketplace.strip().lower().replace(" ", "-")
    org_suffix = org_id.replace("org-", "")[:6] or "org"
    return f"lst-{sku_id}-{market_slug}-{org_suffix}-{uuid4().hex[:6]}"


def generate_competitor_id(listing_id: str) -> str:
    return f"cmp-{listing_id}-{uuid4().hex[:8]}"


def generate_festival_id(name: str, org_id: str) -> str:
    name_slug = "-".join(part for part in name.strip().lower().split(" ") if part)
    org_suffix = org_id.replace("org-", "")[:6] or "org"
    return f"festival-{name_slug}-{org_suffix}-{uuid4().hex[:4]}"


def listing_doc_from_create(payload: ListingCreate, org_id: str) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    listing_id = data.get("id") or generate_listing_id(
        sku_id=data["sku_id"],
        marketplace=data["marketplace"],
        org_id=org_id,
    )
    return {
        "_id": listing_id,
        "org_id": org_id,
        "sku_id": data["sku_id"],
        "marketplace": data["marketplace"],
        "current_price": float(data["current_price"]),
        "cost": float(data["cost"]),
        "inventory": int(data["inventory"]),
        "daily_demand": float(data["daily_demand"]),
        "lead_time_days": int(data["lead_time_days"]),
        "storage_cost_per_unit": float(data["storage_cost_per_unit"]),
        "created_at": now,
        "updated_at": now,
    }


def listing_doc_updates(payload: ListingUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if updates:
        updates["updated_at"] = utc_now()
    return updates


def competitor_doc_from_create(payload: CompetitorCreate, org_id: str) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    competitor_id = data.get("id") or generate_competitor_id(data["listing_id"])
    return {
        "_id": competitor_id,
        "org_id": org_id,
        "listing_id": data["listing_id"],
        "name": data["name"],
        "price": float(data["price"]),
        "rating": float(data.get("rating", 4.0)),
        "shipping_days": int(data.get("shipping_days", 3)),
        "last_updated": now,
    }


def competitor_doc_updates(payload: CompetitorUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if updates:
        updates["last_updated"] = utc_now()
    return updates


def festival_doc_from_create(payload: FestivalCreate, org_id: str) -> Dict[str, Any]:
    now = utc_now()
    data = payload.model_dump()
    festival_id = data.get("id") or generate_festival_id(data["name"], org_id=org_id)
    return {
        "_id": festival_id,
        "org_id": org_id,
        "name": data["name"],
        "date": data["date"].isoformat(),
        "boost": float(data["boost"]),
        "platform": data["platform"],
        "created_at": now,
        "updated_at": now,
    }


def festival_doc_updates(payload: FestivalUpdate) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if "date" in updates and updates["date"] is not None:
        updates["date"] = updates["date"].isoformat()
    if updates:
        updates["updated_at"] = utc_now()
    return updates


def listing_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id", "")),
        "skuId": str(doc.get("sku_id", "")),
        "marketplace": str(doc.get("marketplace", "Amazon")),
        "currentPrice": float(doc.get("current_price", 0.0)),
        "cost": float(doc.get("cost", 0.0)),
        "inventory": int(doc.get("inventory", 0)),
        "dailyDemand": float(doc.get("daily_demand", 0.0)),
        "leadTimeDays": int(doc.get("lead_time_days", 7)),
        "storageCostPerUnit": float(doc.get("storage_cost_per_unit", 0.0)),
    }


def competitor_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id", "")),
        "listingId": str(doc.get("listing_id", "")),
        "name": str(doc.get("name", "Competitor")),
        "price": float(doc.get("price", 0.0)),
        "rating": float(doc.get("rating", 0.0)),
        "shippingDays": int(doc.get("shipping_days", 0)),
    }


def festival_to_frontend(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id", "")),
        "name": str(doc.get("name", "")),
        "date": str(doc.get("date", "")),
        "boost": float(doc.get("boost", 1.0)),
        "platform": list(doc.get("platform", [])),
    }