from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import (
    auth_router,
    cafe_links_router,
    cafe_requests_router,
    cafes_router,
    deadlines_router,
    health_router,
    menu_router,
    orders_router,
    recommendations_router,
    summaries_router,
    user_requests_router,
    users_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Lunch Order Bot API",
    description="Backend API for Telegram lunch ordering bot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(user_requests_router, prefix="/api/v1")
app.include_router(cafes_router, prefix="/api/v1")
app.include_router(cafe_links_router, prefix="/api/v1")
app.include_router(cafe_requests_router, prefix="/api/v1")
app.include_router(menu_router, prefix="/api/v1")
app.include_router(deadlines_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(summaries_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
