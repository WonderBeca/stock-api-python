from fastapi import FastAPI
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from database import init_db
from api.stock_routes import router as stock_router

app = FastAPI()

@app.middleware("http")
async def lifespan(request: Request):
    await init_db()
    yield 

app.include_router(stock_router)
