"""
Simple example demonstrating Task Scheduler usage.
This is a minimal example that doesn't require full agent initialization.
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scheduler import TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_job():
    """Example job function that will be scheduled."""
    logger.info(f"Example job executed at {datetime.now()}")
    print(f"✓ Job executed at {datetime.now()}")


def main():
    """Main example demonstrating scheduler usage."""
    print("\n" + "=" * 60)
    print("Task Scheduler Example")
    print("=" * 60 + "\n")
    
    # Create scheduler
    print("1. Creating scheduler...")
    scheduler = TaskScheduler(config_path="config/config.yaml")
    print("   ✓ Scheduler created\n")
    
    # Schedule a job to run every minute
    print("2. Scheduling job (runs every minute)...")
    scheduler.add_custom_job(
        job_function=example_job,
        cron_expression='* * * * *',  # Every minute
        job_id='example_job',
        job_name='Example Job'
    )
    print("   ✓ Job scheduled\n")
    
    # Set up signal handlers for graceful shutdown
    print("3. Setting up signal handlers...")
    scheduler.setup_signal_handlers()
    print("   ✓ Signal handlers configured\n")
    
    # Start scheduler
    print("4. Starting scheduler...")
    scheduler.start()
    print("   ✓ Scheduler started\n")
    
    # Display scheduled jobs
    print("5. Active jobs:")
    jobs = scheduler.get_scheduled_jobs()
    for job in jobs:
        print(f"   - {job['name']} (ID: {job['id']})")
        print(f"     Next run: {job['next_run_time']}")
    print()
    
    # Run job immediately as a test
    print("6. Running job immediately (test)...")
    scheduler.run_job_now('example_job')
    print()
    
    # Keep running
    print("7. Scheduler is now running in background.")
    print("   The job will execute every minute.")
    print("   Press Ctrl+C to stop.\n")
    print("=" * 60 + "\n")
    
    try:
        while scheduler.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        scheduler.stop(wait=True)
        print("Scheduler stopped.\n")


if __name__ == "__main__":
    main()
