# app/api/stock_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.stock_model import Stock
from app.schemas.stock_schema import StockCreate
from app.services.stock_service import get_stock_by_symbol, create_stock
from app.services.scraper_service import MarketWacth
import os

router = APIRouter()

@router.get("/stock/{stock_symbol}")
async def read_stock(stock_symbol: str, db: AsyncSession = Depends(get_db)):
    stock = await get_stock_by_symbol(db, stock_symbol)
    market_watch = MarketWacth()
    if not stock:
        # marketwatch_data = market_watch.scrape_marketwatch_data(stock_symbol)
        # test = market_watch.map_marketwatch_data_to_stock_create(marketwatch_data)
        test = {"purchased_amount":None,"status":None,"purchased_status":None,"company_code":"AAPL","stock_values":{"open":224.5,"high":225.37,"low":224.06,"close":226.8},"competitors":[{"name":"Microsoft Corp.","market_cap":{"currency":"$","value":3090000000000.0}},{"name":"Alphabet Inc. Cl C","market_cap":{"currency":"$","value":2060000000000.0}},{"name":"Alphabet Inc. Cl A","market_cap":{"currency":"$","value":2060000000000.0}},{"name":"Amazon.com Inc.","market_cap":{"currency":"$","value":1960000000000.0}},{"name":"Meta Platforms Inc.","market_cap":{"currency":"$","value":1510000000000.0}},{"name":"Samsung Electronics Co. Ltd.","market_cap":{"currency":"$","value":403650000000000.0}},{"name":"Samsung Electronics Co. Ltd. Pfd. Series 1","market_cap":{"currency":"$","value":403650000000000.0}},{"name":"Sony Group Corp.","market_cap":{"currency":"$","value":17160000000000.0}},{"name":"Dell Technologies Inc. Cl C","market_cap":{"currency":"$","value":87730000000.0}},{"name":"HP Inc.","market_cap":{"currency":"$","value":34680000000.0}}],"id":1,"request_data":null,"company_name":"Apple Inc.","performance_data":{"five_days":-3.28,"one_month":2.01,"three_months":-1.08,"year_to_date":17.05,"one_year":25.9}}
        # if not marketwatch_data:
        #     raise HTTPException(status_code=404, detail="Stock not found")
        stock = await create_stock(db, test) 
        
    return stock
