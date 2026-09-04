import io
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from ..models.business import Business
from ..models.business_data import BusinessData
from ..models.dataset import Dataset
from ..schemas.business import BusinessCreate, BusinessDataCreate
from ..simulation.data_analysis import analyze_historical_data

REQUIRED_CSV_COLUMNS = ["date", "revenue", "customers"]
OPTIONAL_CSV_COLUMNS = ["orders", "variable_cost", "fixed_cost", "marketing_spend", "other_cost"]


def create_business(db: Session, user_id: int, payload: BusinessCreate) -> Business:
    business = Business(user_id=user_id, **payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def get_business_or_404(db: Session, user_id: int, business_id: int) -> Business | None:
    return (
        db.query(Business)
        .filter(Business.id == business_id, Business.user_id == user_id)
        .first()
    )


def get_active_dataset(db: Session, business_id: int) -> Dataset | None:
    return (
        db.query(Dataset)
        .filter(Dataset.business_id == business_id, Dataset.active.is_(True))
        .order_by(Dataset.created_at.desc(), Dataset.id.desc())
        .first()
    )


def get_active_records(db: Session, business_id: int) -> list[BusinessData]:
    active = get_active_dataset(db, business_id)
    query = db.query(BusinessData).filter(BusinessData.business_id == business_id)
    if active:
        return query.filter(BusinessData.dataset_id == active.id).order_by(BusinessData.date).all()
    # Backward compatibility: before the first CSV upload, manually entered legacy
    # records remain usable. Once a dataset exists, only that dataset is active.
    return query.filter(BusinessData.dataset_id.is_(None)).order_by(BusinessData.date).all()


def add_business_data(db: Session, business_id: int, payload: BusinessDataCreate) -> BusinessData:
    active = get_active_dataset(db, business_id)
    record = BusinessData(
        business_id=business_id,
        dataset_id=active.id if active else None,
        **payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def parse_and_validate_csv(file_bytes: bytes) -> tuple[list[dict], list[str]]:
    """
    Returns (valid_records, errors). Never invents values for missing/invalid cells —
    rows with missing required fields are rejected and reported, not silently zero-filled.
    """
    errors: list[str] = []
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return [], [f"Could not parse CSV: {e}"]

    missing_cols = [c for c in REQUIRED_CSV_COLUMNS if c not in df.columns]
    if missing_cols:
        return [], [f"Missing required column(s): {', '.join(missing_cols)}"]

    for col in OPTIONAL_CSV_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    valid_records = []
    for idx, row in df.iterrows():
        row_errors = []
        try:
            parsed_date = pd.to_datetime(row["date"]).date()
        except Exception:
            row_errors.append(f"row {idx + 2}: invalid date '{row.get('date')}'")
            parsed_date = None

        for numeric_col in ["revenue", "customers"] + OPTIONAL_CSV_COLUMNS:
            val = row.get(numeric_col, 0)
            try:
                fval = float(val)
                if fval < 0:
                    row_errors.append(f"row {idx + 2}: {numeric_col} cannot be negative")
            except (TypeError, ValueError):
                row_errors.append(f"row {idx + 2}: invalid value for {numeric_col}: '{val}'")

        if row_errors:
            errors.extend(row_errors)
            continue

        valid_records.append({
            "date": parsed_date,
            "revenue": float(row["revenue"]),
            "customers": float(row["customers"]),
            "orders": float(row.get("orders", 0) or 0),
            "variable_cost": float(row.get("variable_cost", 0) or 0),
            "fixed_cost": float(row.get("fixed_cost", 0) or 0),
            "marketing_spend": float(row.get("marketing_spend", 0) or 0),
            "other_cost": float(row.get("other_cost", 0) or 0),
        })

    return valid_records, errors


def replace_active_dataset(
    db: Session, business_id: int, filename: str, records: list[dict]
) -> Dataset:
    # Replacement is atomic: the previous active dataset and its rows are removed
    # only as part of the same transaction that creates the new dataset.
    old = get_active_dataset(db, business_id)
    if old:
        db.delete(old)
        db.flush()

    dataset = Dataset(
        business_id=business_id,
        filename=filename[:255],
        row_count=len(records),
        active=True,
    )
    db.add(dataset)
    db.flush()

    objs = [BusinessData(business_id=business_id, dataset_id=dataset.id, **r) for r in records]
    db.bulk_save_objects(objs)
    db.commit()
    db.refresh(dataset)
    return dataset


def clear_active_dataset(db: Session, business_id: int) -> bool:
    active = get_active_dataset(db, business_id)
    if not active:
        return False
    db.delete(active)
    db.commit()
    return True


def get_business_data_summary(db: Session, business_id: int) -> dict:
    rows = get_active_records(db, business_id)
    records = [
        {
            "date": r.date, "revenue": r.revenue, "customers": r.customers,
            "orders": r.orders, "variable_cost": r.variable_cost, "fixed_cost": r.fixed_cost,
            "marketing_spend": r.marketing_spend, "other_cost": r.other_cost,
        }
        for r in rows
    ]
    stats = analyze_historical_data(records)
    active = get_active_dataset(db, business_id)
    return {
        "has_data": stats.n_records > 0,
        "n_records": stats.n_records,
        "date_range_days": stats.date_range_days,
        "data_quality_score": stats.data_quality_score,
        "missing_fields": stats.missing_fields,
        "dataset_id": active.id if active else None,
        "dataset_filename": active.filename if active else None,
    }
