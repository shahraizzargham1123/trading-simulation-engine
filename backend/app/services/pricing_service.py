import asyncio
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

import httpx

from app.core.config import settings
from app.utils.helpers import normalize_symbol, round_money


@dataclass
class Quote:
    symbol: str
    price: float
    previous_close: float
    change_pct: float
    timestamp: float


class PriceProvider(Protocol):
    async def get_quote(self, symbol: str) -> Quote: ...
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]: ...
    def history(self, symbol: str, limit: int = 60) -> List[Quote]: ...


class SimulatedPriceProvider:
    """In-memory random-walk price engine. Keeps a rolling history per symbol
    so the chart endpoint has something real to draw."""

    _SEED_PRICES = {
        "AAPL": 175.0,
        "TSLA": 240.0,
        "GOOG": 140.0,
        "MSFT": 410.0,
        "AMZN": 180.0,
        "NVDA": 850.0,
        "META": 480.0,
    }
    _DEFAULT_SEED = 100.0
    _MAX_HISTORY = 240

    def __init__(self, symbols: List[str]) -> None:
        self._lock = asyncio.Lock()
        self._previous_close: Dict[str, float] = {}
        self._latest: Dict[str, Quote] = {}
        self._history: Dict[str, List[Quote]] = {}
        for sym in symbols:
            s = normalize_symbol(sym)
            seed = self._SEED_PRICES.get(s, self._DEFAULT_SEED)
            self._previous_close[s] = seed
            self._history[s] = []
            self._record(s, seed)

    def _record(self, symbol: str, price: float) -> Quote:
        prev = self._previous_close[symbol]
        change_pct = ((price - prev) / prev * 100.0) if prev > 0 else 0.0
        q = Quote(
            symbol=symbol,
            price=round_money(price, 4),
            previous_close=round_money(prev, 4),
            change_pct=round_money(change_pct, 4),
            timestamp=time.time(),
        )
        self._latest[symbol] = q
        h = self._history.setdefault(symbol, [])
        h.append(q)
        if len(h) > self._MAX_HISTORY:
            del h[0 : len(h) - self._MAX_HISTORY]
        return q

    def _step(self, symbol: str) -> Quote:
        last = self._latest[symbol].price
        # Geometric brownian-ish step: small drift, ~0.5% stdev per tick.
        drift = 0.0001
        shock = random.gauss(0, 0.005)
        new_price = max(0.5, last * (1 + drift + shock))
        return self._record(symbol, new_price)

    async def tick_all(self) -> Dict[str, Quote]:
        async with self._lock:
            return {sym: self._step(sym) for sym in self._latest.keys()}

    async def get_quote(self, symbol: str) -> Quote:
        s = normalize_symbol(symbol)
        if s not in self._latest:
            seed = self._SEED_PRICES.get(s, self._DEFAULT_SEED)
            self._previous_close[s] = seed
            self._record(s, seed)
        return self._latest[s]

    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        return {normalize_symbol(s): await self.get_quote(s) for s in symbols}

    def history(self, symbol: str, limit: int = 60) -> List[Quote]:
        s = normalize_symbol(symbol)
        h = self._history.get(s, [])
        return h[-limit:]


class AlphaVantagePriceProvider:
    """Calls Alpha Vantage GLOBAL_QUOTE. Free tier is 25 requests/day, so we
    cache aggressively and only refresh when a quote is older than the
    configured tick interval."""

    def __init__(self, api_key: str, base_url: str, symbols: List[str]) -> None:
        if not api_key:
            raise RuntimeError(
                "ALPHA_VANTAGE_API_KEY is empty. Set it in backend/.env or "
                "switch PRICE_SOURCE=simulated."
            )
        self._api_key = api_key
        self._base_url = base_url
        self._cache: Dict[str, Quote] = {}
        self._history: Dict[str, List[Quote]] = {normalize_symbol(s): [] for s in symbols}
        self._cache_ttl = max(settings.price_tick_seconds, 12.0)

    def _is_fresh(self, q: Quote) -> bool:
        return (time.time() - q.timestamp) < self._cache_ttl

    async def _fetch(self, symbol: str) -> Quote:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self._api_key,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(self._base_url, params=params)
            r.raise_for_status()
            data = r.json().get("Global Quote") or {}

        try:
            price = float(data.get("05. price") or 0.0)
            prev = float(data.get("08. previous close") or price)
            change_pct_raw = (data.get("10. change percent") or "0").replace("%", "").strip()
            change_pct = float(change_pct_raw or 0.0)
        except (TypeError, ValueError):
            price, prev, change_pct = 0.0, 0.0, 0.0

        q = Quote(
            symbol=symbol,
            price=round_money(price, 4),
            previous_close=round_money(prev, 4),
            change_pct=round_money(change_pct, 4),
            timestamp=time.time(),
        )
        self._cache[symbol] = q
        h = self._history.setdefault(symbol, [])
        h.append(q)
        if len(h) > 240:
            del h[0 : len(h) - 240]
        return q

    async def get_quote(self, symbol: str) -> Quote:
        s = normalize_symbol(symbol)
        cached = self._cache.get(s)
        if cached and self._is_fresh(cached):
            return cached
        return await self._fetch(s)

    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        out: Dict[str, Quote] = {}
        for sym in symbols:
            s = normalize_symbol(sym)
            out[s] = await self.get_quote(s)
        return out

    async def tick_all(self) -> Dict[str, Quote]:
        return await self.get_quotes(list(self._history.keys()))

    def history(self, symbol: str, limit: int = 60) -> List[Quote]:
        s = normalize_symbol(symbol)
        h = self._history.get(s, [])
        return h[-limit:]


_provider: Optional[object] = None


def get_price_provider():
    """Singleton factory. Picks simulated or Alpha Vantage based on env."""
    global _provider
    if _provider is not None:
        return _provider
    if settings.price_source == "alphavantage":
        _provider = AlphaVantagePriceProvider(
            api_key=settings.alpha_vantage_api_key,
            base_url=settings.alpha_vantage_base_url,
            symbols=settings.tracked_symbols,
        )
    else:
        _provider = SimulatedPriceProvider(symbols=settings.tracked_symbols)
    return _provider
