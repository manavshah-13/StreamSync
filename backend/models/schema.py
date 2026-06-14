import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, Boolean, ForeignKey, Numeric, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    onboarding_preferences: Mapped[Optional["OnboardingPreferences"]] = relationship(
        "OnboardingPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    base_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    demand_velocity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pricing_histories: Mapped[List["PricingHistory"]] = relationship(
        "PricingHistory", back_populates="product", cascade="all, delete-orphan"
    )

class PricingHistory(Base):
    __tablename__ = "pricing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    old_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    new_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="pricing_histories")

class FairnessLog(Base):
    __tablename__ = "fairness_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    metric_scanned: Mapped[str] = mapped_column(String, nullable=False)
    bias_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    variance_score: Mapped[float] = mapped_column(Float, nullable=False)
    operational_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    variant_a_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    variant_b_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    # Relationships
    results: Mapped[List["ExperimentResult"]] = relationship(
        "ExperimentResult", back_populates="experiment", cascade="all, delete-orphan"
    )

class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), index=True, nullable=False)
    variant_group: Mapped[str] = mapped_column(String, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[float] = mapped_column(Numeric, default=0.0, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True, nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="results")

class OnboardingPreferences(Base):
    __tablename__ = "onboarding_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    age_group: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interests: Mapped[Optional[List[str]]] = mapped_column(JSON().with_variant(ARRAY(String), "postgresql"), nullable=True)
    shopping_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="onboarding_preferences")

