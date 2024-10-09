import logging
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from app.database.database import init_db
from app.api.stock_routes import router as stock_router
from app.api.user_routes import router as user_router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.debug(f"Incoming request: {request.method} {request.url}")
        if request.method == "POST":
            body = await request.body()
            logger.debug(f"Payload: {body.decode('utf-8')}")
        response = await call_next(request)
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(LogMiddleware)
app.include_router(stock_router)
app.include_router(user_router)
