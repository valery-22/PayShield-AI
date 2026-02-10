"""
Pydantic schemas for request/response validation in PayShield AI API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

from app.constants import UserRole, ReviewStatus, AlertSeverity


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.ANALYST


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


# ============================================================================
# Transaction Schemas
# ============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema."""
    amount: float = Field(..., gt=0, le=1_000_000)
    currency: str = "USD"
    merchant: str
    merchant_category: Optional[str] = None
    country: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address_hash: Optional[str] = None
    timestamp: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    """Transaction creation schema."""
    user_id: Optional[UUID] = None


class TransactionUpdate(BaseModel):
    """Transaction update schema."""
    review_status: Optional[ReviewStatus] = None
    is_fraud: Optional[bool] = None


class TransactionResponse(TransactionBase):
    """Transaction response schema."""
    id: UUID
    user_id: Optional[UUID]
    model_score: Optional[float]
    model_version: Optional[str]
    is_fraud: Optional[bool]
    review_status: ReviewStatus
    shap_values: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Transaction list response with pagination."""
    items: List[TransactionResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# Prediction Schemas
# ============================================================================

class PredictionRequest(BaseModel):
    """Prediction request schema."""
    amount: float = Field(..., gt=0, le=1_000_000)
    merchant_category: str
    country: str
    device_fingerprint: Optional[str] = None
    ip_address_hash: Optional[str] = None
    timestamp: Optional[datetime] = None

    @validator("merchant_category")
    def validate_merchant_category(cls, v):
        """Validate merchant category."""
        valid_categories = [
            "retail", "food", "electronics", "travel", "luxury",
            "groceries", "gas", "utilities", "entertainment", "healthcare"
        ]
        if v not in valid_categories:
            raise ValueError(f"Invalid merchant_category. Must be one of {valid_categories}")
        return v

    @validator("country")
    def validate_country(cls, v):
        """Validate country code."""
        valid_countries = [
            "US", "CA", "GB", "AU", "DE", "FR", "ES", "IT", "NL", "BE",
            "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "AT", "GR", "PT",
        ]
        if v not in valid_countries:
            raise ValueError(f"Invalid country. Must be one of {valid_countries}")
        return v


class PredictionResponse(BaseModel):
    """Prediction response schema."""
    id: UUID
    model_score: float = Field(..., ge=0, le=1)
    fraud_label: int = Field(..., ge=0, le=1)
    model_version: str
    latency_ms: float


class ExplanationRequest(BaseModel):
    """SHAP explanation request schema."""
    transaction_id: UUID


class SHAPFeatureContribution(BaseModel):
    """SHAP feature contribution schema."""
    feature: str
    contribution: float
    rank: int


class ExplanationResponse(BaseModel):
    """SHAP explanation response schema."""
    transaction_id: UUID
    model_score: float
    base_value: float
    shap_values: Dict[str, float]
    feature_contributions: List[SHAPFeatureContribution]


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertBase(BaseModel):
    """Base alert schema."""
    transaction_id: UUID
    alert_reason: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM


class AlertResponse(AlertBase):
    """Alert response schema."""
    id: UUID
    sent_to: Optional[UUID]
    resolved: bool
    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


class AlertListResponse(BaseModel):
    """Alert list response with pagination."""
    items: List[AlertResponse]
    total: int
    limit: int
    offset: int


class ResolveAlertRequest(BaseModel):
    """Resolve alert request schema."""
    is_fraud: bool
    resolution_notes: Optional[str] = None


# ============================================================================
# Feedback Schemas
# ============================================================================

class FeedbackCreate(BaseModel):
    """Feedback creation schema."""
    transaction_id: UUID
    is_fraud: bool
    reviewer_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response schema."""
    id: UUID
    transaction_id: UUID
    is_fraud: bool
    reviewer_id: Optional[UUID]
    reviewer_notes: Optional[str]
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True


# ============================================================================
# Health & Metrics Schemas
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: bool
    redis: bool
    model: bool
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


# ============================================================================
# Pagination & Filtering Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class TransactionFilterParams(PaginationParams):
    """Transaction filter parameters."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    merchant_category: Optional[str] = None
    country: Optional[str] = None
    review_status: Optional[ReviewStatus] = None
    is_fraud: Optional[bool] = None