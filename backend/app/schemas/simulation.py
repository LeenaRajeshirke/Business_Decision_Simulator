from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class DecisionParseRequest(BaseModel):
    decision_text: str


class DecisionParseResponse(BaseModel):
    decision_type: str
    decision_params: dict[str, Any]
    parsed_by: str  # "ai" | "fallback_rules"
    note: Optional[str] = None  # e.g. "AI unavailable — parsed using rule-based fallback"


class SimulationCreateRequest(BaseModel):
    business_id: int
    title: str
    decision_text: str
    decision_type: str
    decision_params: dict[str, Any]
    time_horizon: int = 3
    seed: Optional[int] = None


class AssumptionOut(BaseModel):
    parameter: str
    value: float
    source: str
    confidence: str

    class Config:
        from_attributes = True


class ScenarioOut(BaseModel):
    scenario: str
    revenue: float
    profit: float
    growth_pct: float
    risk_score: float
    confidence_score: float

    class Config:
        from_attributes = True


class SimulationResponse(BaseModel):
    id: int
    business_id: int
    title: str
    decision_text: str
    decision_type: str
    decision_params: dict[str, Any]
    time_horizon: int
    status: str
    seed: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SimulationResultsResponse(BaseModel):
    simulation: SimulationResponse
    assumptions: list[AssumptionOut]
    scenarios: list[ScenarioOut]
    risk_level: str
    risk_factors: dict[str, float]
    confidence_level: str
    confidence_reasons: list[str]
    positive_factors: list[str]
    negative_factors: list[str]
    uncertain_factors: list[str]
    recommendation: str
    recommendation_reason: str
    methodology: str
    data_source_note: str  # e.g. "Based on 36 historical records" / "New Business Mode — estimated assumptions"
