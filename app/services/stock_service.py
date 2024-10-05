from sqlalchemy.orm import Session
from app.models.stock_model import Stock
from app.schemas.stock_schema import StockCreate

def get_stock_by_symbol(db: Session, symbol: str):
    return db.query(Stock).filter(Stock.company_code == symbol).first()

def create_stock(db: Session, stock: StockCreate):
    db_stock = Stock(**stock.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock

def update_stock_amount(db: Session, symbol: str, amount: int):
    stock = get_stock_by_symbol(db, symbol)
    if stock:
        stock.purchased_amount += amount
        db.commit()
        db.refresh(stock)
    return stock
