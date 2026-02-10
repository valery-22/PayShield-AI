"""
Constants and enums for PayShield AI backend.
"""

from enum import Enum
from typing import Literal


class UserRole(str, Enum):
    """User role enumeration."""
    ANALYST = "analyst"
    ADMIN = "admin"


class ReviewStatus(str, Enum):
    """Transaction review status enumeration."""
    UNREVIEWED = "unreviewed"
    CONFIRMED_FRAUD = "confirmed_fraud"
    CONFIRMED_OK = "confirmed_ok"


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AuditAction(str, Enum):
    """Audit log action enumeration."""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    VIEW_TRANSACTION = "VIEW_TRANSACTION"
    MARK_FRAUD = "MARK_FRAUD"
    MARK_OK = "MARK_OK"
    CREATE_USER = "CREATE_USER"
    DELETE_USER = "DELETE_USER"
    DEPLOY_MODEL = "DEPLOY_MODEL"


# Risk thresholds
FRAUD_SCORE_LOW_THRESHOLD: float = 0.30
FRAUD_SCORE_MEDIUM_THRESHOLD: float = 0.70
FRAUD_SCORE_HIGH_THRESHOLD: float = 0.90

# Cache keys
CACHE_KEY_USER: str = "user:{user_id}"
CACHE_KEY_PREDICTION: str = "pred:{features_hash}"
CACHE_KEY_TRANSACTION: str = "txn:{transaction_id}"
CACHE_KEY_RATE_LIMIT: str = "rate_limit:{user_id}:{period}"

# API
API_V1_PREFIX: str = "/api/v1"
HEALTH_CHECK_ENDPOINT: str = "/health"
METRICS_ENDPOINT: str = "/metrics"

# Pagination
DEFAULT_LIMIT: int = 50
MAX_LIMIT: int = 500
DEFAULT_OFFSET: int = 0

# Security
ALGORITHM: str = "HS256"
TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS: int = 30

# Logging
REQUEST_ID_HEADER: str = "X-Request-ID"
CORRELATION_ID_HEADER: str = "X-Correlation-ID"

# Merchant categories
MERCHANT_CATEGORIES = [
    "retail",
    "food",
    "electronics",
    "travel",
    "luxury",
    "groceries",
    "gas",
    "utilities",
    "entertainment",
    "healthcare",
]

# Countries
COUNTRIES = [
    "US", "CA", "GB", "AU", "DE", "FR", "ES", "IT", "NL", "BE",
    "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "AT", "GR", "PT",
]

# HTTP Status Codes
HTTP_401_UNAUTHORIZED: int = 401
HTTP_403_FORBIDDEN: int = 403
HTTP_404_NOT_FOUND: int = 404
HTTP_422_UNPROCESSABLE_ENTITY: int = 422
HTTP_429_TOO_MANY_REQUESTS: int = 429
HTTP_500_INTERNAL_SERVER_ERROR: int = 500
HTTP_503_SERVICE_UNAVAILABLE: int = 503