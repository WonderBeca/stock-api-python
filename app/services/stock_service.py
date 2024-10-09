import os
import time
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.stock_model import Stock, StockPurchase
from app.schemas.stock_schema import StockCreate
from app.services.scraper_service import MarketWacth

marketwatch_cache = {}
CACHE_EXPIRATION_TIME = 300


async def get_marketwatch_data(stock_symbol: str, date: str = None):
    """
    Retrieves market data for a given stock symbol from MarketWatch, using caching 
    to improve performance and reduce the number of requests to the source.

    Args:
        stock_symbol (str): The stock symbol to retrieve data for.
        date (str, optional): The date for which to retrieve the data. Defaults to None.

    Returns:
        dict or None: The market data for the specified stock symbol, or None if no data 
        could be retrieved from MarketWatch.
    """
    cache_key = f"{stock_symbol}_{date}" if date else stock_symbol
    current_time = time.time()

    # Check if the data is in the cache
    if cache_key in marketwatch_cache:
        cached_data, timestamp = marketwatch_cache[cache_key]
        if current_time - timestamp < CACHE_EXPIRATION_TIME:
            return cached_data

    market_watch = MarketWacth()
    marketwatch_data = market_watch.scrape_marketwatch_data(stock_symbol)

    if marketwatch_data:
        marketwatch_cache[cache_key] = (marketwatch_data, current_time)
    
    return marketwatch_data


def stock_dict(stock: Stock) -> dict:
    """
    Converts a Stock object to a dictionary format.

    Args:
        stock (Stock): The Stock object to convert.

    Returns:
        dict: A dictionary representation of the stock.
    """
    return {
        "id": str(stock.id),  # Convert UUID to string
        "request_data": stock.request_data.isoformat() if stock.request_data else None,  # Format date
        "company_code": stock.company_code,
        "company_name": stock.company_name,
        "stock_values": stock.stock_values,  # JSON, no need to format
        "performance_data": {
            "five_days": stock.performance_data.get("five_days"),
            "one_month": stock.performance_data.get("one_month"),
            "three_months": stock.performance_data.get("three_months"),
            "year_to_date": stock.performance_data.get("year_to_date"),
            "one_year": stock.performance_data.get("one_year")
        } if stock.performance_data else None,  # JSON performance data
        "competitors": [
            {
                "name": competitor.get("name"),
                "market_cap": {
                    "currency": competitor["market_cap"].get("currency"),
                    "value": competitor["market_cap"].get("value")
                }
            }
            for competitor in stock.competitors
        ] if stock.competitors else [],  # JSON competitors
        "timestamp": stock.timestamp.isoformat() if stock.timestamp else None,  # Format datetime
    }


async def get_stock_by_symbol(db: AsyncSession, symbol: str):
    """
    Retrieves a stock by its symbol from the database.

    Args:
        db (AsyncSession): The database session.
        symbol (str): The stock symbol to search for.

    Returns:
        Stock or None: The Stock object if found, None otherwise.
    """
    last_update_limit = datetime.utcnow() - timedelta(minutes=int(os.getenv("LAST_UPDATE", 5)))
    try:
        result = await db.execute(
            select(Stock).where(
                Stock.company_code == symbol,
                Stock.timestamp >= last_update_limit
            )
        )
        stock = result.scalars().first()
        return stock  # Return None if no stock was found

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock: {str(e)}")


async def create_stock(db: AsyncSession, stock: StockCreate) -> Stock:
    """
    Creates a new stock in the database.

    Args:
        db (AsyncSession): The database session.
        stock (StockCreate): The stock data to create.

    Returns:
        Stock: The created Stock object.
    
    Raises:
        HTTPException: If there is an error creating the stock.
    """
    try:
        db_stock = Stock(**stock)
        db.add(db_stock)
        await db.commit()
        await db.refresh(db_stock)
        return db_stock
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating stock: {str(e)}")


async def purchase_stock(db: AsyncSession, user_id: str, symbol: str, amount: float) -> list:
    """
    Records a stock purchase for a user.

    Args:
        db (AsyncSession): The database session.
        user_id (str): The ID of the user making the purchase.
        symbol (str): The stock symbol being purchased.
        amount (float): The amount of stock being purchased.

    Returns:
        list: A list of StockPurchase objects for the user.
    
    Raises:
        HTTPException: If the stock is not found or an error occurs during the purchase.
    """
    stock = await get_stock_by_symbol(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found.")

    try:
        purchase = StockPurchase(user_id=user_id, stock_id=stock.id, stock_symbol=symbol, amount_stock=amount)
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        updated_list = await get_stocks_history_by_user(db, user_id)
        return updated_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error purchasing stock: {str(e)}")


async def get_stocks_history_by_user(db: AsyncSession, user_id: str) -> list:
    """
    Retrieves the stock purchase history for a user.

    Args:
        db (AsyncSession): The database session.
        user_id (str): The ID of the user.

    Returns:
        list: A list of StockPurchase objects for the user.
    
    Raises:
        HTTPException: If there is an error retrieving the purchase history.
    """
    try:
        result = await db.execute(select(StockPurchase).where(StockPurchase.user_id == user_id))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock purchase history: {str(e)}")


async def get_stocks_total_by_user(db: AsyncSession, user_id: str) -> list:
    """
    Retrieves the total stock amounts for a user, grouped by stock symbol.

    Args:
        db (AsyncSession): The database session.
        user_id (str): The ID of the user.

    Returns:
        list: A list of tuples containing stock symbols and their total amounts.
    
    Raises:
        HTTPException: If there is an error retrieving the total amounts.
    """
    try:
        result = await db.execute(
            select(
                StockPurchase.stock_symbol,
                func.sum(
                    case(
                        (StockPurchase.status == 'BUY', StockPurchase.amount_stock),
                        (StockPurchase.status == 'SELL', -StockPurchase.amount_stock),
                        else_=0
                    )
                ).label("total_amount")
            ).where(StockPurchase.user_id == user_id)
            .group_by(StockPurchase.stock_symbol)
        )
        return result.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving total stock amounts: {str(e)}")


async def update_stock_amount(db: AsyncSession, user_id: str, stock_symbol: str, amount: float, current_amount: float) -> StockPurchase:
    """
    Updates the stock amount for a user based on their current holdings.

    Args:
        db (AsyncSession): The database session.
        user_id (str): The ID of the user.
        stock_symbol (str): The stock symbol being updated.
        amount (float): The new amount of stock.
        current_amount (float): The current amount of stock held by the user.

    Returns:
        StockPurchase: The StockPurchase object for the updated purchase.

    Raises:
        HTTPException: If the stock is not found or if an unexpected status is encountered.
    """
    stock = await get_stock_by_symbol(db, stock_symbol)
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found in user's wallet.")

    status = 'HOLD'
    calculated_amount = 0

    if current_amount != amount:
        if current_amount < amount:
            status = 'BUY'
            calculated_amount = amount - current_amount
        else:
            status = 'SELL'
            calculated_amount = current_amount - amount

    try:
        purchase = StockPurchase(
            user_id=user_id, stock_id=stock.id, stock_symbol=stock_symbol, amount_stock=calculated_amount, status=status
        )
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        return purchase
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating stock amount: {str(e)}")
