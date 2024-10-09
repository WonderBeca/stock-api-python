from sqlalchemy import Column, String, UUID
from app.database.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4())
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
