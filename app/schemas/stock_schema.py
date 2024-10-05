from pydantic import BaseModel
from typing import List, Optional

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
    status: str
    purchased_amount: int
    purchased_status: str
    request_data: str
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
