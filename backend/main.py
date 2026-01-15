from fastapi import FastAPI

from backend.database import engine, Base
from backend.jobs.models import Job  # noqa: F401 (ensures model is registered)

from backend.credits.models import CreditBalance, CreditTransaction  # noqa
from backend.jobs.routes import router as jobs_router

from backend.users.models import User  # noqa
from backend.auth.models import MagicLinkToken  # noqa
# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------

app = FastAPI(
    title="Perpixa Platform API",
    version="v1",
)

app.include_router(jobs_router)

# -------------------------------------------------
# STARTUP EVENT
# -------------------------------------------------

@app.on_event("startup")
def on_startup():
    """
    Initialize database tables.
    Temporary v1 approach until Alembic is introduced.
    """
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}
