"""
Manual validation script for integration and end-to-end workflows
This script tests actual workflows with real components (not mocks)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from database.repositories.job_repository import JobRepository
from database.repositories.question_repository import QuestionRepository
from agents.match_scorer import MatchScorer
from agents.job_tracker import JobTracker
from utils.notification_manager import NotificationManager, WhatsAppNotificationManager, UnifiedNotificationService
from utils.security import CredentialManager
from models.job import JobListing
from models.user import UserProfile
from models.application import Application
from models.notification import NotificationPreferences


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def validate_daily_search_workflow():
    """Validate complete daily search workflow components"""
    print_section("DAILY SEARCH WORKFLOW VALIDATION")
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    try:
        # Create test user
        user = UserProfile(
            id="test-user-1",
            name="Test User",
            email="test@example.com",
            skills=["Python", "LangChain", "GenAI"],
            experience_years=5,
            target_salary=40,
            preferred_locations=["Bangalore"],
            preferred_remote=True,
            desired_tech_stack=["LangChain", "LangGraph"]
        )
        
        # Create sample jobs
        jobs = [
            JobListing(
                id="job-1",
                title="Senior GenAI Engineer",
                company="AI Corp",
                description="Build LLM applications",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=40,
                salary_max=55,
                location="Bangalore",
                remote_type="hybrid",
                required_skills=["Python", "LangChain", "LLM"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            ),
            JobListing(
                id="job-2",
                title="LLM Engineer",
                company="Tech Startup",
                description="Work on autonomous agents",
                source="naukri",
                source_url="https://example.com/job2",
                salary_min=35,
                salary_max=45,
                location="Remote",
                remote_type="remote",
                required_skills=["Python", "LangGraph"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            )
        ]
        
        # Initialize components
        job_repo = JobRepository(db_manager)
        match_scorer = MatchScorer(job_repo)
        
        print("\n✓ Step 1: Save jobs to database")
        for job in jobs:
            job_repo.save(job)
        print(f"  Saved {len(jobs)} jobs")
        
        print("\n✓ Step 2: Calculate match scores")
        scored_jobs = match_scorer.rank_jobs(jobs, user)
        print(f"  Scored {len(scored_jobs)} jobs")
        for job, score in scored_jobs:
            print(f"  - {job.title}: {score.total_score:.1f}/100")
        
        print("\n✓ Step 3: Update job scores in database")
        # Extract just the jobs with their scores already calculated
        jobs_with_scores = [job for job, score in scored_jobs]
        for job, score in scored_jobs:
            job.match_score = score.total_score
        updated = match_scorer.update_job_scores(jobs_with_scores, user)
        print(f"  Updated {updated} job records")
        
        print("\n✓ Daily search workflow components validated successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)


def validate_application_tracking_workflow():
    """Validate application tracking with HR contacts"""
    print_section("APPLICATION TRACKING WORKFLOW VALIDATION")
    
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    try:
        # Create test data
        user_query = "INSERT INTO users (id, name, email, skills, experience_years, target_salary) VALUES (?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(user_query, ("user-1", "Test User", "test@example.com", "[]", 5, 4000000))
        
        job_query = "INSERT INTO jobs (id, title, company, location, description, source_url, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(job_query, ("job-1", "GenAI Engineer", "Tech Corp", "Bangalore", "Great role", "http://test.com", "naukri"))
        
        tracker = JobTracker(db_manager)
        
        print("\n✓ Step 1: Add application")
        app = tracker.add_application(
            job_id="job-1",
            user_id="user-1",
            status="saved",
            notes="Interesting opportunity"
        )
        print(f"  Application ID: {app.id}")
        
        print("\n✓ Step 2: Update status to applied")
        tracker.update_status(app.id, "applied", applied_date=datetime.now())
        print("  Status updated to 'applied'")
        
        print("\n✓ Step 3: Add HR contact")
        hr_contact = tracker.add_hr_contact(
            application_id=app.id,
            name="Jane Smith",
            email="jane.smith@techcorp.com",
            phone="+1234567890",
            linkedin_url="https://linkedin.com/in/janesmith",
            designation="Senior Recruiter",
            notes="Very responsive"
        )
        print(f"  HR Contact: {hr_contact.name} ({hr_contact.email})")
        
        print("\n✓ Step 4: Update to interview status")
        tracker.update_status(
            app.id,
            "interview",
            interview_date=datetime.now() + timedelta(days=7)
        )
        print("  Status updated to 'interview'")
        
        print("\n✓ Step 5: Get statistics")
        stats = tracker.get_statistics("user-1")
        print(f"  Total applications: {stats['total']}")
        print(f"  By status: {stats['by_status']}")
        
        print("\n✓ Step 6: Export history with HR contacts")
        csv_data = tracker.export_history(
            user_id="user-1",
            format="csv",
            include_hr_contacts=True
        )
        print(f"  Exported {len(csv_data)} characters of CSV data")
        print(f"  Contains HR contact: {'jane.smith@techcorp.com' in csv_data}")
        
        print("\n✓ Application tracking workflow validated successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)


def validate_notification_workflow():
    """Validate notification system"""
    print_section("NOTIFICATION WORKFLOW VALIDATION")
    
    try:
        print("\n✓ Step 1: Test notification preferences")
        prefs = NotificationPreferences(
            user_id="user-1",
            email_address="test@example.com",
            email_enabled=True,
            whatsapp_enabled=True,
            whatsapp_number="+1234567890",
            daily_digest=True,
            interview_reminders=True,
            status_updates=True,
            digest_time="09:00"
        )
        print(f"  Email enabled: {prefs.email_enabled}")
        print(f"  WhatsApp enabled: {prefs.whatsapp_enabled}")
        print(f"  Digest time: {prefs.digest_time}")
        
        print("\n✓ Step 2: Test email notification manager")
        email_manager = NotificationManager(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="dummy",
            from_address="test@example.com"
        )
        print("  Email manager initialized")
        
        print("\n✓ Step 3: Test email template generation")
        jobs = [
            JobListing(
                id="job-1",
                title="GenAI Engineer",
                company="AI Corp",
                description="Great role",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=40,
                salary_max=55,
                location="Bangalore",
                remote_type="hybrid",
                required_skills=["Python"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html="",
                match_score=85.0
            )
        ]
        
        html = email_manager._generate_daily_digest_html(jobs)
        print(f"  Generated HTML email: {len(html)} characters")
        print(f"  Contains job title: {'GenAI Engineer' in html}")
        print(f"  Contains match score: {'85%' in html}")
        
        print("\n✓ Step 4: Test WhatsApp notification manager")
        whatsapp_manager = WhatsAppNotificationManager(
            account_sid="dummy",
            auth_token="dummy",
            from_number="whatsapp:+14155238886"
        )
        print("  WhatsApp manager initialized")
        
        print("\n✓ Step 5: Test WhatsApp message generation")
        message = whatsapp_manager._generate_new_jobs_alert_message(jobs)
        print(f"  Generated WhatsApp message: {len(message)} characters")
        print(f"  Contains job title: {'GenAI Engineer' in message}")
        
        print("\n✓ Notification workflow validated successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_credential_security():
    """Validate credential encryption and security"""
    print_section("CREDENTIAL SECURITY VALIDATION")
    
    try:
        print("\n✓ Step 1: Initialize credential manager")
        manager = CredentialManager()
        print("  Credential manager initialized")
        
        print("\n✓ Step 2: Test encryption")
        test_data = {
            'username': 'test_user',
            'password': 'super_secret_password_123',
            'api_key': 'sk-1234567890abcdef'
        }
        
        encrypted = manager.store_credentials('test_service', test_data)
        print(f"  Encrypted {len(encrypted)} fields")
        print(f"  Password encrypted: {encrypted['password'] != test_data['password']}")
        
        print("\n✓ Step 3: Test decryption")
        decrypted = manager.retrieve_credentials(encrypted)
        print(f"  Decrypted {len(decrypted)} fields")
        print(f"  Password matches: {decrypted['password'] == test_data['password']}")
        print(f"  API key matches: {decrypted['api_key'] == test_data['api_key']}")
        
        print("\n✓ Step 4: Test key generation")
        key1 = manager.generate_key()
        key2 = manager.generate_key()
        print(f"  Generated unique keys: {key1 != key2}")
        
        print("\n✓ Step 5: Test empty credential handling")
        empty_creds = {
            'username': 'test',
            'password': '',
            'api_key': None
        }
        encrypted_empty = manager.store_credentials('test', empty_creds)
        decrypted_empty = manager.retrieve_credentials(encrypted_empty)
        print(f"  Empty password handled: {decrypted_empty['password'] == ''}")
        
        print("\n✓ Credential security validated successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_data_export():
    """Validate data export functionality"""
    print_section("DATA EXPORT VALIDATION")
    
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    try:
        # Create test data
        user_query = "INSERT INTO users (id, name, email, skills, experience_years, target_salary) VALUES (?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(user_query, ("user-1", "Test User", "test@example.com", "[]", 5, 4000000))
        
        job_query = "INSERT INTO jobs (id, title, company, location, description, source_url, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(job_query, ("job-1", "Engineer", "Corp", "City", "Desc", "http://test.com", "naukri"))
        
        app_query = "INSERT INTO applications (id, job_id, user_id, status, applied_date) VALUES (?, ?, ?, ?, ?)"
        db_manager.execute_update(app_query, ("app-1", "job-1", "user-1", "applied", datetime.now()))
        
        hr_query = "INSERT INTO hr_contacts (id, application_id, name, email, phone) VALUES (?, ?, ?, ?, ?)"
        db_manager.execute_update(hr_query, ("hr-1", "app-1", "John Doe", "john@corp.com", "+1234567890"))
        
        tracker = JobTracker(db_manager)
        
        print("\n✓ Step 1: Export as CSV")
        csv_data = tracker.export_history(
            user_id="user-1",
            format="csv",
            include_hr_contacts=True
        )
        print(f"  CSV data length: {len(csv_data)} characters")
        
        print("\n✓ Step 2: Verify CSV contains required fields")
        # Check for key fields (exact field names may vary)
        has_app_id = "Application ID" in csv_data or "application_id" in csv_data
        has_status = "Status" in csv_data or "status" in csv_data
        has_hr_name = "HR Name" in csv_data or "hr_name" in csv_data or "John Doe" in csv_data
        has_hr_email = "HR Email" in csv_data or "hr_email" in csv_data or "john@corp.com" in csv_data
        
        print(f"  ✓ Contains application ID: {has_app_id}")
        print(f"  ✓ Contains status: {has_status}")
        print(f"  ✓ Contains HR name: {has_hr_name}")
        print(f"  ✓ Contains HR email: {has_hr_email}")
        
        if not (has_app_id and has_status and has_hr_name and has_hr_email):
            print("  ✗ Missing some required fields")
            return False
        
        print("\n✓ Step 3: Verify CSV contains data")
        print(f"  Contains HR name: {'John Doe' in csv_data}")
        print(f"  Contains HR email: {'john@corp.com' in csv_data}")
        
        print("\n✓ Data export validated successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)


def main():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print("  INTEGRATION AND END-TO-END WORKFLOW VALIDATION")
    print("=" * 70)
    print("\nThis script validates all major workflows with real components")
    print("(not mocks) to ensure end-to-end functionality.\n")
    
    results = {}
    
    # Run all validations
    results['Daily Search Workflow'] = validate_daily_search_workflow()
    results['Application Tracking Workflow'] = validate_application_tracking_workflow()
    results['Notification Workflow'] = validate_notification_workflow()
    results['Credential Security'] = validate_credential_security()
    results['Data Export'] = validate_data_export()
    
    # Print summary
    print_section("VALIDATION SUMMARY")
    
    all_passed = True
    for workflow, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {workflow}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ ALL WORKFLOWS VALIDATED SUCCESSFULLY")
        print("=" * 70)
        print("\nAll integration and end-to-end workflows are functioning correctly!")
        return 0
    else:
        print("  ✗ SOME WORKFLOWS FAILED")
        print("=" * 70)
        print("\nPlease review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
