"""
SQLAlchemy ORM models for PayShield AI.
Represents database schema for transactions, users, alerts, audit logs.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UUID,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.constants import UserRole, ReviewStatus, AlertSeverity, AuditAction


class User(Base):
    """User model for analysts and admins."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    alerts_resolved = relationship(
        "Alert",
        foreign_keys="Alert.resolved_by",
        back_populates="resolved_by_user",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Transaction(Base):
    """Transaction model for incoming financial transactions."""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    merchant = Column(Text, nullable=False)
    merchant_category = Column(String(50), nullable=True)
    country = Column(String(2), nullable=True)
    device_fingerprint = Column(Text, nullable=True)
    ip_address_hash = Column(Text, nullable=True)  # SHA256 hash, not plaintext
    model_score = Column(Float, nullable=True)
    model_version = Column(String(20), nullable=True)
    is_fraud = Column(Boolean, nullable=True)  # True only when labeled by analyst
    review_status = Column(
        Enum(ReviewStatus),
        default=ReviewStatus.UNREVIEWED,
        nullable=False,
        index=True,
    )
    shap_values = Column(JSON, nullable=True)  # Store SHAP explanation
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    alerts = relationship("Alert", back_populates="transaction", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="transaction", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_txn_timestamp_desc", timestamp.desc()),
        Index("idx_txn_model_score", model_score),
        Index("idx_txn_review_status", review_status),
        Index("idx_txn_user_id", user_id),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.id}>"


class Alert(Base):
    """Alert model for flagged high-risk transactions."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_reason = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM, nullable=False)
    sent_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")
    resolved_by_user = relationship(
        "User",
        foreign_keys=[resolved_by],
        back_populates="alerts_resolved",
    )

    def __repr__(self) -> str:
        return f"<Alert {self.id}>"


class Feedback(Base):
    """Feedback model for analyst labels (for model retraining)."""
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_fraud = Column(Boolean, nullable=False)  # True if fraud, False if legitimate
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback {self.id}>"


class AuditLog(Base):
    """Audit log model for compliance and security tracking."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=True)  # 'transaction', 'alert', 'user'
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after values
    ip_address = Column(Text, nullable=True)  # Consider hashing
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)  # For correlation
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("idx_audit_user_id", user_id),
        Index("idx_audit_created_at_desc", created_at.desc()),
        Index("idx_audit_action", action),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.id}>"