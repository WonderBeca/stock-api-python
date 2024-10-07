from sqlalchemy import Column, String, Integer, Float, Date, JSON, UUID
import uuid
from app.database.database import Base

class Competitor(Base):
    __tablename__ = 'competitors'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    market_cap = Column(JSON) 
class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_data = Column(Date)
    company_code = Column(String)
    company_name = Column(String)
    stock_values = Column(JSON)
    performance_data = Column(JSON)
    competitors = Column(JSON)
