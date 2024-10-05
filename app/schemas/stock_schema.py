# app/schemas/stock_schema.py

from pydantic import BaseModel

class StockBase(BaseModel):
    name: str
    price: int

class StockCreate(StockBase):
    pass

class Stock(StockBase):
    id: int

    class Config:
        orm_mode = True
