# app/api/stock_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.stock_service import StockService
from schemas.stock_schema import StockCreate, Stock

router = APIRouter()

@router.post("/stocks/", response_model=Stock)
async def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    return StockService.create_stock(db=db, stock=stock)

@router.get("/stocks/{stock_id}", response_model=Stock)
async def read_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = StockService.get_stock(db=db, stock_id=stock_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock
