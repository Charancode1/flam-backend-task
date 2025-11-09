import json
from datetime import datetime
from pathlib import Path

JOBS_FILE = Path(__file__).resolve().parent / "jobs.json"

def init_storage():
    """Initialize jobs.json if not exists."""
    if not JOBS_FILE.exists():
        with open(JOBS_FILE, "w") as f:
            json.dump([], f)

def load_jobs():
    """Load all jobs from storage."""
    if not JOBS_FILE.exists():
        return []
    with open(JOBS_FILE, "r") as f:
        return json.load(f)

def save_jobs(jobs):
    """Save all jobs to storage."""
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=4)

def add_job(job):
    """Add a new job."""
    jobs = load_jobs()
    jobs.append(job)
    save_jobs(jobs)

def update_job_state(job_id, new_state):
    """Update the state of a job."""
    jobs = load_jobs()
    for job in jobs:
        if job["id"] == job_id:
            job["state"] = new_state
            job["updated_at"] = datetime.now().isoformat()
    save_jobs(jobs)

def list_jobs(state=None):
    """List all jobs or filter by state."""
    jobs = load_jobs()
    if state:
        jobs = [j for j in jobs if j["state"] == state]
    return jobs
