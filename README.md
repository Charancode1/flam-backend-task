QueueCTL — Lightweight Background Job Queue System (FLAM Backend Internship Task)

Overview  
This project implements a **CLI-based background job queue system** called **QueueCTL**, built using **Python** and **Click**. It allows users to enqueue jobs, manage workers, and automatically execute commands in the background with persistent job tracking and retry mechanisms.  

This was developed as part of the **FLAM Backend Developer Internship Task**, focusing on implementing a modular and reliable background processing system with local storage management.


Features Implemented
Enqueue Jobs – Add new jobs to the system using a simple CLI command (stored in a persistent JSON file).  
Run Command – Execute pending jobs sequentially, updating their state (`pending`, `processing`, `completed`, `failed`, `dead`).  
Worker Mode – Continuously polls for new jobs and executes them automatically, including retry logic for failed jobs (up to 3 attempts).  
Status Command – Displays real-time statistics and a detailed table of job states and attempts.  
Persistent Storage*– All jobs are saved in a `jobs.json` file using helper functions in `storage.py`.  



System Components

1. `__main__.py`
Contains the main CLI logic built using the **Click** framework.  
Implements the following commands:
- `enqueue` → Add new jobs to the queue.  
- `run` → Manually process pending jobs.  
- `worker` → Start a background worker that auto-executes pending jobs.  
- `status` → View all jobs and their current state in a formatted table.  

2. `storage.py`
Handles job persistence and file operations:
- Initializes `jobs.json` storage.  
- Adds new jobs, lists jobs by state, loads, and saves data safely.  



Example Commands

Enqueue a job
```bash
python __main__.py enqueue "{\"id\":\"job1\",\"command\":\"echo Hello from job1\"}"
```

Check queue status
```bash
python __main__.py status
```

Run pending jobs manually
```bash
python __main__.py run
```

Start a background worker
```bash
python __main__.py worker
```

---

Sample Output

Enqueue
```
Job enqueued: id=job1, command=echo Hello from job1
```

Worker Processing
```
Worker started — polling every 5 seconds. Press Ctrl+C to stop.
Running job job1: echo Hello from job1
Job job1 completed successfully.
```

Status
```
Total jobs: 5
ID         STATE        ATTEMPTS   UPDATED_AT                COMMAND
----------------------------------------------------------------------
job1       completed    0          2025-11-09T15:26:35.010988 echo Hello from job1
job2       completed    0          2025-11-09T16:25:02Z      echo Auto job!
fail1      dead         3          2025-11-09T16:35:03Z      exit 1

Summary:
  pending: 0
  processing: 0
  completed: 2
  failed: 0
  dead: 1
```

---

Tech Stack
- **Language:** Python 3.12  
- **Framework:** Click (for CLI interface)  
- **Storage:** Local JSON file (`jobs.json`)  
- **Environment:** Virtualenv (.venv)

---

Learning Outcome
Through this task, I learned:
- How CLI applications are structured using the **Click** library.  
- How to design a background job queue system with **retry and state management**.  
- File-based persistence and safe data handling in Python.  
- Modular code design for backend systems.
