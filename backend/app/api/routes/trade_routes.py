from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User, Trade
from app.schemas.trade_schema import TradeRequest, TradeOut
from app.services.pricing_service import get_price_provider
from app.services.trading_service import execute_trade, TradeError
from app.utils.helpers import normalize_symbol

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("", response_model=TradeOut, status_code=201)
async def place_trade(
    body: TradeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradeOut:
    provider = get_price_provider()
    symbol = normalize_symbol(body.symbol)
    quote = await provider.get_quote(symbol)
    if quote.price <= 0:
        raise HTTPException(status_code=502, detail=f"no live price for {symbol}")

    try:
        trade = execute_trade(
            db,
            user_id=user.id,
            symbol=symbol,
            side=body.side,
            quantity=body.quantity,
            price=float(quote.price),
        )
    except TradeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return TradeOut.model_validate(trade)


@router.get("", response_model=List[TradeOut])
def list_trades(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=500),
) -> List[TradeOut]:
    rows = (
        db.query(Trade)
        .filter(Trade.user_id == user.id)
        .order_by(Trade.executed_at.desc())
        .limit(limit)
        .all()
    )
    return [TradeOut.model_validate(r) for r in rows]
