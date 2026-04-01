from datetime import datetime

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: str
    created_at: datetime
