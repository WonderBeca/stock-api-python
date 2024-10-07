from app.models.stock_model import Stock
from app.schemas.stock_schema import StockCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_stock_by_symbol(db: AsyncSession, symbol: str):
    result = await db.execute(select(Stock).where(Stock.company_code == symbol))
    return result.scalars().first()

async def create_stock(db: AsyncSession, stock: StockCreate):
    db_stock = Stock(**stock.model_dump())
    db.add(db_stock)
    await db.commit()
    await db.refresh(db_stock)
    return db_stock

async def update_stock_amount(db: AsyncSession, symbol: str, amount: int):
    stock = await get_stock_by_symbol(db, symbol)
    if stock:
        stock.purchased_amount += amount
        await db.commit()
        await db.refresh(stock)
    return stock
