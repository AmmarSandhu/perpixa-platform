from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.users.models import User
from backend.config import ENABLE_MOCK_PAYMENTS
from backend.payments.mock import mock_purchase_credits

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/mock/checkout/{pack_id}")
def mock_checkout(
    pack_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not ENABLE_MOCK_PAYMENTS:
        raise HTTPException(status_code=403, detail="Mock payments disabled")

    return mock_purchase_credits(
        db=db,
        user_id=str(current_user.id),
        pack_id=pack_id,
    )
