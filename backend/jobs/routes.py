import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.jobs.models import Job
from backend.jobs.executor import execute_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/")
def submit_job(
    *,
    background_tasks: BackgroundTasks,
    job_config: dict,
    db: Session = Depends(get_db),
):
    """
    Submit a new job for execution.
    """

    user_id = "demo-user"  # TEMP (auth comes later)

    job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        engine="video",
        status="queued",
        input_type=job_config.get("input_type"),
        config=job_config,
        output_dir=f"outputs/{uuid.uuid4()}",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Run job in background
    background_tasks.add_task(execute_job, job, db)

    return {
        "job_id": str(job.id),
        "status": job.status,
    }
