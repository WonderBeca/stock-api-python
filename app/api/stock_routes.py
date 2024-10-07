# app/api/stock_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.stock_model import Stock
from app.schemas.stock_schema import StockResponse
from app.services.stock_service import get_stock_by_symbol
from app.services.scraper_service import scrape_marketwatch_data
import os

router = APIRouter()

@router.get("/stock/{stock_symbol}")
async def read_stock(stock_symbol: str, db: AsyncSession = Depends(get_db)):
    stock = await get_stock_by_symbol(db, stock_symbol)
    if not stock:
        marketwatch_data = scrape_marketwatch_data(stock_symbol)
        
        if not marketwatch_data:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stock = StockResponse(**marketwatch_data)
        
    return stock
