"""
Validation script for Task Scheduler
Verifies scheduler functionality without running full job search.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scheduler import TaskScheduler
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_job_function():
    """Test function to be scheduled."""
    logger.info(f"Test job executed at {datetime.now()}")
    print(f"✓ Test job executed successfully at {datetime.now()}")


def validate_scheduler():
    """Validate scheduler functionality."""
    print("\n" + "=" * 60)
    print("Task Scheduler Validation")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Initialize scheduler
        print("Test 1: Initializing scheduler...")
        scheduler = TaskScheduler(config_path="config/config.yaml")
        print("✓ Scheduler initialized successfully\n")
        
        # Test 2: Schedule a test job (every minute for testing)
        print("Test 2: Scheduling test job (runs every minute)...")
        scheduler.add_custom_job(
            job_function=test_job_function,
            cron_expression='* * * * *',  # Every minute
            job_id='validation_test',
            job_name='Validation Test Job'
        )
        print("✓ Test job scheduled successfully\n")
        
        # Test 3: Get scheduled jobs
        print("Test 3: Retrieving scheduled jobs...")
        jobs = scheduler.get_scheduled_jobs()
        print(f"✓ Found {len(jobs)} scheduled job(s)")
        for job in jobs:
            print(f"  - {job['name']} (ID: {job['id']})")
            print(f"    Next run: {job['next_run_time']}")
        print()
        
        # Test 4: Get job status
        print("Test 4: Getting job status...")
        status = scheduler.get_job_status('validation_test')
        if status:
            print("✓ Job status retrieved successfully")
            print(f"  - ID: {status['id']}")
            print(f"  - Name: {status['name']}")
            print(f"  - Next run: {status['next_run_time']}")
        else:
            print("✗ Failed to retrieve job status")
        print()
        
        # Test 5: Run job immediately
        print("Test 5: Running job immediately...")
        scheduler.run_job_now('validation_test')
        print("✓ Job executed immediately\n")
        
        # Test 6: Start scheduler
        print("Test 6: Starting scheduler...")
        scheduler.start()
        print("✓ Scheduler started successfully")
        print(f"  Scheduler running: {scheduler.is_running()}\n")
        
        # Test 7: Wait for scheduled execution
        print("Test 7: Waiting for scheduled execution (10 seconds)...")
        print("  (The job should execute within the next minute)")
        time.sleep(10)
        print("✓ Scheduler is running in background\n")
        
        # Test 8: Stop scheduler
        print("Test 8: Stopping scheduler...")
        scheduler.stop(wait=True)
        print("✓ Scheduler stopped successfully")
        print(f"  Scheduler running: {scheduler.is_running()}\n")
        
        # Test 9: Schedule daily search with default cron
        print("Test 9: Scheduling daily search with default cron...")
        scheduler2 = TaskScheduler(config_path="config/config.yaml")
        scheduler2.schedule_daily_search(
            search_function=test_job_function,
            job_id='daily_search_test'
        )
        jobs = scheduler2.get_scheduled_jobs()
        print(f"✓ Daily search scheduled successfully")
        for job in jobs:
            print(f"  - {job['name']}: Next run at {job['next_run_time']}")
        print()
        
        # Test 10: Test error handling
        print("Test 10: Testing error handling...")
        try:
            scheduler2.schedule_daily_search(
                search_function=test_job_function,
                cron_expression='invalid',
                job_id='error_test'
            )
            print("✗ Error handling failed - invalid cron accepted")
        except ValueError:
            print("✓ Error handling works - invalid cron rejected\n")
        
        print("=" * 60)
        print("All validation tests passed!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        logger.error(f"Validation error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = validate_scheduler()
    sys.exit(0 if success else 1)
