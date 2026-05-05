from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TradeRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    quantity: int = Field(gt=0)
    side: Literal["BUY", "SELL"]


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    symbol: str
    side: str
    quantity: int
    price: float
    executed_at: datetime
