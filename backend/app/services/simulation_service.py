from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models.business import Business
from ..models.simulation import Simulation, SimulationAssumption, SimulationResult
from ..schemas.simulation import SimulationCreateRequest
from ..simulation.data_analysis import analyze_historical_data
from .business_service import get_active_records
from ..simulation.engine import (
    build_input_from_historical,
    build_input_for_new_business,
    run_simulation,
)


class InsufficientDataError(Exception):
    pass


MIN_RECORDS_FOR_HISTORICAL_SIM = 3  # below this we require New Business Mode explicitly


def create_simulation(db: Session, business_id: int, payload: SimulationCreateRequest) -> Simulation:
    sim = Simulation(
        business_id=business_id,
        title=payload.title,
        decision_text=payload.decision_text,
        decision_type=payload.decision_type,
        decision_params=payload.decision_params,
        time_horizon=payload.time_horizon,
        seed=payload.seed,
        iterations=settings.SIMULATION_ITERATIONS,
        status="pending",
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def run_and_store_simulation(db: Session, sim: Simulation, business: Business) -> Simulation:
    sim.status = "running"
    db.commit()

    rows = get_active_records(db, business.id)
    records = [
        {
            "date": r.date, "revenue": r.revenue, "customers": r.customers,
            "orders": r.orders, "variable_cost": r.variable_cost, "fixed_cost": r.fixed_cost,
            "marketing_spend": r.marketing_spend, "other_cost": r.other_cost,
        }
        for r in rows
    ]
    stats = analyze_historical_data(records)

    try:
        if stats.n_records >= MIN_RECORDS_FOR_HISTORICAL_SIM:
            sim_in = build_input_from_historical(
                stats, sim.decision_type, sim.decision_params,
                time_horizon_months=sim.time_horizon, seed=sim.seed, iterations=sim.iterations,
            )
            sim.is_new_business_mode = False
            data_source_note = f"Based on {stats.n_records} historical business records."
        elif business.is_new_business or stats.n_records == 0:
            required = [
                business.expected_monthly_customers, business.expected_price,
                business.estimated_variable_cost_per_customer, business.estimated_fixed_cost,
                business.estimated_marketing_spend,
            ]
            if any(v is None for v in required):
                raise InsufficientDataError(
                    "Insufficient business data for a reliable historical-data simulation, and "
                    "New Business Mode assumptions are incomplete. Please upload data or complete "
                    "your business profile's estimated assumptions."
                )
            sim_in = build_input_for_new_business(
                sim.decision_type, sim.decision_params,
                expected_customers=business.expected_monthly_customers,
                expected_price=business.expected_price,
                estimated_variable_cost_per_customer=business.estimated_variable_cost_per_customer,
                estimated_fixed_cost=business.estimated_fixed_cost,
                estimated_marketing_spend=business.estimated_marketing_spend,
                time_horizon_months=sim.time_horizon, seed=sim.seed, iterations=sim.iterations,
            )
            sim.is_new_business_mode = True
            data_source_note = "New Business Mode — based on your estimated assumptions, not historical data."
        else:
            raise InsufficientDataError(
                f"Insufficient business data for a reliable historical-data simulation "
                f"({stats.n_records} record(s) found, {MIN_RECORDS_FOR_HISTORICAL_SIM} minimum required). "
                "Upload more data or switch to New Business Mode."
            )
    except InsufficientDataError:
        sim.status = "failed"
        db.commit()
        raise

    output = run_simulation(sim_in)

    for a in sim_in.assumptions:
        db.add(SimulationAssumption(
            simulation_id=sim.id, parameter=a.parameter, value=a.value,
            source=a.source, confidence=a.confidence,
        ))

    for s in output.scenarios:
        db.add(SimulationResult(
            simulation_id=sim.id, scenario=s.scenario, revenue=s.revenue, profit=s.profit,
            growth_pct=s.growth_pct, risk_score=output.risk_score,
            confidence_score=output.confidence_score,
        ))

    sim.status = "completed"
    sim.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sim)

    # Stash transient (non-persisted-as-columns) explainability fields for the router to read once.
    sim._transient_output = output
    sim._transient_data_source_note = data_source_note
    return sim
