from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    currency = Column(String, default="INR")

    is_new_business = Column(Boolean, default=False)

    # Only used / shown for new businesses with no historical data yet.
    # These are explicitly labeled "estimated assumption" everywhere in the UI.
    expected_price = Column(Float, nullable=True)
    expected_monthly_customers = Column(Float, nullable=True)
    estimated_variable_cost_per_customer = Column(Float, nullable=True)
    estimated_fixed_cost = Column(Float, nullable=True)
    estimated_marketing_spend = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="businesses")
    data_records = relationship("BusinessData", back_populates="business", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="business", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="business", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="business", cascade="all, delete-orphan")
