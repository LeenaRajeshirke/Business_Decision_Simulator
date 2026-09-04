from sqlalchemy.orm import Session

from ..models.insight import Insight
from ..simulation.data_analysis import analyze_historical_data
from .business_service import get_active_records


def generate_insights(db: Session, business_id: int) -> list[Insight]:
    """
    Regenerates insights from the business's actual stored data. If there is no
    data, returns an empty list rather than fabricating anything — the router/
    frontend renders the "no data yet" empty state in that case.
    """
    rows = get_active_records(db, business_id)
    if not rows:
        return []

    records = [
        {
            "date": r.date, "revenue": r.revenue, "customers": r.customers,
            "orders": r.orders, "variable_cost": r.variable_cost, "fixed_cost": r.fixed_cost,
            "marketing_spend": r.marketing_spend, "other_cost": r.other_cost,
        }
        for r in rows
    ]
    stats = analyze_historical_data(records)
    source = f"Based on {stats.n_records} business records" + (
        f" spanning {stats.date_range_days} days." if stats.date_range_days else "."
    )

    generated: list[Insight] = []

    def add(type_, title, description, severity="info"):
        ins = Insight(
            business_id=business_id, type=type_, title=title,
            description=description, severity=severity, source=source,
        )
        db.add(ins)
        generated.append(ins)

    if stats.revenue_growth_rate is not None:
        if stats.revenue_growth_rate > 0.02:
            add("trend", "Revenue is growing",
                f"Revenue has been growing at roughly {stats.revenue_growth_rate * 100:.1f}% per period based on your recorded history.")
        elif stats.revenue_growth_rate < -0.02:
            add("risk", "Revenue is declining",
                f"Revenue has been declining at roughly {abs(stats.revenue_growth_rate) * 100:.1f}% per period.", severity="warning")
        else:
            add("trend", "Revenue is roughly flat",
                "Revenue growth over your recorded history is close to 0%.")

    if stats.profit_margin is not None:
        if stats.profit_margin < 0.05:
            add("risk", "Profit margin is thin",
                f"Average profit margin is {stats.profit_margin * 100:.1f}%, leaving little buffer for cost increases.", severity="warning")
        elif stats.profit_margin > 0.25:
            add("opportunity", "Healthy profit margin",
                f"Average profit margin is {stats.profit_margin * 100:.1f}%, which may support reinvestment (e.g. marketing or expansion).")

    if stats.revenue_volatility is not None and stats.revenue_volatility > 0.25:
        add("risk", "Revenue volatility is high",
            f"Revenue varies significantly period to period (coefficient of variation ~{stats.revenue_volatility:.2f}), which increases forecasting risk.", severity="warning")

    if stats.marketing_efficiency is not None:
        add("trend", "Marketing efficiency",
            f"On average, each unit of marketing spend is associated with {stats.marketing_efficiency:.2f} units of revenue.")

    if stats.data_quality_score < 50:
        add("risk", "Data quality is limited",
            f"Data quality score is {stats.data_quality_score:.0f}/100 — more consistent, complete records would improve simulation reliability.", severity="warning")

    db.commit()
    return generated
