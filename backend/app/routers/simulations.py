from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai.decision_parser import parse_decision
from ..database import get_db
from ..models.business import Business
from ..models.simulation import Simulation, SimulationAssumption, SimulationResult
from ..models.user import User
from ..schemas.simulation import (
    DecisionParseRequest, DecisionParseResponse, SimulationCreateRequest,
    SimulationResponse, SimulationResultsResponse, AssumptionOut, ScenarioOut,
)
from ..services import business_service, simulation_service
from ..services.simulation_service import InsufficientDataError
from ..utils.deps import get_current_user

router = APIRouter(prefix="/api/simulations", tags=["simulations"])


def _authorize_business(db, user, business_id) -> Business:
    business = business_service.get_business_or_404(db, user.id, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.post("/parse-decision", response_model=DecisionParseResponse)
def parse_decision_text(payload: DecisionParseRequest, user: User = Depends(get_current_user)):
    result = parse_decision(payload.decision_text)
    return DecisionParseResponse(
        decision_type=result.decision_type,
        decision_params=result.decision_params,
        parsed_by=result.parsed_by,
        note=result.note,
    )


@router.post("", response_model=SimulationResponse, status_code=201)
def create_simulation(
    payload: SimulationCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _authorize_business(db, user, payload.business_id)
    return simulation_service.create_simulation(db, payload.business_id, payload)


@router.get("", response_model=list[SimulationResponse])
def list_simulations(
    business_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _authorize_business(db, user, business_id)
    return (
        db.query(Simulation)
        .filter(Simulation.business_id == business_id)
        .order_by(Simulation.created_at.desc())
        .all()
    )


@router.get("/{simulation_id}", response_model=SimulationResponse)
def get_simulation(
    simulation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    _authorize_business(db, user, sim.business_id)
    return sim


@router.post("/{simulation_id}/run", response_model=SimulationResultsResponse)
def run_simulation_endpoint(
    simulation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    business = _authorize_business(db, user, sim.business_id)

    try:
        sim = simulation_service.run_and_store_simulation(db, sim, business)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return _build_results_response(db, sim)


@router.get("/{simulation_id}/results", response_model=SimulationResultsResponse)
def get_results(
    simulation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    _authorize_business(db, user, sim.business_id)
    if sim.status != "completed":
        raise HTTPException(status_code=409, detail=f"Simulation status is '{sim.status}', not completed.")
    return _build_results_response(db, sim)


def _build_results_response(db: Session, sim: Simulation) -> SimulationResultsResponse:
    assumptions = db.query(SimulationAssumption).filter(SimulationAssumption.simulation_id == sim.id).all()
    results = db.query(SimulationResult).filter(SimulationResult.simulation_id == sim.id).all()

    if not results:
        raise HTTPException(status_code=500, detail="Simulation completed but no results were stored.")

    risk_score = results[0].risk_score
    risk_level = "Low" if risk_score < 33 else ("Medium" if risk_score < 66 else "High")
    confidence_score = results[0].confidence_score
    confidence_level = "High" if confidence_score >= 66 else ("Medium" if confidence_score >= 40 else "Low")

    output = getattr(sim, "_transient_output", None)
    data_source_note = getattr(
        sim, "_transient_data_source_note",
        "New Business Mode — based on your estimated assumptions." if sim.is_new_business_mode
        else "Based on stored historical business data.",
    )

    return SimulationResultsResponse(
        simulation=sim,
        assumptions=[AssumptionOut.model_validate(a) for a in assumptions],
        scenarios=[
            ScenarioOut(
                scenario=r.scenario, revenue=r.revenue, profit=r.profit,
                growth_pct=r.growth_pct, risk_score=r.risk_score, confidence_score=r.confidence_score,
            ) for r in results
        ],
        risk_level=risk_level,
        risk_factors=output.risk_factors if output else {},
        confidence_level=confidence_level,
        confidence_reasons=output.confidence_reasons if output else [],
        positive_factors=output.positive_factors if output else [],
        negative_factors=output.negative_factors if output else [],
        uncertain_factors=output.uncertain_factors if output else [],
        recommendation=output.recommendation if output else "N/A — re-run to regenerate explanation",
        recommendation_reason=output.recommendation_reason if output else "",
        methodology=output.methodology if output else "10,000-iteration Monte Carlo simulation over historical/estimated parameters.",
        data_source_note=data_source_note,
    )
