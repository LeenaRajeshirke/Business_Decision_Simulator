from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..utils.password_validation import MAX_PASSWORD_BYTES, password_byte_length


def _check_password_bytes(password: str) -> str:
    """Shared validator: rejects (never truncates) passwords whose UTF-8
    byte length exceeds bcrypt's 72-byte limit. Checked separately from
    Python string length, since multi-byte characters (emoji, accents,
    non-Latin scripts) can be short in characters but long in bytes."""
    byte_len = password_byte_length(password)
    if byte_len > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password must be {MAX_PASSWORD_BYTES} bytes or fewer (got {byte_len} bytes)."
        )
    return password


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    # max_length=72 is a fast character-count pre-filter; the byte-length
    # validator below is the real check, since UTF-8 bytes >= character count.
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_limit(cls, v: str) -> str:
        return _check_password_bytes(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_limit(cls, v: str) -> str:
        return _check_password_bytes(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True
