# main.py
import click
import json
import time
import subprocess
import threading

# Try to import storage from package or local module
try:
    # If your storage.py is inside a package folder named `queuectl`, use:
    from queuectl import storage
except Exception:
    # If storage.py is alongside main.py, use simple import
    import storage


@click.group()
def cli():
    """QueueCTL - A CLI-based background job queue system."""
    pass


@cli.command()
@click.argument('job_data')
def enqueue(job_data):
    """Enqueue a new job into the system.

    job_data must be a JSON string with at least `id` and `command`.
    Example (PowerShell escaping):
    python main.py enqueue "{\"id\":\"job1\",\"command\":\"echo Hello\"}"
    """
    # parse JSON
    try:
        job = json.loads(job_data)
    except json.JSONDecodeError:
        click.echo("❌ Invalid JSON. Provide job as a JSON string.")
        return

    # required fields
    if "id" not in job or "command" not in job:
        click.echo("❌ job must include 'id' and 'command' fields.")
        return

    # fill defaults
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    job.setdefault("state", "pending")
    job.setdefault("attempts", 0)
    job.setdefault("max_retries", 3)
    job.setdefault("created_at", now)
    job.setdefault("updated_at", now)

    # init storage and add job
    try:
        storage.init_storage()
    except Exception as e:
        click.echo(f"❌ Storage initialization failed: {e}")
        return

    try:
        storage.add_job(job)
        click.echo(f"✅ Job enqueued: id={job['id']}, command={job['command']}")
    except Exception as e:
        click.echo(f"❌ Failed to save job: {e}")


@cli.group()
def worker():
    """Manage worker processes."""
    pass


@worker.command('start')
@click.option('--count', default=1, help='Number of workers to start.')
def start_workers(count):
    click.echo(f"🚀 Starting {count} worker(s)...")
    # TODO: later we will call worker.start_workers(count)


@worker.command('stop')
def stop_workers():
    click.echo("🛑 Stopping all workers...")
    # TODO: later we will signal workers to stop


@cli.command()
@click.option('--state', default=None, help='Filter by job state (pending, processing, completed, failed, dead).')
def status(state):
    """Show the status summary of all jobs."""
    from storage import load_jobs

    jobs = load_jobs()
    if state:
        jobs = [j for j in jobs if j['state'] == state]

    total = len(jobs)
    click.echo(f"Total jobs: {total}")

    if total > 0:
        click.echo(f"{'ID':<10} {'STATE':<12} {'ATTEMPTS':<10} {'UPDATED_AT':<25} {'COMMAND'}")
        click.echo("-" * 70)
        for j in jobs:
            click.echo(f"{j['id']:<10} {j['state']:<12} {j['attempts']:<10} {j.get('updated_at', 'N/A'):<25} {j['command']}")

    summary = {s: len([j for j in jobs if j['state'] == s])
               for s in ['pending', 'processing', 'completed', 'failed', 'dead']}
    
    click.echo("\nSummary:")
    for state, count in summary.items():
        click.echo(f"  {state}: {count}")


@cli.command()
@click.option('--state', default=None, help='List jobs by state')
def list(state):
    """List jobs (optionally filtered by state)"""
    try:
        storage.init_storage()
    except Exception as e:
        click.echo(f"❌ Storage init failed: {e}")
        return

    jobs = storage.list_jobs(state=state) if state else storage.list_jobs()
    if not jobs:
        click.echo("No jobs found.")
        return

    for j in jobs:
        click.echo(json.dumps(j, ensure_ascii=False))

@cli.command()
def run():
    """Run pending jobs from the queue."""

    from storage import load_jobs, save_jobs
    jobs = load_jobs()

    pending_jobs = [job for job in jobs if job['state'] == 'pending']

    if not pending_jobs:
        click.echo("⚡ No pending jobs to run.")
        return

    for job in pending_jobs:
        click.echo(f"▶️ Running job {job['id']}: {job['command']}")
        job['state'] = 'processing'
        save_jobs(jobs)
        time.sleep(1)  # Simulate work

        try:
            result = subprocess.run(job['command'], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                job['state'] = 'completed'
                click.echo(f"✅ Job {job['id']} completed successfully.")
            else:
                job['state'] = 'failed'
                click.echo(f"❌ Job {job['id']} failed: {result.stderr.strip()}")
        except Exception as e:
            job['state'] = 'failed'
            click.echo(f"💥 Error executing job {job['id']}: {e}")

        save_jobs(jobs)

@cli.command()
@click.option('--interval', default=5, help='Polling interval in seconds.')
def worker(interval):
    """Start a simple background worker that executes pending jobs automatically with retry logic."""
    import time, subprocess
    from storage import load_jobs, save_jobs

    click.echo(f"🧠 Worker started — polling every {interval} seconds. Press Ctrl+C to stop.")
    
    try:
        while True:
            jobs = load_jobs()
            pending_jobs = [j for j in jobs if j['state'] == 'pending']
            
            if pending_jobs:
                job = pending_jobs[0]
                click.echo(f"▶️ Running job {job['id']}: {job['command']}")
                job['state'] = 'processing'
                save_jobs(jobs)

                try:
                    result = subprocess.run(job['command'], shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        job['state'] = 'completed'
                        click.echo(f"✅ Job {job['id']} completed successfully.")
                    else:
                        job['attempts'] += 1
                        if job['attempts'] < job['max_retries']:
                            job['state'] = 'pending'
                            click.echo(f"🔁 Job {job['id']} failed (attempt {job['attempts']}/{job['max_retries']}). Retrying later...")
                        else:
                            job['state'] = 'dead'
                            click.echo(f"💀 Job {job['id']} permanently failed after {job['attempts']} attempts.")
                except Exception as e:
                    job['attempts'] += 1
                    if job['attempts'] < job['max_retries']:
                        job['state'] = 'pending'
                        click.echo(f"💥 Error executing job {job['id']} (attempt {job['attempts']}/{job['max_retries']}): {e}")
                    else:
                        job['state'] = 'dead'
                        click.echo(f"💀 Job {job['id']} permanently failed due to repeated errors.")

                job['updated_at'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                save_jobs(jobs)
            else:
                click.echo("😴 No pending jobs. Waiting...")
            
            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n🛑 Worker stopped manually.")


if __name__ == '__main__':
    cli()
