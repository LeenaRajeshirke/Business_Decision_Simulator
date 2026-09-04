from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.business_data import BusinessData
from ..models.user import User
from ..models.insight import Insight
from ..schemas.business import (
    BusinessDataCreate,
    BusinessDataResponse,
    BusinessDataSummary,
    DatasetResponse,
)
from ..services import business_service
from ..utils.deps import get_current_user


router = APIRouter(
    prefix="/api/business-data",
    tags=["business-data"],
)


def _authorize_business(db: Session, user: User, business_id: int):
    """Verify that the authenticated user owns/accesses the requested business."""
    business = business_service.get_business_or_404(
        db,
        user.id,
        business_id,
    )

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return business


# ============================================================
# ACTIVE DATASET
# IMPORTANT: Keep these static routes BEFORE /{record_id}
# ============================================================

@router.get(
    "/active",
    response_model=DatasetResponse | None,
)
def active_dataset(
    business_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return the currently active CSV dataset for the business.

    Returns:
        Dataset information when a dataset exists.
        None when no dataset is active.
    """
    _authorize_business(db, user, business_id)

    return business_service.get_active_dataset(
        db,
        business_id,
    )


@router.delete(
    "/active",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_dataset(
    business_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove the currently active dataset."""
    _authorize_business(db, user, business_id)

    business_service.clear_active_dataset(
        db,
        business_id,
    )

    # Dataset changes invalidate previously generated insights.
    db.query(Insight).filter(
        Insight.business_id == business_id
    ).delete()

    db.commit()

    return None


# ============================================================
# DATA SUMMARY
# ============================================================

@router.get(
    "/summary",
    response_model=BusinessDataSummary,
)
def data_summary(
    business_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return summary information for the active business dataset.

    No fabricated/default business metrics are returned.
    """
    _authorize_business(db, user, business_id)

    return business_service.get_business_data_summary(
        db,
        business_id,
    )


# ============================================================
# LIST ACTIVE DATA
# ============================================================

@router.get(
    "",
    response_model=list[BusinessDataResponse],
)
def list_data(
    business_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return records belonging to the currently active dataset."""
    _authorize_business(db, user, business_id)

    return business_service.get_active_records(
        db,
        business_id,
    )


# ============================================================
# ADD MANUAL RECORD
# ============================================================

@router.post(
    "",
    response_model=BusinessDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_data(
    business_id: int,
    payload: BusinessDataCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a manual business-data record."""
    _authorize_business(db, user, business_id)

    result = business_service.add_business_data(
        db,
        business_id,
        payload,
    )

    # Existing insights are no longer guaranteed to represent
    # the current dataset.
    db.query(Insight).filter(
        Insight.business_id == business_id
    ).delete()

    db.commit()

    return result


# ============================================================
# CSV UPLOAD
# ============================================================

@router.post(
    "/upload",
)
def upload_csv(
    business_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Upload a CSV and replace the currently active dataset.

    The uploaded CSV becomes the single active dataset for
    this business.
    """

    _authorize_business(
        db,
        user,
        business_id,
    )

    # Basic file validation
    filename = file.filename or "uploaded.csv"

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only CSV files are supported.",
        )

    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded CSV file is empty.",
        )

    # Parse and validate CSV
    records, errors = business_service.parse_and_validate_csv(
        content
    )

    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "No valid rows found in CSV.",
                "errors": errors[:50],
            },
        )

    # Replace existing active dataset
    dataset = business_service.replace_active_dataset(
        db,
        business_id,
        filename,
        records,
    )

    # Dataset changed → old insights are invalid.
    db.query(Insight).filter(
        Insight.business_id == business_id
    ).delete()

    db.commit()

    return {
        "dataset": {
            "id": dataset.id,
            "business_id": dataset.business_id,
            "filename": dataset.filename,
            "row_count": dataset.row_count,
            "active": dataset.active,
            "created_at": dataset.created_at,
        },
        "inserted": dataset.row_count,
        "rejected": len(errors),
        "errors": errors[:50],
    }


# ============================================================
# UPDATE RECORD
# ============================================================

@router.put(
    "/{record_id}",
    response_model=BusinessDataResponse,
)
def update_data(
    business_id: int,
    record_id: int,
    payload: BusinessDataCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a record belonging to the active dataset."""

    _authorize_business(
        db,
        user,
        business_id,
    )

    # Only allow editing records in the active dataset.
    active_records = business_service.get_active_records(
        db,
        business_id,
    )

    active_ids = {
        record.id
        for record in active_records
    }

    if record_id not in active_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found in the active dataset",
        )

    record = (
        db.query(BusinessData)
        .filter(
            BusinessData.id == record_id,
            BusinessData.business_id == business_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    # Update fields
    for key, value in payload.model_dump().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)

    # Invalidate insights after data modification.
    db.query(Insight).filter(
        Insight.business_id == business_id
    ).delete()

    db.commit()

    return record


# ============================================================
# DELETE RECORD
# ============================================================

@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_data(
    business_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a record from the active dataset."""

    _authorize_business(
        db,
        user,
        business_id,
    )

    active_records = business_service.get_active_records(
        db,
        business_id,
    )

    active_ids = {
        record.id
        for record in active_records
    }

    if record_id not in active_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found in the active dataset",
        )

    record = (
        db.query(BusinessData)
        .filter(
            BusinessData.id == record_id,
            BusinessData.business_id == business_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    db.delete(record)
    db.commit()

    # Invalidate insights after deletion.
    db.query(Insight).filter(
        Insight.business_id == business_id
    ).delete()

    db.commit()

    return None