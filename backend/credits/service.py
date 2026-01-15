from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.credits.models import CreditBalance, CreditTransaction


def get_or_create_balance(db: Session, user_id: str) -> CreditBalance:
    balance = db.query(CreditBalance).filter_by(user_id=user_id).first()
    if balance:
        return balance

    balance = CreditBalance(user_id=user_id, balance=0)
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def debit_credits(
    db: Session,
    *,
    user_id: str,
    job_id,
    amount: int,
    reason: str
):
    if amount <= 0:
        raise ValueError("Debit amount must be positive")

    balance = get_or_create_balance(db, user_id)

    if balance.balance < amount:
        raise ValueError("Insufficient credits")

    balance.balance -= amount

    txn = CreditTransaction(
        user_id=user_id,
        job_id=job_id,
        amount=amount,
        type="debit",
        reason=reason,
    )

    db.add(txn)
    db.commit()


def refund_credits(
    db: Session,
    *,
    user_id: str,
    job_id,
    amount: int,
    reason: str
):
    if amount <= 0:
        raise ValueError("Refund amount must be positive")

    balance = get_or_create_balance(db, user_id)
    balance.balance += amount

    txn = CreditTransaction(
        user_id=user_id,
        job_id=job_id,
        amount=amount,
        type="refund",
        reason=reason,
    )

    db.add(txn)
    db.commit()
