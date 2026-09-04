"""
Standalone tests for the simulation engine. These import ONLY numpy/pandas/scipy/
scikit-learn — no FastAPI/SQLAlchemy/DB required — so they can run in any plain
Python 3.12 environment, including this sandbox.

Run with:  python3 backend/tests/test_simulation_engine.py
(or, where pytest is installed:  pytest backend/tests/test_simulation_engine.py -v)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from app.simulation.data_analysis import analyze_historical_data
from app.simulation.engine import (
    build_input_from_historical,
    build_input_for_new_business,
    run_simulation,
)

PASS, FAIL = [], []


def check(name, cond):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'} - {name}")


def make_sample_records(n=36, seed=7, growth=0.01, price=250.0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-08-01", periods=n, freq="MS")
    customers = 400 * (1 + growth) ** np.arange(n) * rng.lognormal(0, 0.08, n)
    revenue = customers * price * rng.lognormal(0, 0.05, n)
    variable_cost = revenue * 0.42 * rng.lognormal(0, 0.04, n)
    fixed_cost = np.full(n, 18000.0) * rng.lognormal(0, 0.02, n)
    marketing_spend = np.full(n, 6000.0) * rng.lognormal(0, 0.1, n)
    records = []
    for i in range(n):
        records.append({
            "date": dates[i], "revenue": float(revenue[i]), "customers": float(customers[i]),
            "orders": float(customers[i]), "variable_cost": float(variable_cost[i]),
            "fixed_cost": float(fixed_cost[i]), "marketing_spend": float(marketing_spend[i]),
            "other_cost": 0.0,
        })
    return records


def test_no_data_gives_zero_quality_and_no_ml():
    stats = analyze_historical_data([])
    check("empty data -> n_records == 0", stats.n_records == 0)
    check("empty data -> data_quality_score == 0", stats.data_quality_score == 0.0)
    check("empty data -> not sufficient_for_ml", stats.sufficient_for_ml is False)


def test_historical_analysis_reflects_real_input():
    records = make_sample_records(n=36)
    stats = analyze_historical_data(records)
    df = pd.DataFrame(records)
    check("avg_revenue matches manual mean", abs(stats.avg_revenue - df["revenue"].mean()) < 1e-6)
    check("n_records correct", stats.n_records == 36)
    check("36 months of good data -> sufficient_for_ml", stats.sufficient_for_ml is True)
    check("demand_elasticity computed (>=6 records)", stats.demand_elasticity is not None)


def test_pricing_simulation_no_negative_values():
    records = make_sample_records(n=36)
    stats = analyze_historical_data(records)
    sim_in = build_input_from_historical(
        stats, decision_type="pricing", decision_params={"price_change_pct": 0.10}, seed=42, iterations=5000,
    )
    out = run_simulation(sim_in)
    check("no negative revenue samples", bool(np.all(out.revenue_samples >= 0)))
    check("no negative customer samples", bool(np.all(out.customer_samples >= 0)))
    check("scenario ordering: conservative <= expected <= optimistic (profit)",
          out.scenarios[0].profit <= out.scenarios[1].profit <= out.scenarios[2].profit)
    check("risk_score within [0,100]", 0 <= out.risk_score <= 100)
    check("confidence_score within [0,100]", 0 <= out.confidence_score <= 100)
    check("recommendation is one of the allowed set",
          out.recommendation in {"Proceed", "Proceed cautiously", "Gather more data",
                                  "Test on a smaller scale", "Avoid for now"})


def test_reproducibility_with_seed():
    records = make_sample_records(n=36)
    stats = analyze_historical_data(records)
    sim_in_a = build_input_from_historical(stats, "pricing", {"price_change_pct": 0.10}, seed=123, iterations=4000)
    sim_in_b = build_input_from_historical(stats, "pricing", {"price_change_pct": 0.10}, seed=123, iterations=4000)
    out_a = run_simulation(sim_in_a)
    out_b = run_simulation(sim_in_b)
    check("same seed -> identical expected profit", out_a.scenarios[1].profit == out_b.scenarios[1].profit)
    check("same seed -> identical risk score", out_a.risk_score == out_b.risk_score)


def test_new_business_mode_lower_confidence_and_labeled():
    sim_in = build_input_for_new_business(
        decision_type="pricing", decision_params={"price_change_pct": 0.05},
        expected_customers=200, expected_price=180,
        estimated_variable_cost_per_customer=70, estimated_fixed_cost=8000,
        estimated_marketing_spend=2000, seed=99,
    )
    out = run_simulation(sim_in)
    check("new business -> elasticity flagged as estimated", sim_in.elasticity_is_estimated is True)
    check("new business -> confidence reasons mention New Business Mode",
          any("New Business Mode" in r for r in out.confidence_reasons))
    check("new business -> confidence score is capped lower (<70)", out.confidence_score < 70)


def test_insufficient_data_flag_for_short_history():
    records = make_sample_records(n=3)
    stats = analyze_historical_data(records)
    check("3 records -> not sufficient_for_ml", stats.sufficient_for_ml is False)
    check("3 records -> demand_elasticity is None (not enough data to estimate)", stats.demand_elasticity is None)


if __name__ == "__main__":
    test_no_data_gives_zero_quality_and_no_ml()
    test_historical_analysis_reflects_real_input()
    test_pricing_simulation_no_negative_values()
    test_reproducibility_with_seed()
    test_new_business_mode_lower_confidence_and_labeled()
    test_insufficient_data_flag_for_short_history()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        sys.exit(1)
