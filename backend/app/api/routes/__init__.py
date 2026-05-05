from fastapi import APIRouter

from app.api.routes.market_routes import router as market_router
from app.api.routes.portfolio_routes import router as portfolio_router
from app.api.routes.trade_routes import router as trade_router

api_router = APIRouter(prefix="/api")
api_router.include_router(market_router)
api_router.include_router(portfolio_router)
api_router.include_router(trade_router)
