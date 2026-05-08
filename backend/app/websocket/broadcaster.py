import asyncio
import logging
from typing import Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import User
from app.services.pricing_service import get_price_provider, Quote
from app.services.portfolio_service import build_snapshot
from app.websocket.connection import manager

log = logging.getLogger("broadcaster")


def _quote_to_dict(q: Quote) -> dict:
    return {
        "symbol": q.symbol,
        "price": q.price,
        "previous_close": q.previous_close,
        "change_pct": q.change_pct,
        "timestamp": q.timestamp,
    }


async def push_portfolio_update(user_id: int) -> None:
    """Build a fresh snapshot for the given user and broadcast it.
    Called on each price tick and immediately after a trade."""
    provider = get_price_provider()
    quotes = await provider.get_quotes(settings.tracked_symbols)
    with SessionLocal() as db:
        snapshot = await build_snapshot(db, user_id, quotes)
    await manager.broadcast({
        "type": "portfolio_update",
        "snapshot": snapshot.model_dump(),
    })


async def _ticker_loop(stop_event: asyncio.Event) -> None:
    provider = get_price_provider()
    interval = max(0.5, settings.price_tick_seconds)

    # Resolve the demo user once; routes already guarantee it's seeded.
    with SessionLocal() as db:
        demo = db.query(User).filter(User.username == settings.demo_user_username).one_or_none()
        demo_id = demo.id if demo else None

    while not stop_event.is_set():
        try:
            tick_method = getattr(provider, "tick_all", None)
            if tick_method is None:
                quotes = await provider.get_quotes(settings.tracked_symbols)
            else:
                quotes = await tick_method()

            await manager.broadcast({
                "type": "price_update",
                "quotes": [_quote_to_dict(q) for q in quotes.values()],
            })

            if demo_id is not None and manager.active_count > 0:
                await push_portfolio_update(demo_id)

        except Exception as e:
            log.exception("ticker loop error: %s", e)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


_task: Optional[asyncio.Task] = None
_stop: Optional[asyncio.Event] = None


def start_broadcaster() -> None:
    global _task, _stop
    if _task is not None and not _task.done():
        return
    _stop = asyncio.Event()
    _task = asyncio.create_task(_ticker_loop(_stop), name="price-broadcaster")


async def stop_broadcaster() -> None:
    global _task, _stop
    if _stop is not None:
        _stop.set()
    if _task is not None:
        try:
            await asyncio.wait_for(_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            _task.cancel()
    _task = None
    _stop = None
