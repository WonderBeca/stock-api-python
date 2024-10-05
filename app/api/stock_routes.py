from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.stock_model import Stock
from app.schemas.stock_schema import StockResponse, StockCreate, StockUpdate
from app.services.stock_service import create_stock, get_stock_by_symbol, update_stock_amount

router = APIRouter()

@router.get("/stock/{stock_symbol}", response_model=StockResponse)
def get_stock(stock_symbol: str, db: Session = Depends(get_db)):
    stock = get_stock_by_symbol(db, stock_symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock

@router.post("/stock/{stock_symbol}")
def update_stock(stock_symbol: str, stock_update: StockUpdate, db: Session = Depends(get_db)):
    stock = update_stock_amount(db, stock_symbol, stock_update.purchased_amount)
    return {"message": f"{stock_update.purchased_amount} units of stock {stock_symbol} were added to your stock record"}
