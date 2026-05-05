from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.schemas.portfolio_schema import PortfolioSnapshot
from app.schemas.user_schema import UserOut
from app.services.pricing_service import get_price_provider
from app.services.portfolio_service import build_snapshot

router = APIRouter(tags=["portfolio"])


@router.get("/users/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/portfolio", response_model=PortfolioSnapshot)
async def get_portfolio(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PortfolioSnapshot:
    provider = get_price_provider()
    quotes = await provider.get_quotes(settings.tracked_symbols)
    return await build_snapshot(db, user.id, quotes)
