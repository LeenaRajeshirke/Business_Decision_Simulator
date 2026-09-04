from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class BusinessData(Base):
    __tablename__ = "business_data"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)

    date = Column(Date, nullable=False)
    revenue = Column(Float, nullable=False)
    customers = Column(Float, nullable=False)
    orders = Column(Float, nullable=True)
    variable_cost = Column(Float, nullable=False, default=0.0)
    fixed_cost = Column(Float, nullable=False, default=0.0)
    marketing_spend = Column(Float, nullable=False, default=0.0)
    other_cost = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="data_records")
    dataset = relationship("Dataset", back_populates="records")
