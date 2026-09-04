from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.insight import Insight
from ..models.user import User
from ..services import business_service, insight_service
from ..utils.deps import get_current_user

router = APIRouter(prefix="/api/insights", tags=["insights"])


class InsightOut(BaseModel):
    id: int
    type: str
    title: str
    description: str
    severity: str
    source: str

    class Config:
        from_attributes = True


def _authorize_business(db, user, business_id):
    business = business_service.get_business_or_404(db, user.id, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.get("", response_model=list[InsightOut])
def list_insights(
    business_id: int, refresh: bool = False,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    _authorize_business(db, user, business_id)
    if refresh:
        db.query(Insight).filter(Insight.business_id == business_id).delete()
        db.commit()
        return insight_service.generate_insights(db, business_id)

    existing = db.query(Insight).filter(Insight.business_id == business_id).all()
    if not existing:
        return insight_service.generate_insights(db, business_id)
    return existing
