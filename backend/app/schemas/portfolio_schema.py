from typing import List
from pydantic import BaseModel, ConfigDict


class HoldingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    quantity: int
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PortfolioSnapshot(BaseModel):
    user_id: int
    cash_balance: float
    holdings_value: float
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    holdings: List[HoldingOut]
