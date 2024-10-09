from sqlalchemy import Column, String, Integer, Date, JSON, UUID, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.database.database import Base
from datetime import datetime


class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_data = Column(Date)
    company_code = Column(String)
    company_name = Column(String)
    stock_values = Column(JSON)
    performance_data = Column(JSON)
    competitors = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now)
    purchases = relationship("StockPurchase", back_populates="stock")

class StockPurchase(Base):
    __tablename__ = 'stock_purchases'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    stock_id = Column(UUID(as_uuid=True), ForeignKey('stocks.id'), nullable=False)
    amount_stock = Column(Integer, nullable=False)
    purchase_date = Column(DateTime, default=datetime.now)
    stock_symbol = Column(String)
    status = Column(String, default='BUY')
    stock = relationship("Stock", back_populates="purchases")
