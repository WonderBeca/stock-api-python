from sqlalchemy import Column, String, Integer, Float, Date, JSON
from app.database.database import Base

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True)
    purchased_amount = Column(Integer)
    purchased_status = Column(String)
    request_data = Column(Date)
    company_code = Column(String)
    company_name = Column(String)
    stock_values = Column(JSON)
    performance_data = Column(JSON)
    competitors = Column(JSON)
