# Task Scheduler Documentation

## Overview

The Task Scheduler provides autonomous scheduling capabilities for the GenAI Job Assistant. It runs independently of the Streamlit UI as a background service, enabling automated daily job searches and other periodic tasks.

## Features

- **Cron-based Scheduling**: Flexible scheduling using standard cron expressions
- **Background Execution**: Runs independently of the Streamlit UI
- **Graceful Shutdown**: Handles SIGINT and SIGTERM signals for clean shutdown
- **Job Monitoring**: Event listeners for job execution and error tracking
- **Error Notifications**: Logs errors and can send notifications on failures
- **Multiple Jobs**: Support for scheduling multiple concurrent jobs
- **Immediate Execution**: Ability to run scheduled jobs on-demand

## Architecture

```
┌─────────────────────────────────────────┐
│         Task Scheduler Service          │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   APScheduler (Background)        │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  Daily Job Search           │ │ │
│  │  │  (9:00 AM daily)            │ │ │
│  │  └─────────────────────────────┘ │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  Database Backup            │ │ │
│  │  │  (Midnight daily)           │ │ │
│  │  └─────────────────────────────┘ │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │  Custom Jobs                │ │ │
│  │  └─────────────────────────────┘ │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Event Listeners:                       │
│  - Job Executed                         │
│  - Job Error                            │
└─────────────────────────────────────────┘
```

## Usage

### Running as a Background Service

The scheduler can be run as a standalone background service:

```bash
python scripts/run_scheduler.py
```

This will:
1. Load configuration from `config/config.yaml`
2. Initialize all agents and dependencies
3. Schedule the daily job search
4. Run continuously until stopped (Ctrl+C)

### Programmatic Usage

```python
from utils.scheduler import TaskScheduler

# Initialize scheduler
scheduler = TaskScheduler(config_path="config/config.yaml")

# Schedule daily search
def my_search_function():
    print("Executing search...")

scheduler.schedule_daily_search(
    search_function=my_search_function,
    cron_expression='0 9 * * *',  # 9:00 AM daily
    job_id='daily_search'
)

# Start scheduler
scheduler.start()

# Keep running
try:
    while scheduler.is_running():
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.stop()
```

### Scheduling Custom Jobs

```python
# Add a custom job
scheduler.add_custom_job(
    job_function=my_custom_function,
    cron_expression='0 */6 * * *',  # Every 6 hours
    job_id='custom_job',
    job_name='My Custom Job'
)

# Run a job immediately (outside its schedule)
scheduler.run_job_now('custom_job')

# Remove a job
scheduler.remove_job('custom_job')
```

### Monitoring Jobs

```python
# Get all scheduled jobs
jobs = scheduler.get_scheduled_jobs()
for job in jobs:
    print(f"{job['name']}: Next run at {job['next_run_time']}")

# Get specific job status
status = scheduler.get_job_status('daily_search')
if status:
    print(f"Next run: {status['next_run_time']}")
```

## Cron Expression Format

Cron expressions use 5 fields:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Examples

- `0 9 * * *` - Every day at 9:00 AM
- `0 */6 * * *` - Every 6 hours
- `*/30 * * * *` - Every 30 minutes
- `0 0 * * 0` - Every Sunday at midnight
- `0 9 * * 1-5` - Weekdays at 9:00 AM

## Configuration

The scheduler reads configuration from `config/config.yaml`:

```yaml
job_search:
  search_schedule: "0 9 * * *"  # Daily at 9:00 AM
  keywords:
    - "GenAI"
    - "LLM"
  min_salary: 3500000

database:
  backup_schedule: "0 0 * * *"  # Daily at midnight
  backup_enabled: true
```

## Logging

The scheduler logs to:
- **File**: `logs/scheduler.log`
- **Console**: Standard output

Log levels:
- `INFO`: Normal operations, job executions
- `ERROR`: Job failures, exceptions
- `WARNING`: Non-critical issues

## Error Handling

### Job Execution Errors

When a scheduled job fails:
1. Error is logged with full stack trace
2. Error event listener is triggered
3. Job remains scheduled for next execution
4. Optional error notification can be sent

### Graceful Shutdown

The scheduler handles shutdown signals:
- `SIGINT` (Ctrl+C): Graceful shutdown
- `SIGTERM`: Graceful shutdown

During shutdown:
1. Signal is caught
2. Running jobs are allowed to complete (configurable)
3. Scheduler stops cleanly
4. Resources are released

## Best Practices

### 1. Job Function Design

```python
def my_job_function():
    """Job functions should be self-contained and handle errors."""
    try:
        # Your job logic here
        logger.info("Job started")
        # ... do work ...
        logger.info("Job completed")
    except Exception as e:
        logger.error(f"Job failed: {e}")
        # Don't raise - let scheduler continue
```

### 2. Avoid Overlapping Executions

The scheduler prevents overlapping executions by default:

```python
scheduler.add_custom_job(
    job_function=long_running_job,
    cron_expression='0 * * * *',
    job_id='my_job',
    # max_instances=1 is set automatically
)
```

### 3. Resource Management

```python
def cleanup_job():
    """Jobs should clean up resources."""
    connection = None
    try:
        connection = get_database_connection()
        # ... do work ...
    finally:
        if connection:
            connection.close()
```

### 4. Testing Schedules

Use shorter intervals for testing:

```python
# Production: Daily at 9 AM
# scheduler.schedule_daily_search(func, '0 9 * * *')

# Testing: Every minute
scheduler.schedule_daily_search(func, '* * * * *')
```

## Troubleshooting

### Scheduler Not Starting

**Problem**: Scheduler fails to start

**Solutions**:
- Check configuration file exists and is valid YAML
- Verify all dependencies are installed
- Check logs for initialization errors

### Jobs Not Executing

**Problem**: Scheduled jobs don't run

**Solutions**:
- Verify scheduler is running: `scheduler.is_running()`
- Check cron expression is valid
- Review logs for execution errors
- Ensure job function is callable

### High Memory Usage

**Problem**: Scheduler consumes too much memory

**Solutions**:
- Limit number of concurrent jobs
- Ensure job functions release resources
- Check for memory leaks in job functions
- Monitor with `get_scheduled_jobs()`

## API Reference

### TaskScheduler

#### `__init__(config_path: str)`
Initialize scheduler with configuration file.

#### `schedule_daily_search(search_function, cron_expression=None, job_id='daily_job_search')`
Schedule daily job search with cron configuration.

#### `add_custom_job(job_function, cron_expression, job_id, job_name=None)`
Add a custom scheduled job.

#### `remove_job(job_id)`
Remove a scheduled job.

#### `start()`
Start the scheduler (begins background execution).

#### `stop(wait=True)`
Stop the scheduler gracefully.

#### `is_running() -> bool`
Check if scheduler is running.

#### `run_job_now(job_id)`
Execute a job immediately.

#### `get_scheduled_jobs() -> list`
Get list of all scheduled jobs.

#### `get_job_status(job_id) -> dict`
Get status information for a specific job.

#### `setup_signal_handlers()`
Set up signal handlers for graceful shutdown.

## Examples

### Example 1: Basic Daily Search

```python
from utils.scheduler import TaskScheduler

def daily_search():
    print("Running daily search...")

scheduler = TaskScheduler()
scheduler.schedule_daily_search(daily_search)
scheduler.start()
```

### Example 2: Multiple Jobs

```python
scheduler = TaskScheduler()

# Daily search at 9 AM
scheduler.schedule_daily_search(search_func, '0 9 * * *')

# Database backup at midnight
scheduler.schedule_database_backup(backup_func, '0 0 * * *')

# Custom cleanup every 6 hours
scheduler.add_custom_job(cleanup_func, '0 */6 * * *', 'cleanup')

scheduler.start()
```

### Example 3: With Error Handling

```python
def robust_search():
    try:
        # Search logic
        result = perform_search()
        logger.info(f"Search completed: {result}")
    except Exception as e:
        logger.error(f"Search failed: {e}")
        send_error_notification(e)

scheduler = TaskScheduler()
scheduler.schedule_daily_search(robust_search)
scheduler.setup_signal_handlers()
scheduler.start()
```

## Integration with Streamlit

The scheduler runs independently of Streamlit:

```python
# In your Streamlit app
import streamlit as st
from utils.scheduler import TaskScheduler

# Check scheduler status
scheduler = TaskScheduler()
if st.button("Check Scheduler Status"):
    jobs = scheduler.get_scheduled_jobs()
    st.write(f"Active jobs: {len(jobs)}")
    for job in jobs:
        st.write(f"- {job['name']}: {job['next_run_time']}")
```

## Support

For issues or questions:
1. Check logs in `logs/scheduler.log`
2. Review configuration in `config/config.yaml`
3. Run validation: `python tests/validate_scheduler.py`
4. Check APScheduler documentation: https://apscheduler.readthedocs.io/
