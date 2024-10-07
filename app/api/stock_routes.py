# app/api/stock_routes.py
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.stock_model import Stock
from app.services.stock_service import get_stock_by_symbol, create_stock
from app.services.scraper_service import MarketWacth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/stock", response_class=HTMLResponse)
async def query_stock(
        request: Request,
        stock_symbol: str = Form(...),
        db: AsyncSession = Depends(get_db),
    ):
    stock = await get_stock_by_symbol(db, stock_symbol)
    market_watch = MarketWacth()
    
    if not stock:
        # Descomentar a linha abaixo para buscar dados do MarketWatch
        # marketwatch_data = market_watch.scrape_marketwatch_data(stock_symbol)
        # if not marketwatch_data:
        #     raise HTTPException(status_code=404, detail="Stock not found")
        
        # Exemplo de dados da ação
        test = {
            "purchased_amount": None,
            "status": None,
            "purchased_status": None,
            "company_code": stock_symbol.upper(),  # Use o símbolo inserido
            "stock_values": {
                "open": 224.5,
                "high": 225.37,
                "low": 224.06,
                "close": 226.8
            },
            "competitors": [
                {"name": "Microsoft Corp.", "market_cap": {"currency": "$", "value": 3090000000000.0}},
                {"name": "Alphabet Inc. Cl C", "market_cap": {"currency": "$", "value": 2060000000000.0}},
            ],
            "company_name": "Apple Inc.",
            "performance_data": {
                "five_days": -3.28,
                "one_month": 2.01,
                "three_months": -1.08,
                "year_to_date": 17.05,
                "one_year": 25.9
            }
        }
        stock = await create_stock(db, test)

    return templates.TemplateResponse("stock_search.html", {"request": request, "stock": stock})
