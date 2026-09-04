from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    business_type: Optional[str] = None
    location: Optional[str] = None
    currency: str = "INR"
    is_new_business: bool = False

    # Only relevant when is_new_business = True. Always shown to the user as
    # "estimated assumption", never presented as measured fact.
    expected_price: Optional[float] = None
    expected_monthly_customers: Optional[float] = None
    estimated_variable_cost_per_customer: Optional[float] = None
    estimated_fixed_cost: Optional[float] = None
    estimated_marketing_spend: Optional[float] = None


class BusinessUpdate(BusinessCreate):
    pass


class BusinessResponse(BusinessCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BusinessDataCreate(BaseModel):
    date: date
    revenue: float = Field(ge=0)
    customers: float = Field(ge=0)
    orders: Optional[float] = Field(default=None, ge=0)
    variable_cost: float = Field(ge=0, default=0)
    fixed_cost: float = Field(ge=0, default=0)
    marketing_spend: float = Field(ge=0, default=0)
    other_cost: float = Field(ge=0, default=0)


class BusinessDataResponse(BusinessDataCreate):
    id: int

    class Config:
        from_attributes = True


class BusinessDataSummary(BaseModel):
    """Used to render honest empty/loading/data states on the frontend."""
    has_data: bool
    n_records: int
    date_range_days: Optional[int]
    data_quality_score: float
    missing_fields: list[str]
    dataset_id: Optional[int] = None
    dataset_filename: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    business_id: int
    filename: str
    row_count: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
