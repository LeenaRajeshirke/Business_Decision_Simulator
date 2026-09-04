from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.simulation import Simulation, SimulationResult
from ..models.user import User
from ..services import business_service
from ..utils.deps import get_current_user

router = APIRouter(prefix="/api/compare", tags=["compare"])


class CompareRequest(BaseModel):
    simulation_ids: list[int]


class CompareRow(BaseModel):
    simulation_id: int
    title: str
    decision_text: str
    expected_revenue: float | None
    expected_profit: float | None
    expected_growth_pct: float | None
    risk_score: float | None
    confidence_score: float | None


@router.post("", response_model=list[CompareRow])
def compare_simulations(
    payload: CompareRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if len(payload.simulation_ids) < 2:
        raise HTTPException(status_code=422, detail="Select at least 2 simulations to compare.")

    rows: list[CompareRow] = []
    for sim_id in payload.simulation_ids:
        sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
        if not sim:
            raise HTTPException(status_code=404, detail=f"Simulation {sim_id} not found")
        business = business_service.get_business_or_404(db, user.id, sim.business_id)
        if not business:
            raise HTTPException(status_code=403, detail=f"Not authorized for simulation {sim_id}")
        if sim.status != "completed":
            raise HTTPException(status_code=409, detail=f"Simulation {sim_id} has not completed running yet.")

        expected = (
            db.query(SimulationResult)
            .filter(SimulationResult.simulation_id == sim_id, SimulationResult.scenario == "expected")
            .first()
        )
        rows.append(CompareRow(
            simulation_id=sim.id, title=sim.title, decision_text=sim.decision_text,
            expected_revenue=expected.revenue if expected else None,
            expected_profit=expected.profit if expected else None,
            expected_growth_pct=expected.growth_pct if expected else None,
            risk_score=expected.risk_score if expected else None,
            confidence_score=expected.confidence_score if expected else None,
        ))
    return rows
