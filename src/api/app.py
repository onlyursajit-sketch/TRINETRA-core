from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.api.version import API_VERSION

load_dotenv()

from src.api.routes.health import router as health_router
from src.api.routes.market import router as market_router
from src.api.routes.signal import router as signal_router
from src.api.routes.trade import router as trade_router

app = FastAPI(
    title="TRINETRA API",
    version=API_VERSION,
    description="TRINETRA market intelligence API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(market_router)
app.include_router(signal_router)
app.include_router(trade_router)

app.include_router(health_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(signal_router, prefix="/api/v1")
app.include_router(trade_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "TRINETRA",
        "status": "running",
        "version": API_VERSION,
    }
