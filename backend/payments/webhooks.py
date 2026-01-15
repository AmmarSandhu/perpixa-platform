from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.credits.service import get_or_create_balance
from backend.credits.models import CreditTransaction
from backend.config import CREDIT_PACKS

router = APIRouter(prefix="/webhooks", tags=["payments"])


@router.post("/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    user_id = payload["meta"]["user_id"]
    pack_id = payload["meta"]["pack_id"]

    credits = CREDIT_PACKS[pack_id]["credits"]

    balance = get_or_create_balance(db, user_id)
    balance.balance += credits

    txn = CreditTransaction(
        user_id=user_id,
        job_id=None,
        amount=credits,
        type="purchase",
        reason=f"lemonsqueezy_{pack_id}",
    )

    db.add(txn)
    db.commit()

    return {"status": "ok"}
