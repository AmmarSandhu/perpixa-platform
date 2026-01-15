from sqlalchemy.orm import Session

from backend.jobs.models import Job
from backend.engines.video_engine.generate import run_job
from backend.engines.video_engine.generate import SystemFailure, UserContentError

from backend.credits.service import debit_credits, refund_credits
from backend.config import VIDEO_JOB_COST


def execute_job(job: Job, db: Session) -> Job:
    """
    Executes a queued job and updates its lifecycle state.
    This function is the ONLY place where engine is invoked.
    """

    if job.status != "queued":
        raise ValueError("Only queued jobs can be executed")

    # ---------------------------------
    # 0. Debit credits BEFORE execution
    # ---------------------------------
    debit_credits(
        db,
        user_id=job.user_id,
        job_id=job.id,
        amount=VIDEO_JOB_COST,
        reason="video_job_execution",
    )

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
        run_job(
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
        # 4a. User failure (NO refund)
        # ---------------------------------
        job.status = "failed"
        job.error_type = "user"
        job.error_message = str(e)

    except SystemFailure as e:
        # ---------------------------------
        # 4b. System failure (REFUND)
        # ---------------------------------
        job.status = "failed"
        job.error_type = "system"
        job.error_message = str(e)

        # Refund credits on system failure
        refund_credits(
            db,
            user_id=job.user_id,
            job_id=job.id,
            amount=VIDEO_JOB_COST,
            reason="system_failure_refund",
        )

        raise  # bubble up for higher-level handling

    except Exception as e:
        # ---------------------------------
        # 4c. Unknown failure → system (REFUND)
        # ---------------------------------
        job.status = "failed"
        job.error_type = "system"
        job.error_message = f"Unhandled error: {e}"

        refund_credits(
            db,
            user_id=job.user_id,
            job_id=job.id,
            amount=VIDEO_JOB_COST,
            reason="unhandled_system_failure_refund",
        )

        raise

    finally:
        db.commit()
        db.refresh(job)

    return job
