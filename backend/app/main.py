from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import User
from app.websocket.connection import manager
from app.websocket.broadcaster import start_broadcaster, stop_broadcaster


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
    start_broadcaster()
    try:
        yield
    finally:
        await stop_broadcaster()


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
    return {
        "status": "ok",
        "price_source": settings.price_source,
        "ws_clients": manager.active_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # We do not expect inbound messages; receive_text keeps the
            # connection alive and detects client disconnect.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
