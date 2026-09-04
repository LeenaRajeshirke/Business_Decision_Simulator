from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    type = Column(String, nullable=False)       # trend | risk | opportunity
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="info")   # info | warning | critical
    source = Column(String, nullable=False)     # e.g. "Based on the last 90 days of business data."

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="insights")
