import os
from contextlib import asynccontextmanager
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    # If python-dotenv isn't installed or .env doesn't exist, we still allow
    # environment variables to be provided by the host.
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.routes.auth_routes import router as auth_router
from app.routes.competitor_routes import router as competitor_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.festival_routes import router as festival_router
from app.routes.inventory_routes import router as inventory_router
from app.routes.pricing_routes import router as pricing_router
from app.routes.sku_routes import router as sku_router


def _frontend_origins() -> list[str]:
    env_value = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:3001")
    return [origin.strip() for origin in env_value.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="AI Pricing Engine API",
    version="1.0.0",
    description="Pricing, competitor intelligence, and inventory planning backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sku_router)
app.include_router(pricing_router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(competitor_router)
app.include_router(festival_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
