from sqlalchemy.orm import Session

from backend.jobs.models import Job
from backend.engines.video_engine.generate import run_job
from backend.engines.video_engine.generate import SystemFailure, UserContentError


def execute_job(job: Job, db: Session) -> Job:
    """
    Executes a queued job and updates its lifecycle state.
    This function is the ONLY place where engine is invoked.
    """

    if job.status != "queued":
        raise ValueError("Only queued jobs can be executed")

    # ---------------------------------
    # 1. Mark job as running
    # ---------------------------------
    job.status = "running"
    db.commit()
    db.refresh(job)

    try:
        # ---------------------------------
        # 2. Execute engine
        # ---------------------------------
        result = run_job(
            job_id=str(job.id),
            user_id=job.user_id,
            config=job.config,
            output_dir=job.output_dir,
        )

        # ---------------------------------
        # 3. Mark completed
        # ---------------------------------
        job.status = "completed"
        job.error_type = None
        job.error_message = None

    except UserContentError as e:
        # ---------------------------------
        # 4a. User failure (no refund)
        # ---------------------------------
        job.status = "failed"
        job.error_type = "user"
        job.error_message = str(e)

    except SystemFailure as e:
        # ---------------------------------
        # 4b. System failure (refund)
        # ---------------------------------
        job.status = "failed"
        job.error_type = "system"
        job.error_message = str(e)
        raise  # bubble up for refund handling later

    except Exception as e:
        # ---------------------------------
        # 4c. Unknown failure → system
        # ---------------------------------
        job.status = "failed"
        job.error_type = "system"
        job.error_message = f"Unhandled error: {e}"
        raise

    finally:
        db.commit()
        db.refresh(job)

    return job
