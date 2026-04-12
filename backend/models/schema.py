from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True)
    base_price = Column(Float)
    current_price = Column(Float)
    rating = Column(Float)
    review_count = Column(Integer)
    demand_velocity = Column(Integer)
    brand = Column(String)
    description = Column(Text)
    specs = Column(JSON)
    image = Column(String)
    color = Column(String)
    material = Column(String)
    style = Column(String)
    tags = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
