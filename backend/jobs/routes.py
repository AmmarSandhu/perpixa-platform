import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.jobs.models import Job
from backend.jobs.executor import execute_job

from backend.auth.dependencies import get_current_user
from backend.users.models import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/")
def submit_job(
    *,
    background_tasks: BackgroundTasks,
    job_config: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new job for execution.
    """
    input_type = job_config.get("input_type")

    if not input_type:
        raise HTTPException(
            status_code=422,
            detail="input_type is required in job_config",
        )
    
    
    job = Job(
        id=uuid.uuid4(),
        user_id=str(current_user.id),
        engine="video",
        status="queued",
        input_type=input_type,
        config=job_config,
        output_dir=f"outputs/{uuid.uuid4()}",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(execute_job, job, db)

    return {
        "job_id": str(job.id),
        "status": job.status,
    }
