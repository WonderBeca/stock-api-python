# app/services/stock_service.py

from sqlalchemy.orm import Session
from models.stock_model import Stock
from schemas.stock_schema import StockCreate

class StockService:
    @staticmethod
    def create_stock(db: Session, stock: StockCreate):
        db_stock = Stock(name=stock.name, price=stock.price)
        db.add(db_stock)
        db.commit()
        db.refresh(db_stock)
        return db_stock

    @staticmethod
    def get_stock(db: Session, stock_id: int):
        return db.query(Stock).filter(Stock.id == stock_id).first()
