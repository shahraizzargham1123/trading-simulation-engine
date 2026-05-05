from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import User


def ensure_demo_user() -> None:
    with SessionLocal() as db:
        existing = db.query(User).filter(User.username == settings.demo_user_username).one_or_none()
        if existing is None:
            db.add(User(
                username=settings.demo_user_username,
                cash_balance=settings.demo_user_starting_cash,
            ))
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_demo_user()
    yield


app = FastAPI(title="Trading Simulation Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "price_source": settings.price_source}
