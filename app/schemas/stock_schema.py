from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel, Field

class StockPurchaseRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The amount of stock to purchase, must be greater than 0")

class StockUpdateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The new amount of stock, must be greater than 0")
    current_amount: float = Field(..., gt=0, description="The current amount of stock, must be greater than 0")

class StockQueryRequest(BaseModel):
    date: str = Field(None, description="The date for stock data, optional")

class StockValues(BaseModel):
    open: float
    high: float
    low: float
    close: float

class PerformanceData(BaseModel):
    five_days: Optional[float]
    one_month: Optional[float]
    three_months: Optional[float]
    year_to_date: Optional[float]
    one_year: Optional[float]

class Competitor(BaseModel):
    name: str
    market_cap: dict

class StockBase(BaseModel):
    company_code: str
    company_name: str
    stock_values: StockValues
    performance_data: PerformanceData
    competitors: List[Competitor]

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    purchased_amount: int

class StockResponse(StockBase):
    id: int

    class Config:
        from_attributes = True
