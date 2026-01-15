from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.users.models import User
from backend.auth.models import MagicLinkToken
from backend.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def request_magic_link(email: str, db: Session = Depends(get_db)):
    """
    Request a magic login link.
    Email sending is mocked for v1.
    """

    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = MagicLinkToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    db.add(token)
    db.commit()
    db.refresh(token)

    # Mock email sending
    return {
        "login_url": f"/auth/callback?token={token.id}"
    }


@router.get("/callback")
def magic_link_callback(token: uuid.UUID, db: Session = Depends(get_db)):
    """
    Validate magic link and issue JWT.
    """

    token_record = (
        db.query(MagicLinkToken)
        .filter_by(id=token, used=False)
        .first()
    )

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or used token")

    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")

    token_record.used = True
    db.commit()

    access_token = create_access_token(
        data={"sub": str(token_record.user_id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
