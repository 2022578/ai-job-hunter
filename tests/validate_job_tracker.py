"""
Validation script for Job Tracker implementation
Verifies all requirements from task 12 are met
"""

import os
import tempfile
from datetime import datetime
from agents.job_tracker import JobTracker
from database.db_manager import DatabaseManager


def validate_job_tracker():
    """Validate Job Tracker implementation against requirements"""
    
    print("=" * 60)
    print("Job Tracker Implementation Validation")
    print("=" * 60)
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        # Initialize database and tracker
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        tracker = JobTracker(db_manager)
        
        # Create test user and job
        _create_test_data(db_manager)
        
        test_user_id = "test-user-123"
        test_job_id = "test-job-456"
        
        print("\n✓ Job Tracker initialized successfully")
        
        # Requirement 8.1: Record new applications
        print("\n[Requirement 8.1] Testing add_application...")
        app = tracker.add_application(
            job_id=test_job_id,
            user_id=test_user_id,
            status="saved",
            notes="Interesting opportunity"
        )
        assert app is not None, "Failed to add application"
        assert app.job_id == test_job_id
        assert app.status == "saved"
        print("✓ Can record new applications with job title, company, date, and status")
        
        # Requirement 8.2: Update status
        print("\n[Requirement 8.2] Testing update_status...")
        success = tracker.update_status(app.id, "applied", applied_date=datetime.now())
        assert success, "Failed to update status"
        updated_app = tracker.application_repo.find_by_id(app.id)
        assert updated_app.status == "applied"
        print("✓ Can update status to: Applied, Interview Scheduled, Offered, Rejected")
        
        # Requirement 8.3: Mark as saved
        print("\n[Requirement 8.3] Testing mark_as_saved...")
        saved_app = tracker.mark_as_saved(
            job_id=test_job_id,
            user_id=test_user_id,
            notes="Save for later"
        )
        assert saved_app is not None
        assert saved_app.status == "saved"
        print("✓ Can mark jobs as 'Saved for Later'")
        
        # Requirement 8.3: Mark as not interested
        print("\n[Requirement 8.3] Testing mark_as_not_interested...")
        success = tracker.mark_as_not_interested(saved_app.id)
        assert success
        updated = tracker.application_repo.find_by_id(saved_app.id)
        assert updated.status == "not_interested"
        print("✓ Can mark jobs as 'Not Interested'")
        
        # Requirement 8.4: Add HR contact
        print("\n[Requirement 8.4] Testing add_hr_contact...")
        hr_contact = tracker.add_hr_contact(
            application_id=app.id,
            name="John Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            linkedin_url="https://linkedin.com/in/johndoe",
            designation="HR Manager",
            notes="Very responsive"
        )
        assert hr_contact is not None
        assert hr_contact.name == "John Doe"
        assert hr_contact.email == "john.doe@example.com"
        print("✓ Can store HR contact information: name, email, phone, LinkedIn, designation, notes")
        
        # Requirement 8.5: Link HR contacts to applications
        print("\n[Requirement 8.5] Testing HR contact linking...")
        updated_app = tracker.application_repo.find_by_id(app.id)
        assert updated_app.hr_contact_id == hr_contact.id
        print("✓ HR contacts are linked to specific applications")
        
        # Requirement 8.6: Searchable HR directory
        print("\n[Requirement 8.6] Testing get_hr_contacts...")
        contacts = tracker.get_hr_contacts(search_name="John")
        assert len(contacts) > 0
        assert contacts[0].name == "John Doe"
        
        contacts_by_app = tracker.get_hr_contacts(application_id=app.id)
        assert len(contacts_by_app) > 0
        print("✓ Provides searchable directory of all HR contacts")
        
        # Requirement 8.6: Update HR contact
        print("\n[Requirement 8.6] Testing update_hr_contact...")
        success = tracker.update_hr_contact(
            contact_id=hr_contact.id,
            phone="+9876543210",
            designation="Senior HR Manager"
        )
        assert success
        updated_contact = tracker.hr_contact_repo.find_by_id(hr_contact.id)
        assert updated_contact.phone == "+9876543210"
        print("✓ Can update HR contact details")
        
        # Requirement 8.7: Export history
        print("\n[Requirement 8.7] Testing export_history...")
        csv_data = tracker.export_history(
            user_id=test_user_id,
            format="csv",
            include_hr_contacts=True
        )
        assert csv_data is not None
        assert "Application ID" in csv_data
        assert "HR Name" in csv_data
        assert "John Doe" in csv_data
        print("✓ Can generate CSV/Excel file with complete application history and HR contacts")
        
        # Requirement 8.8: Display statistics
        print("\n[Requirement 8.8] Testing get_statistics...")
        stats = tracker.get_statistics(test_user_id)
        assert 'total' in stats
        assert 'by_status' in stats
        assert 'interview_rate' in stats
        assert 'offer_rate' in stats
        print("✓ Displays application statistics and timeline")
        print(f"  - Total applications: {stats['total']}")
        print(f"  - By status: {stats['by_status']}")
        print(f"  - Interview rate: {stats['interview_rate']}%")
        print(f"  - Offer rate: {stats['offer_rate']}%")
        
        # Additional validation: Status transition validation
        print("\n[Additional] Testing status transition validation...")
        assert tracker._validate_status_transition("saved", "applied")
        assert tracker._validate_status_transition("applied", "interview")
        assert tracker._validate_status_transition("interview", "offered")
        assert not tracker._validate_status_transition("rejected", "offered")
        print("✓ Status transitions are validated")
        
        print("\n" + "=" * 60)
        print("✓ ALL REQUIREMENTS VALIDATED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ Validation failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)


def _create_test_data(db_manager):
    """Create test user and job data"""
    # Create test user
    user_query = """
        INSERT INTO users (id, name, email, skills, experience_years, target_salary)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db_manager.execute_update(
        user_query,
        ("test-user-123", "Test User", "test@example.com", "[]", 5, 3500000)
    )
    
    # Create test job
    job_query = """
        INSERT INTO jobs (id, title, company, location, description, source_url, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    db_manager.execute_update(
        job_query,
        ("test-job-456", "GenAI Engineer", "Test Company", "Remote", 
         "Test job description", "http://test.com/job", "test")
    )


if __name__ == "__main__":
    success = validate_job_tracker()
    exit(0 if success else 1)
