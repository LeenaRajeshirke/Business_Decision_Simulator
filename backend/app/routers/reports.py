from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.simulation import Simulation
from ..models.user import User
from ..routers.simulations import _build_results_response, _authorize_business
from ..utils.deps import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{simulation_id}")
def get_report(simulation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    A 'report' is a read-only view assembled from a completed simulation's real,
    stored results — assumptions, scenarios, risk, confidence, recommendation.
    PDF export can be layered on top of this same payload later (e.g. with the
    project's `pdf` skill / WeasyPrint) without changing what data is shown.
    """
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    _authorize_business(db, user, sim.business_id)
    if sim.status != "completed":
        raise HTTPException(status_code=409, detail="Report is only available for completed simulations.")
    return _build_results_response(db, sim)
