from sqlalchemy.orm import Session

from app.models import User, Trade, TradeSide, PortfolioHolding
from app.utils.calculations import new_average_cost
from app.utils.helpers import normalize_symbol


class TradeError(ValueError):
    """Raised when a trade is rejected for business reasons (insufficient
    cash, insufficient shares, bad input)."""


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise TradeError(f"user {user_id} not found")
    return user


def _get_or_create_holding(db: Session, user_id: int, symbol: str) -> PortfolioHolding:
    holding = (
        db.query(PortfolioHolding)
        .filter(PortfolioHolding.user_id == user_id, PortfolioHolding.symbol == symbol)
        .one_or_none()
    )
    if holding is None:
        holding = PortfolioHolding(user_id=user_id, symbol=symbol, quantity=0, average_cost=0)
        db.add(holding)
        db.flush()
    return holding


def execute_trade(
    db: Session,
    *,
    user_id: int,
    symbol: str,
    side: str,
    quantity: int,
    price: float,
) -> Trade:
    if quantity <= 0:
        raise TradeError("quantity must be positive")
    if price <= 0:
        raise TradeError("price must be positive")

    sym = normalize_symbol(symbol)
    side_enum = TradeSide(side.upper())

    user = _get_user(db, user_id)
    holding = _get_or_create_holding(db, user_id, sym)
    notional = quantity * price

    if side_enum is TradeSide.BUY:
        if float(user.cash_balance) < notional:
            raise TradeError(
                f"insufficient cash: need {notional:.2f}, have {float(user.cash_balance):.2f}"
            )
        holding.average_cost = new_average_cost(
            existing_qty=holding.quantity,
            existing_avg_cost=float(holding.average_cost),
            buy_qty=quantity,
            buy_price=price,
        )
        holding.quantity += quantity
        user.cash_balance = float(user.cash_balance) - notional

    else:  # SELL
        if holding.quantity < quantity:
            raise TradeError(
                f"insufficient shares: trying to sell {quantity} {sym}, hold {holding.quantity}"
            )
        holding.quantity -= quantity
        user.cash_balance = float(user.cash_balance) + notional
        if holding.quantity == 0:
            holding.average_cost = 0.0

    trade = Trade(
        user_id=user_id,
        symbol=sym,
        side=side_enum,
        quantity=quantity,
        price=price,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade
