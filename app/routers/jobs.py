from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import Annotated, List
from app.database import get_session
from app.models.job import Job

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(session: SessionDep, job: Job):
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

@router.get("/", response_model=List[Job])
def read_jobs(session:SessionDep):
    jobs = session.exec(select(Job)).all()
    return jobs

@router.get("/{job_id}", response_model=Job)
def read_job(session: SessionDep, job_id: int):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=Job)
def update_job(session:SessionDep, job_id: int, job: Job):
    db_job = session.get(Job, job_id)
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job_data = job.dict(exclude_unset=True)
    for key, value in job_data.items():
        setattr(db_job, key, value)
    db_job.update_timestamp()
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job( job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    session.delete(job)
    session.commit()
    return {"ok": True}