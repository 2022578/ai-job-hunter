"""
Task Scheduler for Autonomous Daily Job Searches
Implements background scheduling using APScheduler for automated job discovery.
"""

import logging
import signal
import sys
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import yaml
import os

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Scheduler for autonomous daily job searches and other periodic tasks.
    Runs independently of the Streamlit UI as a background service.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize Task Scheduler.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.scheduler = BackgroundScheduler()
        self._setup_event_listeners()
        self._shutdown_requested = False
        
        logger.info("TaskScheduler initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _setup_event_listeners(self):
        """Set up event listeners for job execution monitoring."""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
    
    def _job_executed_listener(self, event):
        """
        Listener for successful job execution.
        
        Args:
            event: Job execution event
        """
        logger.info(f"Job '{event.job_id}' executed successfully at {datetime.now()}")
    
    def _job_error_listener(self, event):
        """
        Listener for job execution errors.
        
        Args:
            event: Job error event
        """
        logger.error(f"Job '{event.job_id}' failed with exception: {event.exception}")
        
        # Send error notification if notification service is available
        try:
            self._send_error_notification(event.job_id, event.exception)
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def _send_error_notification(self, job_id: str, exception: Exception):
        """
        Send error notification for failed job execution.
        
        Args:
            job_id: ID of the failed job
            exception: Exception that occurred
        """
        # This can be enhanced to send email/WhatsApp notifications
        # For now, just log the error
        logger.error(f"Job execution failed - Job ID: {job_id}, Error: {str(exception)}")
    
    def schedule_daily_search(
        self,
        search_function: Callable,
        cron_expression: Optional[str] = None,
        job_id: str = "daily_job_search"
    ):
        """
        Schedule daily job search with cron-like configuration.
        
        Args:
            search_function: Function to execute for job search
            cron_expression: Cron expression (default: "0 9 * * *" for 9:00 AM daily)
            job_id: Unique identifier for the scheduled job
        """
        try:
            # Use cron expression from config or parameter or default
            if cron_expression is None:
                cron_expression = self.config.get('job_search', {}).get(
                    'search_schedule',
                    '0 9 * * *'
                )
            
            logger.info(f"Scheduling daily search with cron: {cron_expression}")
            
            # Parse cron expression
            # Format: minute hour day month day_of_week
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=search_function,
                trigger=trigger,
                id=job_id,
                name="Daily Job Search",
                replace_existing=True,
                max_instances=1  # Prevent overlapping executions
            )
            
            logger.info(f"Daily search scheduled successfully: {job_id}")
            
            # Log next run time (only available after scheduler starts)
            job = self.scheduler.get_job(job_id)
            if job:
                next_run = getattr(job, 'next_run_time', None)
                if next_run:
                    logger.info(f"Next scheduled run: {next_run}")
                else:
                    logger.info("Next run time will be set when scheduler starts")
            
        except Exception as e:
            logger.error(f"Error scheduling daily search: {e}")
            raise
    
    def schedule_database_backup(
        self,
        backup_function: Callable,
        cron_expression: Optional[str] = None,
        job_id: str = "database_backup"
    ):
        """
        Schedule database backup task.
        
        Args:
            backup_function: Function to execute for database backup
            cron_expression: Cron expression (default: "0 0 * * *" for midnight daily)
            job_id: Unique identifier for the scheduled job
        """
        try:
            # Use cron expression from config or parameter or default
            if cron_expression is None:
                cron_expression = self.config.get('database', {}).get(
                    'backup_schedule',
                    '0 0 * * *'
                )
            
            logger.info(f"Scheduling database backup with cron: {cron_expression}")
            
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=backup_function,
                trigger=trigger,
                id=job_id,
                name="Database Backup",
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"Database backup scheduled successfully: {job_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling database backup: {e}")
            raise
    
    def add_custom_job(
        self,
        job_function: Callable,
        cron_expression: str,
        job_id: str,
        job_name: Optional[str] = None
    ):
        """
        Add a custom scheduled job.
        
        Args:
            job_function: Function to execute
            cron_expression: Cron expression for scheduling
            job_id: Unique identifier for the job
            job_name: Optional human-readable name for the job
        """
        try:
            logger.info(f"Adding custom job '{job_id}' with cron: {cron_expression}")
            
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job to scheduler
            self.scheduler.add_job(
                func=job_function,
                trigger=trigger,
                id=job_id,
                name=job_name or job_id,
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"Custom job '{job_id}' scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error adding custom job '{job_id}': {e}")
            raise
    
    def remove_job(self, job_id: str):
        """
        Remove a scheduled job.
        
        Args:
            job_id: ID of the job to remove
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job '{job_id}' removed successfully")
        except Exception as e:
            logger.error(f"Error removing job '{job_id}': {e}")
            raise
    
    def get_scheduled_jobs(self) -> list:
        """
        Get list of all scheduled jobs.
        
        Returns:
            List of scheduled job information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            # next_run_time is only available after scheduler starts
            next_run = getattr(job, 'next_run_time', None)
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': next_run,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def start(self):
        """
        Start the scheduler.
        This begins background execution of scheduled tasks.
        """
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started successfully")
                
                # Log scheduled jobs
                jobs = self.get_scheduled_jobs()
                if jobs:
                    logger.info(f"Active scheduled jobs: {len(jobs)}")
                    for job in jobs:
                        logger.info(f"  - {job['name']} (ID: {job['id']}): "
                                  f"Next run at {job['next_run_time']}")
                else:
                    logger.warning("No jobs scheduled")
            else:
                logger.warning("Scheduler is already running")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self, wait: bool = True):
        """
        Stop the scheduler gracefully.
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        try:
            if self.scheduler.running:
                logger.info("Stopping scheduler...")
                self.scheduler.shutdown(wait=wait)
                logger.info("Scheduler stopped successfully")
            else:
                logger.warning("Scheduler is not running")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    def is_running(self) -> bool:
        """
        Check if scheduler is running.
        
        Returns:
            True if scheduler is running, False otherwise
        """
        return self.scheduler.running
    
    def setup_signal_handlers(self):
        """
        Set up signal handlers for graceful shutdown.
        Handles SIGINT (Ctrl+C) and SIGTERM signals.
        """
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            signal_name = signal.Signals(signum).name
            logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
            self._shutdown_requested = True
            self.stop(wait=True)
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Signal handlers registered for graceful shutdown")
    
    def run_job_now(self, job_id: str):
        """
        Execute a scheduled job immediately (outside its schedule).
        
        Args:
            job_id: ID of the job to run
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                logger.info(f"Running job '{job_id}' immediately")
                job.func()
                logger.info(f"Job '{job_id}' completed")
            else:
                logger.error(f"Job '{job_id}' not found")
                raise ValueError(f"Job '{job_id}' not found")
        except Exception as e:
            logger.error(f"Error running job '{job_id}': {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information or None if not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                # next_run_time is only available after scheduler starts
                next_run = getattr(job, 'next_run_time', None)
                pending = getattr(job, 'pending', False)
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': next_run,
                    'trigger': str(job.trigger),
                    'pending': pending
                }
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting job status for '{job_id}': {e}")
            return None


def create_scheduler_service(
    orchestrator,
    search_criteria,
    user_profile,
    user_id: str,
    config_path: str = "config/config.yaml"
) -> TaskScheduler:
    """
    Factory function to create and configure a scheduler service.
    
    Args:
        orchestrator: LangGraphOrchestrator instance
        search_criteria: SearchCriteria for job search
        user_profile: UserProfile for scoring
        user_id: User ID for notifications
        config_path: Path to configuration file
        
    Returns:
        Configured TaskScheduler instance
    """
    # Create scheduler
    scheduler = TaskScheduler(config_path=config_path)
    
    # Define search function
    def execute_search():
        """Wrapper function for daily search execution."""
        try:
            logger.info("=== Starting scheduled daily job search ===")
            result = orchestrator.execute_daily_search(
                search_criteria=search_criteria,
                user_profile=user_profile,
                user_id=user_id
            )
            
            if result['success']:
                logger.info(f"Daily search completed successfully: "
                          f"{result['jobs_found']} jobs found, "
                          f"{result['jobs_scored']} jobs scored, "
                          f"notification sent: {result['notification_sent']}")
            else:
                logger.error(f"Daily search failed: {result.get('error', 'Unknown error')}")
            
            logger.info("=== Daily job search completed ===")
            
        except Exception as e:
            logger.error(f"Error during scheduled job search: {e}")
            raise
    
    # Schedule daily search
    scheduler.schedule_daily_search(execute_search)
    
    return scheduler
