from typing import Dict, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, PortfolioHolding
from app.schemas.portfolio_schema import HoldingOut, PortfolioSnapshot
from app.services.pricing_service import Quote
from app.utils.calculations import holding_metrics, total_pnl_pct
from app.utils.helpers import round_money


async def build_snapshot(
    db: Session,
    user_id: int,
    quotes: Dict[str, Quote],
) -> PortfolioSnapshot:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError(f"user {user_id} not found")

    holdings_rows: List[PortfolioHolding] = (
        db.query(PortfolioHolding)
        .filter(PortfolioHolding.user_id == user_id, PortfolioHolding.quantity > 0)
        .all()
    )

    holdings_out: List[HoldingOut] = []
    holdings_value = 0.0

    for h in holdings_rows:
        quote = quotes.get(h.symbol)
        current_price = float(quote.price) if quote else float(h.average_cost)
        m = holding_metrics(h.quantity, float(h.average_cost), current_price)
        holdings_value += m.market_value
        holdings_out.append(
            HoldingOut(
                symbol=h.symbol,
                quantity=h.quantity,
                average_cost=round_money(float(h.average_cost), 4),
                current_price=round_money(current_price, 4),
                market_value=round_money(m.market_value),
                unrealized_pnl=round_money(m.unrealized_pnl),
                unrealized_pnl_pct=round_money(m.unrealized_pnl_pct, 4),
            )
        )

    cash = float(user.cash_balance)
    total_value = cash + holdings_value
    total_pnl = total_value - settings.demo_user_starting_cash

    return PortfolioSnapshot(
        user_id=user_id,
        cash_balance=round_money(cash),
        holdings_value=round_money(holdings_value),
        total_value=round_money(total_value),
        total_pnl=round_money(total_pnl),
        total_pnl_pct=round_money(total_pnl_pct(settings.demo_user_starting_cash, total_value), 4),
        holdings=holdings_out,
    )
