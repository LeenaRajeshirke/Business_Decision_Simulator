from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)
    decision_text = Column(Text, nullable=False)          # original natural-language input
    decision_type = Column(String, nullable=False)         # pricing | marketing | hiring | ...
    decision_params = Column(JSON, nullable=False)          # structured params (post AI-extraction, user-edited)
    time_horizon = Column(Integer, default=3)               # months
    status = Column(String, default="pending")              # pending | running | completed | failed

    seed = Column(Integer, nullable=True)
    iterations = Column(Integer, default=10000)
    is_new_business_mode = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="simulations")
    assumptions = relationship("SimulationAssumption", back_populates="simulation", cascade="all, delete-orphan")
    results = relationship("SimulationResult", back_populates="simulation", cascade="all, delete-orphan")


class SimulationAssumption(Base):
    __tablename__ = "simulation_assumptions"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)

    parameter = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String, nullable=False)      # historical | estimated | user_input
    confidence = Column(String, nullable=False)  # high | medium | low

    simulation = relationship("Simulation", back_populates="assumptions")


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)

    scenario = Column(String, nullable=False)  # conservative | expected | optimistic
    revenue = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    growth_pct = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    simulation = relationship("Simulation", back_populates="results")
