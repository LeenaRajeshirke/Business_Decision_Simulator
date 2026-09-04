from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from ..services import auth_service
from ..utils.deps import get_current_user
from ..utils.password_validation import PasswordTooLongError
from ..models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Note: PasswordTooLongError is normally already caught by Pydantic's
    # field_validator on RegisterRequest (schemas/auth.py), which returns a
    # 422 automatically before this function even runs. The except clause
    # below is defense-in-depth in case hash_password() is ever reached with
    # an over-length value some other way — it must never surface as a raw
    # bcrypt ValueError/stack trace.
    try:
        user = auth_service.register_user(db, payload.name, payload.email, payload.password)
    except PasswordTooLongError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, payload.email, payload.password)
    except PasswordTooLongError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
