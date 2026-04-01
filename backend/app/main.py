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

from app.db.mongo import close_mongo_connection, connect_to_mongo, get_database
from app.routes.competitor_routes import router as competitor_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.festival_routes import router as festival_router
from app.routes.inventory_routes import router as inventory_router
from app.routes.pricing_routes import router as pricing_router
from app.routes.sku_routes import router as sku_router
from app.utils.helpers import default_seed_payload


def _frontend_origins() -> list[str]:
    env_value = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:3001")
    return [origin.strip() for origin in env_value.split(",") if origin.strip()]


async def _seed_if_empty() -> None:
    db = await get_database()

    skus_count = await db.skus.count_documents({})
    listings_count = await db.listings.count_documents({})

    should_reset = False
    if skus_count == 0:
        should_reset = True
    elif listings_count == 0:
        # Legacy flat model detected; replace with normalized seed for phase-1.
        should_reset = True

    if not should_reset:
        return

    for collection_name in ["organizations", "users", "skus", "listings", "competitors", "festivals"]:
        await db[collection_name].delete_many({})

    payload = default_seed_payload()
    for collection_name, docs in payload.items():
        if docs:
            await db[collection_name].insert_many(docs)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    await _seed_if_empty()
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

app.include_router(sku_router)
app.include_router(pricing_router)
app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(competitor_router)
app.include_router(festival_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
