from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.business import Business
from ..models.user import User
from ..schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from ..services import business_service
from ..utils.deps import get_current_user

router = APIRouter(prefix="/api/business", tags=["business"])


@router.get("", response_model=list[BusinessResponse])
def list_businesses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Business).filter(Business.user_id == user.id).all()


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return business_service.create_business(db, user.id, payload)


@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: int, payload: BusinessUpdate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    business = business_service.get_business_or_404(db, user.id, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    for k, v in payload.model_dump().items():
        setattr(business, k, v)
    db.commit()
    db.refresh(business)
    return business
