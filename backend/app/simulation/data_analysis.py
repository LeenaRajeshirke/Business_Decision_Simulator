"""
Historical business data analysis.

Every number produced here is derived directly from the records passed in.
If there is not enough data to compute a statistic reliably, the function
returns None (or a flagged low-confidence value) instead of guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

MIN_RECORDS_FOR_TREND = 3
MIN_RECORDS_FOR_ELASTICITY = 6


@dataclass
class HistoricalStats:
    n_records: int
    date_range_days: Optional[int]
    avg_revenue: Optional[float]
    avg_customers: Optional[float]
    avg_order_value: Optional[float]
    avg_variable_cost: Optional[float]
    avg_fixed_cost: Optional[float]
    avg_marketing_spend: Optional[float]
    revenue_growth_rate: Optional[float]        # per-period % growth, from linear fit
    customer_growth_rate: Optional[float]
    revenue_volatility: Optional[float]          # coefficient of variation
    cost_volatility: Optional[float]
    profit_margin: Optional[float]
    marketing_efficiency: Optional[float]        # revenue per unit marketing spend
    demand_elasticity: Optional[float]           # % change in customers per % change in price (if inferable)
    data_quality_score: float                    # 0-100
    missing_fields: list = field(default_factory=list)
    sufficient_for_ml: bool = False


def _cv(series: pd.Series) -> Optional[float]:
    """Coefficient of variation (volatility), guarded against zero mean."""
    if len(series) < 2:
        return None
    mean = series.mean()
    if mean == 0:
        return None
    return float(series.std(ddof=1) / abs(mean))


def _growth_rate(series: pd.Series) -> Optional[float]:
    """Average per-period % growth rate estimated via linear regression on log values."""
    s = series.replace(0, np.nan).dropna()
    if len(s) < MIN_RECORDS_FOR_TREND:
        return None
    x = np.arange(len(s))
    y = np.log(s.values)
    slope, _ = np.polyfit(x, y, 1)
    return float(np.expm1(slope))  # per-period growth rate as a fraction


def compute_data_quality(df: pd.DataFrame, required_fields: list[str]) -> tuple[float, list[str]]:
    if df.empty:
        return 0.0, required_fields[:]

    missing = [f for f in required_fields if f not in df.columns or df[f].isna().mean() > 0.2]
    completeness = 1.0 - (df[required_fields].isna().mean().mean() if required_fields else 0.0)
    record_score = min(1.0, len(df) / 30.0)  # 30+ records considered "good" coverage
    date_score = 1.0
    if "date" in df.columns and df["date"].notna().sum() >= 2:
        span_days = (df["date"].max() - df["date"].min()).days
        date_score = min(1.0, span_days / 90.0)  # 90+ days considered good coverage

    score = 100.0 * (0.5 * completeness + 0.3 * record_score + 0.2 * date_score)
    return round(max(0.0, min(100.0, score)), 1), missing


def analyze_historical_data(records: list[dict]) -> HistoricalStats:
    """
    records: list of dicts with keys matching BUSINESS_DATA columns:
    date, revenue, customers, orders, variable_cost, fixed_cost, marketing_spend, other_cost
    """
    if not records:
        return HistoricalStats(
            n_records=0, date_range_days=None, avg_revenue=None, avg_customers=None,
            avg_order_value=None, avg_variable_cost=None, avg_fixed_cost=None,
            avg_marketing_spend=None, revenue_growth_rate=None, customer_growth_rate=None,
            revenue_volatility=None, cost_volatility=None, profit_margin=None,
            marketing_efficiency=None, demand_elasticity=None, data_quality_score=0.0,
            missing_fields=["all business data"], sufficient_for_ml=False,
        )

    df = pd.DataFrame(records)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    required = ["revenue", "customers", "variable_cost", "fixed_cost", "marketing_spend"]
    quality_score, missing_fields = compute_data_quality(df, required)

    n = len(df)
    date_range_days = None
    if "date" in df.columns and df["date"].notna().sum() >= 2:
        date_range_days = int((df["date"].max() - df["date"].min()).days)

    avg_revenue = float(df["revenue"].mean()) if "revenue" in df else None
    avg_customers = float(df["customers"].mean()) if "customers" in df else None
    avg_variable_cost = float(df["variable_cost"].mean()) if "variable_cost" in df else None
    avg_fixed_cost = float(df["fixed_cost"].mean()) if "fixed_cost" in df else None
    avg_marketing = float(df["marketing_spend"].mean()) if "marketing_spend" in df else None

    avg_order_value = None
    if "revenue" in df and "customers" in df and (df["customers"] > 0).any():
        aov_series = df["revenue"] / df["customers"].replace(0, np.nan)
        avg_order_value = float(aov_series.mean(skipna=True))

    revenue_growth = _growth_rate(df["revenue"]) if "revenue" in df else None
    customer_growth = _growth_rate(df["customers"]) if "customers" in df else None
    revenue_vol = _cv(df["revenue"]) if "revenue" in df else None

    cost_cols = [c for c in ["variable_cost", "fixed_cost", "marketing_spend", "other_cost"] if c in df]
    cost_vol = _cv(df[cost_cols].sum(axis=1)) if cost_cols else None

    profit_margin = None
    total_cost_avg = sum(v for v in [avg_variable_cost, avg_fixed_cost, avg_marketing] if v is not None)
    if avg_revenue and avg_revenue > 0:
        profit_margin = float((avg_revenue - total_cost_avg) / avg_revenue)

    marketing_efficiency = None
    if avg_marketing and avg_marketing > 0 and avg_revenue is not None:
        marketing_efficiency = float(avg_revenue / avg_marketing)

    demand_elasticity = None
    if n >= MIN_RECORDS_FOR_ELASTICITY and "revenue" in df and "customers" in df and avg_order_value:
        # crude price proxy = revenue / customers per period; regress log(customers) on log(price proxy)
        price_proxy = (df["revenue"] / df["customers"].replace(0, np.nan)).replace(0, np.nan)
        valid = price_proxy.notna() & (df["customers"] > 0)
        if valid.sum() >= MIN_RECORDS_FOR_ELASTICITY and price_proxy[valid].std() > 0:
            log_p = np.log(price_proxy[valid].values)
            log_c = np.log(df["customers"][valid].values)
            slope, _ = np.polyfit(log_p, log_c, 1)
            demand_elasticity = float(slope)  # negative slope = normal demand response

    sufficient_for_ml = n >= 24 and quality_score >= 60.0

    return HistoricalStats(
        n_records=n,
        date_range_days=date_range_days,
        avg_revenue=avg_revenue,
        avg_customers=avg_customers,
        avg_order_value=avg_order_value,
        avg_variable_cost=avg_variable_cost,
        avg_fixed_cost=avg_fixed_cost,
        avg_marketing_spend=avg_marketing,
        revenue_growth_rate=revenue_growth,
        customer_growth_rate=customer_growth,
        revenue_volatility=revenue_vol,
        cost_volatility=cost_vol,
        profit_margin=profit_margin,
        marketing_efficiency=marketing_efficiency,
        demand_elasticity=demand_elasticity,
        data_quality_score=quality_score,
        missing_fields=missing_fields,
        sufficient_for_ml=sufficient_for_ml,
    )
