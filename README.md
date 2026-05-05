# Trading Simulation Engine

A small stock trading simulator I'm building to practice the kind of system you'd actually find on a trading desk. Live prices come in, orders go out, and the portfolio recalculates itself the moment anything moves.

It's a single-page dashboard. You watch tickers update in real time, hit buy or sell, and your PnL changes instantly. No login, no fluff.

## What's under the hood

Backend is FastAPI on Python 3.11. SQLAlchemy talks to Postgres, Pydantic handles validation, and a WebSocket pushes price and portfolio updates to the browser so nothing has to be polled.

Frontend is React with Vite, and Recharts draws the price chart. Dark theme, green for gains, red for losses, that's about as fancy as it gets.

For market data there are two modes. The default is a simulated price engine that does a small random walk on each ticker every few seconds, which is honestly better for development because you don't burn through API quota every time you reload. Flip a single env var and it pulls real quotes from Alpha Vantage instead.

Everything runs in Docker Compose at the end. Backend, Postgres, frontend, one command.

## Project layout

```
trading-simulation-engine/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/         # config + db connection
│   │   ├── models/       # SQLAlchemy: User, Trade, Portfolio
│   │   ├── schemas/      # Pydantic request/response shapes
│   │   ├── services/     # the actual logic (pricing, trading, portfolio)
│   │   ├── api/routes/   # REST endpoints
│   │   ├── websocket/    # connection manager + broadcaster
│   │   └── utils/        # PnL math, helpers
│   ├── requirements.txt
│   └── .env              # gitignored, copy from .env.example
├── frontend/
│   └── src/
│       ├── components/   # MarketPrices, Portfolio, PriceChart, TradePanel
│       ├── pages/        # Dashboard
│       └── services/     # api client + websocket hook
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
└── docker-compose.yml
```

## How the pieces fit

The pricing service ticks on its own. Every few seconds it produces a fresh quote for each tracked symbol and hands it to the WebSocket manager, which fans it out to anyone connected. When you place a trade, the trading service checks your cash, writes a `Trade` row, updates your `Portfolio` row, and then broadcasts a portfolio update on the same socket. The frontend doesn't have to ask for anything, it just listens.

PnL math lives in `utils/calculations.py` so it's easy to test in isolation. Average cost, unrealized PnL, total portfolio value, all in one place.

## Running it

Setup notes will land here as the phases come together. Once Docker is wired up at the end, the goal is `docker compose up` and you're trading.

## A note on the user model

This is a single-user demo, but every table still carries a `user_id` column. That way the schema is ready for multi-user without ripping anything up. You'd just bolt auth on top.
