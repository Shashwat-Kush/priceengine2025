from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SKUModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    name: str
    category: str
    marketplace: str
    current_price: float
    cost: float
    competitor_price: float
    inventory: int
    daily_demand: float
    price_sensitivity: str
    lead_time_days: int = 7
    storage_cost_per_unit: float = 5.0
    base_demand: float
    festival_boost_potential: str = "medium"
    marketplace_strength: str = "medium"
    created_at: datetime
    updated_at: datetime
