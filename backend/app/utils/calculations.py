from dataclasses import dataclass


@dataclass(frozen=True)
class HoldingMetrics:
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


def new_average_cost(
    existing_qty: int,
    existing_avg_cost: float,
    buy_qty: int,
    buy_price: float,
) -> float:
    """Weighted average cost after a buy. Sells do not change avg cost."""
    if buy_qty <= 0:
        return existing_avg_cost
    total_qty = existing_qty + buy_qty
    if total_qty == 0:
        return 0.0
    return ((existing_qty * existing_avg_cost) + (buy_qty * buy_price)) / total_qty


def holding_metrics(quantity: int, average_cost: float, current_price: float) -> HoldingMetrics:
    market_value = quantity * current_price
    cost_basis = quantity * average_cost
    unrealized_pnl = market_value - cost_basis
    unrealized_pnl_pct = ((current_price - average_cost) / average_cost * 100.0) if average_cost > 0 else 0.0
    return HoldingMetrics(
        market_value=market_value,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
    )


def total_pnl_pct(starting_cash: float, total_value: float) -> float:
    if starting_cash <= 0:
        return 0.0
    return (total_value - starting_cash) / starting_cash * 100.0
