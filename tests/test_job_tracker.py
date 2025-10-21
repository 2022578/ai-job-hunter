"""
Unit tests for Job Tracker agent
"""

import unittest
import os
import tempfile
from datetime import datetime
from agents.job_tracker import JobTracker
from database.db_manager import DatabaseManager
from models.application import Application
from models.hr_contact import HRContact


class TestJobTracker(unittest.TestCase):
    """Test cases for Job Tracker agent"""
    
    def setUp(self):
        """Set up test database and job tracker"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        
        # Initialize database manager
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize_database()
        
        # Initialize job tracker
        self.tracker = JobTracker(self.db_manager)
        
        # Test data
        self.test_user_id = "test-user-123"
        self.test_job_id = "test-job-456"
        
        # Create test user and job to satisfy foreign key constraints
        self._create_test_user()
        self._create_test_job()
    
    def tearDown(self):
        """Clean up test database"""
        self.db_manager.close_connection()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def _create_test_user(self):
        """Create a test user in the database"""
        query = """
            INSERT INTO users (id, name, email, skills, experience_years, target_salary)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db_manager.execute_update(
            query,
            (self.test_user_id, "Test User", "test@example.com", "[]", 5, 3500000)
        )
    
    def _create_test_job(self, job_id=None):
        """Create a test job in the database"""
        if job_id is None:
            job_id = self.test_job_id
        
        query = """
            INSERT INTO jobs (id, title, company, location, description, source_url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db_manager.execute_update(
            query,
            (job_id, "GenAI Engineer", "Test Company", "Remote", "Test job", f"http://test.com/{job_id}", "test")
        )
    
    def test_add_application(self):
        """Test adding a new application"""
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="saved",
            notes="Interesting role"
        )
        
        self.assertIsNotNone(application)
        self.assertEqual(application.job_id, self.test_job_id)
        self.assertEqual(application.user_id, self.test_user_id)
        self.assertEqual(application.status, "saved")
        self.assertEqual(application.notes, "Interesting role")
    
    def test_update_status(self):
        """Test updating application status"""
        # Add application
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="saved"
        )
        
        # Update status
        success = self.tracker.update_status(application.id, "applied")
        self.assertTrue(success)
        
        # Verify update
        updated_app = self.tracker.application_repo.find_by_id(application.id)
        self.assertEqual(updated_app.status, "applied")
    
    def test_status_transition_validation(self):
        """Test status transition validation"""
        # Valid transition: saved -> applied
        self.assertTrue(
            self.tracker._validate_status_transition("saved", "applied")
        )
        
        # Valid transition: applied -> interview
        self.assertTrue(
            self.tracker._validate_status_transition("applied", "interview")
        )
        
        # Invalid transition: rejected -> offered
        self.assertFalse(
            self.tracker._validate_status_transition("rejected", "offered")
        )
        
        # Same status (no-op)
        self.assertTrue(
            self.tracker._validate_status_transition("applied", "applied")
        )
    
    def test_mark_as_saved(self):
        """Test marking a job as saved"""
        application = self.tracker.mark_as_saved(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            notes="Save for later"
        )
        
        self.assertIsNotNone(application)
        self.assertEqual(application.status, "saved")
        self.assertEqual(application.notes, "Save for later")
    
    def test_mark_as_not_interested(self):
        """Test marking application as not interested"""
        # Add application
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="saved"
        )
        
        # Mark as not interested
        success = self.tracker.mark_as_not_interested(application.id)
        self.assertTrue(success)
        
        # Verify status
        updated_app = self.tracker.application_repo.find_by_id(application.id)
        self.assertEqual(updated_app.status, "not_interested")
    
    def test_add_hr_contact(self):
        """Test adding HR contact information"""
        # Add application first
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="applied"
        )
        
        # Add HR contact
        hr_contact = self.tracker.add_hr_contact(
            application_id=application.id,
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            linkedin_url="https://linkedin.com/in/johndoe",
            designation="HR Manager",
            notes="Very responsive"
        )
        
        self.assertIsNotNone(hr_contact)
        self.assertEqual(hr_contact.name, "John Doe")
        self.assertEqual(hr_contact.email, "john.doe@example.com")
        self.assertEqual(hr_contact.phone, "+1234567890")
        self.assertEqual(hr_contact.designation, "HR Manager")
    
    def test_update_hr_contact(self):
        """Test updating HR contact details"""
        # Add application and HR contact
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="applied"
        )
        
        hr_contact = self.tracker.add_hr_contact(
            application_id=application.id,
            name="John Doe",
            email="john.doe@example.com"
        )
        
        # Update HR contact
        success = self.tracker.update_hr_contact(
            contact_id=hr_contact.id,
            phone="+9876543210",
            designation="Senior HR Manager"
        )
        
        self.assertTrue(success)
        
        # Verify update
        updated_contact = self.tracker.hr_contact_repo.find_by_id(hr_contact.id)
        self.assertEqual(updated_contact.phone, "+9876543210")
        self.assertEqual(updated_contact.designation, "Senior HR Manager")
    
    def test_get_hr_contacts_by_application(self):
        """Test getting HR contacts for an application"""
        # Add application and HR contact
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="applied"
        )
        
        self.tracker.add_hr_contact(
            application_id=application.id,
            name="John Doe",
            email="john.doe@example.com"
        )
        
        # Get HR contacts
        contacts = self.tracker.get_hr_contacts(application_id=application.id)
        
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].name, "John Doe")
    
    def test_get_hr_contacts_search(self):
        """Test searching HR contacts"""
        # Create test jobs
        self._create_test_job("job-1")
        self._create_test_job("job-2")
        
        # Add multiple applications and HR contacts
        app1 = self.tracker.add_application(
            job_id="job-1",
            user_id=self.test_user_id,
            status="applied"
        )
        
        app2 = self.tracker.add_application(
            job_id="job-2",
            user_id=self.test_user_id,
            status="applied"
        )
        
        self.tracker.add_hr_contact(
            application_id=app1.id,
            name="John Doe",
            email="john.doe@example.com",
            designation="HR Manager"
        )
        
        self.tracker.add_hr_contact(
            application_id=app2.id,
            name="Jane Smith",
            email="jane.smith@example.com",
            designation="Recruiter"
        )
        
        # Search by name
        contacts = self.tracker.get_hr_contacts(search_name="John")
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].name, "John Doe")
        
        # Search by designation
        contacts = self.tracker.get_hr_contacts(search_designation="Recruiter")
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].name, "Jane Smith")
    
    def test_get_statistics(self):
        """Test getting application statistics"""
        # Create test jobs
        self._create_test_job("job-1")
        self._create_test_job("job-2")
        self._create_test_job("job-3")
        
        # Add multiple applications with different statuses
        self.tracker.add_application(
            job_id="job-1",
            user_id=self.test_user_id,
            status="saved"
        )
        
        app2 = self.tracker.add_application(
            job_id="job-2",
            user_id=self.test_user_id,
            status="applied"
        )
        
        app3 = self.tracker.add_application(
            job_id="job-3",
            user_id=self.test_user_id,
            status="applied"
        )
        
        # Update one to interview
        self.tracker.update_status(app2.id, "interview")
        
        # Update one to offered
        self.tracker.update_status(app3.id, "interview")
        self.tracker.update_status(app3.id, "offered")
        
        # Get statistics
        stats = self.tracker.get_statistics(self.test_user_id)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['by_status']['saved'], 1)
        self.assertEqual(stats['by_status']['interview'], 1)
        self.assertEqual(stats['by_status']['offered'], 1)
        # Interview rate: 1 out of 2 applied (50%)
        # Offer rate: 1 out of 2 applied (50%)
        self.assertEqual(stats['interview_rate'], 50.0)
        self.assertEqual(stats['offer_rate'], 50.0)
    
    def test_export_history_csv(self):
        """Test exporting application history to CSV"""
        # Add application with HR contact
        application = self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="applied",
            notes="Great opportunity"
        )
        
        self.tracker.add_hr_contact(
            application_id=application.id,
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890"
        )
        
        # Export to CSV
        csv_data = self.tracker.export_history(
            user_id=self.test_user_id,
            format="csv",
            include_hr_contacts=True
        )
        
        self.assertIsNotNone(csv_data)
        self.assertIn("Application ID", csv_data)
        self.assertIn("Job ID", csv_data)
        self.assertIn("Status", csv_data)
        self.assertIn("HR Name", csv_data)
        self.assertIn(self.test_job_id, csv_data)
        self.assertIn("John Doe", csv_data)
    
    def test_export_history_without_hr_contacts(self):
        """Test exporting application history without HR contacts"""
        # Add application
        self.tracker.add_application(
            job_id=self.test_job_id,
            user_id=self.test_user_id,
            status="applied"
        )
        
        # Export to CSV without HR contacts
        csv_data = self.tracker.export_history(
            user_id=self.test_user_id,
            format="csv",
            include_hr_contacts=False
        )
        
        self.assertIsNotNone(csv_data)
        self.assertIn("Application ID", csv_data)
        self.assertNotIn("HR Name", csv_data)
    
    def test_get_applications(self):
        """Test getting applications for a user"""
        # Create test jobs
        self._create_test_job("job-1")
        self._create_test_job("job-2")
        
        # Add multiple applications
        self.tracker.add_application(
            job_id="job-1",
            user_id=self.test_user_id,
            status="saved"
        )
        
        self.tracker.add_application(
            job_id="job-2",
            user_id=self.test_user_id,
            status="applied"
        )
        
        # Get all applications
        applications = self.tracker.get_applications(self.test_user_id)
        self.assertEqual(len(applications), 2)
        
        # Get applications by status
        saved_apps = self.tracker.get_applications(
            self.test_user_id,
            status="saved"
        )
        self.assertEqual(len(saved_apps), 1)
        self.assertEqual(saved_apps[0].status, "saved")


if __name__ == '__main__':
    unittest.main()
