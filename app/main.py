from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.database import init_db
from app.api.stock_routes import router as stock_router
from app.api.auth_routes import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(stock_router)
app.include_router(auth_router)
