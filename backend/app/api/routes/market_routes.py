from typing import List
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.services.pricing_service import get_price_provider
from app.utils.helpers import normalize_symbol

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/symbols")
def list_symbols() -> List[str]:
    return list(settings.tracked_symbols)


@router.get("/quotes")
async def get_all_quotes():
    provider = get_price_provider()
    quotes = await provider.get_quotes(settings.tracked_symbols)
    return [
        {
            "symbol": q.symbol,
            "price": q.price,
            "previous_close": q.previous_close,
            "change_pct": q.change_pct,
            "timestamp": q.timestamp,
        }
        for q in quotes.values()
    ]


@router.get("/history/{symbol}")
def get_history(symbol: str, limit: int = Query(default=60, ge=1, le=240)):
    provider = get_price_provider()
    sym = normalize_symbol(symbol)
    points = provider.history(sym, limit=limit)
    if not points:
        raise HTTPException(status_code=404, detail=f"no history for {sym}")
    return [
        {"symbol": p.symbol, "price": p.price, "timestamp": p.timestamp}
        for p in points
    ]
