"""
Unit tests for Task Scheduler
Tests scheduling functionality, job execution, and error handling.
"""

import unittest
import time
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import yaml

from utils.scheduler import TaskScheduler, create_scheduler_service


class TestTaskScheduler(unittest.TestCase):
    """Test cases for TaskScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False
        )
        
        config_data = {
            'job_search': {
                'search_schedule': '0 9 * * *',
                'keywords': ['GenAI', 'LLM']
            },
            'database': {
                'backup_schedule': '0 0 * * *'
            }
        }
        
        yaml.dump(config_data, self.temp_config)
        self.temp_config.close()
        
        self.scheduler = TaskScheduler(config_path=self.temp_config.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.scheduler.is_running():
            self.scheduler.stop(wait=False)
        
        # Remove temporary config file
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes correctly."""
        self.assertIsNotNone(self.scheduler)
        self.assertIsNotNone(self.scheduler.scheduler)
        self.assertFalse(self.scheduler.is_running())
    
    def test_load_config(self):
        """Test configuration loading."""
        config = self.scheduler.config
        self.assertIsNotNone(config)
        self.assertIn('job_search', config)
        self.assertEqual(config['job_search']['search_schedule'], '0 9 * * *')
    
    def test_schedule_daily_search(self):
        """Test scheduling daily search job."""
        mock_function = Mock()
        
        # Schedule job
        self.scheduler.schedule_daily_search(
            search_function=mock_function,
            cron_expression='0 9 * * *',
            job_id='test_daily_search'
        )
        
        # Verify job was added
        jobs = self.scheduler.get_scheduled_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['id'], 'test_daily_search')
    
    def test_schedule_with_invalid_cron(self):
        """Test scheduling with invalid cron expression."""
        mock_function = Mock()
        
        with self.assertRaises(ValueError):
            self.scheduler.schedule_daily_search(
                search_function=mock_function,
                cron_expression='invalid cron',
                job_id='test_invalid'
            )
    
    def test_add_custom_job(self):
        """Test adding custom scheduled job."""
        mock_function = Mock()
        
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='*/5 * * * *',
            job_id='test_custom',
            job_name='Test Custom Job'
        )
        
        # Verify job was added
        jobs = self.scheduler.get_scheduled_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['id'], 'test_custom')
        self.assertEqual(jobs[0]['name'], 'Test Custom Job')
    
    def test_remove_job(self):
        """Test removing scheduled job."""
        mock_function = Mock()
        
        # Add job
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='0 9 * * *',
            job_id='test_remove'
        )
        
        # Verify job exists
        jobs = self.scheduler.get_scheduled_jobs()
        self.assertEqual(len(jobs), 1)
        
        # Remove job
        self.scheduler.remove_job('test_remove')
        
        # Verify job was removed
        jobs = self.scheduler.get_scheduled_jobs()
        self.assertEqual(len(jobs), 0)
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping scheduler."""
        # Start scheduler
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running())
        
        # Stop scheduler
        self.scheduler.stop(wait=False)
        self.assertFalse(self.scheduler.is_running())
    
    def test_run_job_now(self):
        """Test running job immediately."""
        mock_function = Mock()
        
        # Add job
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='0 9 * * *',
            job_id='test_run_now'
        )
        
        # Run job immediately
        self.scheduler.run_job_now('test_run_now')
        
        # Verify function was called
        mock_function.assert_called_once()
    
    def test_get_job_status(self):
        """Test getting job status."""
        mock_function = Mock()
        
        # Add job
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='0 9 * * *',
            job_id='test_status',
            job_name='Test Status Job'
        )
        
        # Get job status
        status = self.scheduler.get_job_status('test_status')
        
        self.assertIsNotNone(status)
        self.assertEqual(status['id'], 'test_status')
        self.assertEqual(status['name'], 'Test Status Job')
        self.assertIsNotNone(status['next_run_time'])
    
    def test_get_job_status_not_found(self):
        """Test getting status for non-existent job."""
        status = self.scheduler.get_job_status('non_existent')
        self.assertIsNone(status)
    
    def test_get_scheduled_jobs(self):
        """Test getting list of scheduled jobs."""
        mock_function = Mock()
        
        # Add multiple jobs
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='0 9 * * *',
            job_id='job1'
        )
        
        self.scheduler.add_custom_job(
            job_function=mock_function,
            cron_expression='0 10 * * *',
            job_id='job2'
        )
        
        # Get jobs
        jobs = self.scheduler.get_scheduled_jobs()
        
        self.assertEqual(len(jobs), 2)
        job_ids = [job['id'] for job in jobs]
        self.assertIn('job1', job_ids)
        self.assertIn('job2', job_ids)


class TestSchedulerService(unittest.TestCase):
    """Test cases for scheduler service creation."""
    
    @patch('utils.scheduler.TaskScheduler')
    def test_create_scheduler_service(self, mock_scheduler_class):
        """Test creating scheduler service with orchestrator."""
        # Create mocks
        mock_orchestrator = Mock()
        mock_search_criteria = Mock()
        mock_user_profile = Mock()
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Create service
        scheduler = create_scheduler_service(
            orchestrator=mock_orchestrator,
            search_criteria=mock_search_criteria,
            user_profile=mock_user_profile,
            user_id='test_user'
        )
        
        # Verify scheduler was created
        self.assertIsNotNone(scheduler)
        mock_scheduler.schedule_daily_search.assert_called_once()


if __name__ == '__main__':
    unittest.main()
