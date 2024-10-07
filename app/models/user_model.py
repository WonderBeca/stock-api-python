from sqlalchemy import Column, Integer, String
from app.database.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
