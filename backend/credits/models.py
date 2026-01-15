import uuid
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.database import Base


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    user_id = Column(String, primary_key=True)
    balance = Column(Integer, nullable=False, default=0)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(String, nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=True)

    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # purchase | debit | refund
    reason = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
