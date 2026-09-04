"""
Monte Carlo simulation engine.

This module NEVER calls an AI/LLM. All numbers are produced by sampling
distributions parameterized from real historical data (when available)
or from explicit, clearly-labeled user assumptions (new business mode).

Design:
  1. Build a ScenarioInput from either historical stats or manual assumptions.
  2. Sample thousands of parameter draws (Monte Carlo).
  3. Compute revenue/cost/profit per draw using an explicit accounting identity.
  4. Summarize into percentile-based Conservative / Expected / Optimistic scenarios.
  5. Compute a transparent risk score and confidence score from the resulting
     distribution and input data quality — never from vibes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np

from .data_analysis import HistoricalStats

DecisionType = Literal[
    "pricing", "marketing", "hiring", "expansion", "product_launch", "cost_reduction", "other"
]


@dataclass
class Assumption:
    parameter: str
    value: float
    source: Literal["historical", "estimated", "user_input"]
    confidence: Literal["high", "medium", "low"]


@dataclass
class SimulationInput:
    decision_type: DecisionType
    decision_params: dict  # e.g. {"price_change_pct": 0.10}
    time_horizon_months: int
    seed: Optional[int] = None
    iterations: int = 10_000

    # Baseline business economics (never fabricated — either from HistoricalStats or manual entry)
    base_customers: float = 0.0
    base_price: float = 0.0            # average order value / price per customer
    base_variable_cost_per_customer: float = 0.0
    base_fixed_cost: float = 0.0
    base_marketing_spend: float = 0.0

    # Uncertainty inputs (fractions, e.g. 0.15 = 15% coefficient of variation)
    customer_volatility: float = 0.15
    cost_volatility: float = 0.08
    demand_elasticity: Optional[float] = None   # None => use a labeled assumption band instead
    elasticity_is_estimated: bool = True         # True unless it came from >= MIN_RECORDS_FOR_ELASTICITY historical fit

    data_quality_score: float = 50.0
    is_new_business: bool = False

    assumptions: list[Assumption] = field(default_factory=list)


@dataclass
class ScenarioResult:
    scenario: Literal["conservative", "expected", "optimistic"]
    revenue: float
    profit: float
    growth_pct: float
    risk_score: float


@dataclass
class SimulationOutput:
    scenarios: list[ScenarioResult]
    risk_score: float
    risk_level: Literal["Low", "Medium", "High"]
    risk_factors: dict
    confidence_score: float
    confidence_level: Literal["High", "Medium", "Low"]
    confidence_reasons: list[str]
    revenue_samples: np.ndarray
    profit_samples: np.ndarray
    customer_samples: np.ndarray
    baseline_profit: float
    positive_factors: list[str]
    negative_factors: list[str]
    uncertain_factors: list[str]
    recommendation: str
    recommendation_reason: str
    methodology: str
    seed_used: int


DEFAULT_ELASTICITY_BY_BAND = {
    "low": -0.4,
    "medium": -1.0,
    "high": -2.0,
}


def _decision_deltas(sim_in: SimulationInput) -> tuple[float, float, float, float]:
    """
    Translate a decision + its params into expected shifts applied BEFORE Monte Carlo noise:
    returns (price_multiplier, customer_shift_multiplier, marketing_delta, fixed_cost_delta)
    """
    p = sim_in.decision_params
    price_mult = 1.0
    customer_mult = 1.0
    marketing_delta = 0.0
    fixed_delta = 0.0

    if sim_in.decision_type == "pricing":
        pct = p.get("price_change_pct", 0.0)
        price_mult = 1.0 + pct
    elif sim_in.decision_type == "marketing":
        pct = p.get("marketing_change_pct", 0.0)
        marketing_delta = sim_in.base_marketing_spend * pct
    elif sim_in.decision_type == "hiring":
        fixed_delta = p.get("monthly_salary_cost", 0.0)
        # a new hire is assumed (explicitly, as an assumption) to lift capacity/demand slightly
        customer_mult = 1.0 + p.get("expected_customer_lift_pct", 0.0)
    elif sim_in.decision_type == "expansion":
        fixed_delta = p.get("new_location_fixed_cost", 0.0)
        customer_mult = 1.0 + p.get("expected_customer_lift_pct", 0.0)
    elif sim_in.decision_type == "product_launch":
        marketing_delta = p.get("launch_marketing_spend", 0.0)
        customer_mult = 1.0 + p.get("expected_customer_lift_pct", 0.0)
    elif sim_in.decision_type == "cost_reduction":
        fixed_delta = -p.get("fixed_cost_reduction", 0.0)

    return price_mult, customer_mult, marketing_delta, fixed_delta


def run_simulation(sim_in: SimulationInput) -> SimulationOutput:
    rng_seed = sim_in.seed if sim_in.seed is not None else np.random.SeedSequence().entropy % (2**32)
    rng = np.random.default_rng(rng_seed)
    n = sim_in.iterations

    price_mult, customer_mult, marketing_delta, fixed_delta = _decision_deltas(sim_in)

    # --- Elasticity: apply demand response to price changes ---
    if sim_in.demand_elasticity is not None:
        elasticity = sim_in.demand_elasticity
    else:
        band = sim_in.decision_params.get("elasticity_band", "medium")
        elasticity = DEFAULT_ELASTICITY_BY_BAND.get(band, -1.0)

    price_change_pct = price_mult - 1.0
    demand_response = elasticity * price_change_pct  # % change in customers from price move

    # --- Sample uncertain customer counts (lognormal keeps customers > 0) ---
    base_c = max(sim_in.base_customers, 0.0)
    if base_c <= 0:
        base_c = 1.0  # avoid degenerate zero baselines; flagged via low confidence elsewhere
    mu_c = np.log(base_c * customer_mult * (1 + demand_response))
    sigma_c = max(sim_in.customer_volatility, 0.01)
    customers = rng.lognormal(mean=mu_c - 0.5 * sigma_c**2, sigma=sigma_c, size=n)
    customers = np.clip(customers, 0, None)

    # --- Sample price/order value with small noise ---
    price_noise_sigma = 0.03
    price_per_customer = sim_in.base_price * price_mult * rng.lognormal(
        mean=-0.5 * price_noise_sigma**2, sigma=price_noise_sigma, size=n
    )
    price_per_customer = np.clip(price_per_customer, 0, None)

    revenue = customers * price_per_customer
    revenue = np.clip(revenue, 0, None)

    # --- Sample costs ---
    var_cost_sigma = max(sim_in.cost_volatility, 0.01)
    variable_cost_per_customer = sim_in.base_variable_cost_per_customer * rng.lognormal(
        mean=-0.5 * var_cost_sigma**2, sigma=var_cost_sigma, size=n
    )
    variable_cost = np.clip(customers * variable_cost_per_customer, 0, None)

    fixed_cost = max(sim_in.base_fixed_cost + fixed_delta, 0.0)
    marketing_spend = max(sim_in.base_marketing_spend + marketing_delta, 0.0)

    profit = revenue - variable_cost - fixed_cost - marketing_spend

    baseline_revenue = sim_in.base_customers * sim_in.base_price
    baseline_cost = (
        sim_in.base_customers * sim_in.base_variable_cost_per_customer
        + sim_in.base_fixed_cost
        + sim_in.base_marketing_spend
    )
    baseline_profit = baseline_revenue - baseline_cost

    growth_pct = np.where(
        baseline_revenue > 0, (revenue - baseline_revenue) / baseline_revenue * 100.0, np.nan
    )

    def _pctile_scenario(name, pct):
        rev_p = float(np.percentile(revenue, pct))
        profit_p = float(np.percentile(profit, pct))
        growth_p = float(np.nanpercentile(growth_pct, pct)) if baseline_revenue > 0 else 0.0
        return ScenarioResult(
            scenario=name, revenue=rev_p, profit=profit_p, growth_pct=growth_p,
            risk_score=0.0,  # filled in below, same for all scenarios (risk is a property of the distribution)
        )

    conservative = _pctile_scenario("conservative", 10)
    expected = _pctile_scenario("expected", 50)
    optimistic = _pctile_scenario("optimistic", 90)

    # --- Risk score: volatility + downside magnitude + parameter uncertainty + data quality ---
    profit_std = float(np.std(profit))
    profit_mean = float(np.mean(profit))
    outcome_volatility = min(1.0, profit_std / (abs(profit_mean) + 1e-6)) if profit_mean != 0 else 1.0

    downside_prob = float(np.mean(profit < baseline_profit))
    downside_magnitude = float(
        max(0.0, (baseline_profit - np.percentile(profit, 10)) / (abs(baseline_profit) + 1e-6))
    ) if baseline_profit != 0 else 0.5

    param_uncertainty = 0.7 if sim_in.elasticity_is_estimated else 0.3
    data_quality_penalty = max(0.0, (100.0 - sim_in.data_quality_score) / 100.0)

    risk_score = 100.0 * np.clip(
        0.30 * outcome_volatility
        + 0.25 * downside_magnitude
        + 0.20 * downside_prob
        + 0.15 * param_uncertainty
        + 0.10 * data_quality_penalty,
        0, 1,
    )
    risk_score = round(float(risk_score), 1)
    risk_level = "Low" if risk_score < 33 else ("Medium" if risk_score < 66 else "High")

    for s in (conservative, expected, optimistic):
        s.risk_score = risk_score

    # --- Confidence score ---
    data_component = sim_in.data_quality_score / 100.0
    elasticity_component = 0.3 if sim_in.elasticity_is_estimated else 0.9
    new_business_penalty = 0.5 if sim_in.is_new_business else 1.0
    volatility_component = 1.0 - min(1.0, outcome_volatility)

    confidence_score = 100.0 * np.clip(
        (0.4 * data_component + 0.25 * elasticity_component + 0.35 * volatility_component)
        * new_business_penalty,
        0, 1,
    )
    confidence_score = round(float(confidence_score), 1)
    confidence_level = "High" if confidence_score >= 66 else ("Medium" if confidence_score >= 40 else "Low")

    confidence_reasons = []
    if sim_in.is_new_business:
        confidence_reasons.append("New Business Mode: no historical data, projections rely on your assumptions.")
    else:
        confidence_reasons.append(f"Based on {sim_in.data_quality_score:.0f}/100 historical data quality score.")
    if sim_in.elasticity_is_estimated:
        confidence_reasons.append("Demand sensitivity is an estimated assumption, not measured from data.")
    else:
        confidence_reasons.append("Demand sensitivity was estimated from your historical revenue/customer data.")

    # --- Explainability ---
    positive_factors, negative_factors, uncertain_factors = [], [], []
    if price_change_pct > 0:
        positive_factors.append("Higher price increases revenue per customer.")
        if demand_response < 0:
            negative_factors.append("Estimated demand response suggests some customer loss from the price increase.")
    elif price_change_pct < 0:
        negative_factors.append("Lower price reduces revenue per customer.")
        if demand_response > 0:
            positive_factors.append("Estimated demand response suggests more customers from the lower price.")
    if marketing_delta > 0:
        uncertain_factors.append("Additional marketing spend is assumed to convert to revenue at the historical efficiency rate; actual response may differ.")
    if fixed_delta > 0:
        negative_factors.append("This decision adds fixed costs that must be covered regardless of outcome.")
    if fixed_delta < 0:
        positive_factors.append("This decision reduces fixed costs.")
    if sim_in.elasticity_is_estimated:
        uncertain_factors.append("Demand sensitivity is an assumption band, not measured — actual response could be higher or lower.")

    # --- Recommendation ---
    if risk_score >= 66 and downside_prob > 0.4:
        recommendation = "Gather more data"
        recommendation_reason = "Risk is high and there is a substantial chance of a worse-than-current outcome; more historical data or a smaller test would improve reliability."
    elif expected.profit > baseline_profit and risk_score < 33:
        recommendation = "Proceed"
        recommendation_reason = "The expected scenario improves profit and downside risk is limited."
    elif expected.profit > baseline_profit and risk_score < 66:
        recommendation = "Proceed cautiously"
        recommendation_reason = "The expected scenario improves profit, but there is meaningful downside risk to monitor."
    elif expected.profit > baseline_profit:
        recommendation = "Test on a smaller scale"
        recommendation_reason = "The expected outcome is positive, but risk and uncertainty are high enough to warrant a limited pilot first."
    else:
        recommendation = "Avoid for now"
        recommendation_reason = "The expected scenario does not improve profit over the current baseline."

    methodology = (
        f"{sim_in.iterations:,} Monte Carlo iterations sampled customer demand, price, and cost "
        f"from distributions parameterized by your business data (or stated assumptions in New "
        f"Business Mode). Conservative/Expected/Optimistic are the 10th/50th/90th percentiles of "
        f"the resulting profit and revenue distributions — not arbitrary multipliers."
    )

    return SimulationOutput(
        scenarios=[conservative, expected, optimistic],
        risk_score=risk_score,
        risk_level=risk_level,
        risk_factors={
            "outcome_volatility": round(outcome_volatility, 3),
            "downside_probability": round(downside_prob, 3),
            "downside_magnitude": round(downside_magnitude, 3),
            "parameter_uncertainty": param_uncertainty,
            "data_quality_penalty": round(data_quality_penalty, 3),
        },
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        confidence_reasons=confidence_reasons,
        revenue_samples=revenue,
        profit_samples=profit,
        customer_samples=customers,
        baseline_profit=baseline_profit,
        positive_factors=positive_factors,
        negative_factors=negative_factors,
        uncertain_factors=uncertain_factors,
        recommendation=recommendation,
        recommendation_reason=recommendation_reason,
        methodology=methodology,
        seed_used=int(rng_seed),
    )


def build_input_from_historical(
    stats: HistoricalStats,
    decision_type: DecisionType,
    decision_params: dict,
    time_horizon_months: int = 3,
    seed: Optional[int] = None,
    iterations: int = 10_000,
) -> SimulationInput:
    if stats.n_records == 0:
        raise ValueError("No historical data available — use build_input_from_manual for New Business Mode.")

    elasticity_estimated = stats.demand_elasticity is None
    return SimulationInput(
        decision_type=decision_type,
        decision_params=decision_params,
        time_horizon_months=time_horizon_months,
        seed=seed,
        iterations=iterations,
        base_customers=stats.avg_customers or 0.0,
        base_price=stats.avg_order_value or 0.0,
        base_variable_cost_per_customer=(
            (stats.avg_variable_cost or 0.0) / stats.avg_customers if stats.avg_customers else 0.0
        ),
        base_fixed_cost=stats.avg_fixed_cost or 0.0,
        base_marketing_spend=stats.avg_marketing_spend or 0.0,
        customer_volatility=min(0.6, max(0.05, (stats.revenue_volatility or 0.15))),
        cost_volatility=min(0.4, max(0.03, (stats.cost_volatility or 0.08))),
        demand_elasticity=stats.demand_elasticity,
        elasticity_is_estimated=elasticity_estimated,
        data_quality_score=stats.data_quality_score,
        is_new_business=False,
        assumptions=[
            Assumption("avg_customers", stats.avg_customers or 0.0, "historical", "high" if stats.n_records >= 24 else "medium"),
            Assumption("avg_order_value", stats.avg_order_value or 0.0, "historical", "high" if stats.n_records >= 24 else "medium"),
        ],
    )


def build_input_for_new_business(
    decision_type: DecisionType,
    decision_params: dict,
    expected_customers: float,
    expected_price: float,
    estimated_variable_cost_per_customer: float,
    estimated_fixed_cost: float,
    estimated_marketing_spend: float,
    elasticity_band: str = "medium",
    time_horizon_months: int = 3,
    seed: Optional[int] = None,
    iterations: int = 10_000,
) -> SimulationInput:
    params = dict(decision_params)
    params.setdefault("elasticity_band", elasticity_band)
    return SimulationInput(
        decision_type=decision_type,
        decision_params=params,
        time_horizon_months=time_horizon_months,
        seed=seed,
        iterations=iterations,
        base_customers=expected_customers,
        base_price=expected_price,
        base_variable_cost_per_customer=estimated_variable_cost_per_customer,
        base_fixed_cost=estimated_fixed_cost,
        base_marketing_spend=estimated_marketing_spend,
        customer_volatility=0.30,  # wider uncertainty band for new businesses
        cost_volatility=0.15,
        demand_elasticity=None,
        elasticity_is_estimated=True,
        data_quality_score=20.0,  # deliberately low: no historical data
        is_new_business=True,
        assumptions=[
            Assumption("expected_customers", expected_customers, "estimated", "low"),
            Assumption("expected_price", expected_price, "estimated", "low"),
            Assumption("estimated_variable_cost_per_customer", estimated_variable_cost_per_customer, "estimated", "low"),
            Assumption("estimated_fixed_cost", estimated_fixed_cost, "estimated", "low"),
            Assumption("estimated_marketing_spend", estimated_marketing_spend, "estimated", "low"),
        ],
    )
