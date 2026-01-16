import uuid
import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi import Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

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



@router.get("/")
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(Job)
        .filter(Job.user_id == str(current_user.id))
        .order_by(desc(Job.created_at))
        .all()
    )

    return [
        {
            "job_id": str(job.id),
            "engine": job.engine,
            "status": job.status,
            "input_type": job.input_type,
            "created_at": job.created_at,
            "error_type": job.error_type,
            "error_message": job.error_message,
        }
        for job in jobs
    ]





@router.get("/{job_id}")
def get_job(
    job_id: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": str(job.id),
        "engine": job.engine,
        "status": job.status,
        "input_type": job.input_type,
        "config": job.config,
        "output_dir": job.output_dir,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error_type": job.error_type,
        "error_message": job.error_message,
    }




@router.get("/{job_id}/outputs")
def list_job_outputs(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    outputs = []

    if os.path.exists(job.output_dir):
        for root, _, files in os.walk(job.output_dir):
            for file in files:
                if file.endswith((".mp4", ".png", ".mp3", ".json")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, job.output_dir)
                    outputs.append(rel_path)

    return {
        "job_id": str(job.id),
        "outputs": outputs,
    }





@router.get("/{job_id}/download")
def download_job_output(
    job_id: str,
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    full_path = os.path.abspath(os.path.join(job.output_dir, path))
    base_dir = os.path.abspath(job.output_dir)

    # 🔒 Path traversal protection
    if not full_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Invalid file path")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(full_path, filename=os.path.basename(full_path))
