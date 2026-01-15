from sqlalchemy.orm import Session

from backend.credits.service import get_or_create_balance
from backend.credits.models import CreditTransaction
from backend.config import CREDIT_PACKS


def mock_purchase_credits(
    *,
    db: Session,
    user_id: str,
    pack_id: str,
):
    if pack_id not in CREDIT_PACKS:
        raise ValueError("Invalid credit pack")

    credits = CREDIT_PACKS[pack_id]["credits"]

    balance = get_or_create_balance(db, user_id)
    balance.balance += credits

    txn = CreditTransaction(
        user_id=user_id,
        job_id=None,
        amount=credits,
        type="purchase",
        reason=f"mock_{pack_id}",
    )

    db.add(txn)
    db.commit()

    return {
        "credits_added": credits,
        "new_balance": balance.balance,
    }
