"""
Validation script for Applications UI
Tests the applications page functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from database.repositories.application_repository import ApplicationRepository
from database.repositories.hr_contact_repository import HRContactRepository
from database.repositories.job_repository import JobRepository
from models.application import Application
from models.hr_contact import HRContact
from models.job import JobListing
from datetime import datetime


def test_applications_ui():
    """Test applications UI functionality"""
    print("=" * 60)
    print("APPLICATIONS UI VALIDATION")
    print("=" * 60)
    
    # Initialize database
    db_path = "data/test_applications_ui.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()  # Initialize schema
    
    # Initialize repositories
    app_repo = ApplicationRepository(db_manager)
    hr_repo = HRContactRepository(db_manager)
    job_repo = JobRepository(db_manager)
    
    user_id = "test_user"
    
    # Create test user
    from models.user import UserProfile
    from database.repositories.user_repository import UserRepository
    
    user_repo = UserRepository(db_manager)
    test_user = UserProfile(
        id=user_id,
        name="Test User",
        email="test@example.com",
        resume_text="Test resume",
        resume_path="",
        skills=["Python", "LangChain"],
        experience_years=5,
        target_salary=40,
        preferred_locations=["Bangalore"],
        preferred_remote=True,
        desired_tech_stack=["LangChain", "LLM"]
    )
    user_repo.save(test_user)
    
    print("\n1. Testing Application Creation")
    print("-" * 60)
    
    # Create test jobs
    job1 = JobListing(
        title="Senior GenAI Engineer",
        company="TechCorp",
        salary_min=40,
        salary_max=60,
        location="Bangalore",
        remote_type="hybrid",
        description="Work on cutting-edge GenAI projects",
        required_skills=["Python", "LangChain", "LLM"],
        posted_date=datetime.now(),
        source_url="https://example.com/job1",
        source="naukri",
        raw_html="<html></html>",
        match_score=85.0
    )
    
    job2 = JobListing(
        title="LLM Research Scientist",
        company="AI Labs",
        salary_min=50,
        salary_max=70,
        location="Remote",
        remote_type="remote",
        description="Research and develop LLM applications",
        required_skills=["Python", "PyTorch", "Transformers"],
        posted_date=datetime.now(),
        source_url="https://example.com/job2",
        source="naukri",
        raw_html="<html></html>",
        match_score=92.0
    )
    
    # Save jobs
    assert job_repo.save(job1), "Failed to save job1"
    assert job_repo.save(job2), "Failed to save job2"
    print("✓ Created 2 test jobs")
    
    # Create applications
    app1 = Application(
        job_id=job1.id,
        user_id=user_id,
        status="applied",
        applied_date=datetime.now(),
        notes="Applied through company website"
    )
    
    app2 = Application(
        job_id=job2.id,
        user_id=user_id,
        status="interview",
        applied_date=datetime.now(),
        interview_date=datetime.now(),
        notes="Interview scheduled for next week"
    )
    
    assert app_repo.save(app1), "Failed to save application 1"
    assert app_repo.save(app2), "Failed to save application 2"
    print("✓ Created 2 applications")
    
    print("\n2. Testing Application Retrieval")
    print("-" * 60)
    
    # Get all applications
    all_apps = app_repo.find_by_user(user_id)
    assert len(all_apps) == 2, f"Expected 2 applications, got {len(all_apps)}"
    print(f"✓ Retrieved {len(all_apps)} applications")
    
    # Get applications by status
    applied_apps = app_repo.find_by_user(user_id, status="applied")
    assert len(applied_apps) == 1, f"Expected 1 applied application, got {len(applied_apps)}"
    print(f"✓ Retrieved {len(applied_apps)} applied applications")
    
    interview_apps = app_repo.find_by_user(user_id, status="interview")
    assert len(interview_apps) == 1, f"Expected 1 interview application, got {len(interview_apps)}"
    print(f"✓ Retrieved {len(interview_apps)} interview applications")
    
    print("\n3. Testing Application Statistics")
    print("-" * 60)
    
    stats = app_repo.get_statistics(user_id)
    print(f"Total applications: {stats['total']}")
    print(f"By status: {stats['by_status']}")
    print(f"Interview rate: {stats['interview_rate']}%")
    print(f"Offer rate: {stats['offer_rate']}%")
    
    assert stats['total'] == 2, f"Expected 2 total applications, got {stats['total']}"
    assert stats['by_status']['applied'] == 1, "Expected 1 applied application"
    assert stats['by_status']['interview'] == 1, "Expected 1 interview application"
    print("✓ Statistics calculated correctly")
    
    print("\n4. Testing HR Contact Management")
    print("-" * 60)
    
    # Create HR contact
    hr_contact = HRContact(
        application_id=app1.id,
        name="John Doe",
        email="john.doe@techcorp.com",
        phone="+91-9876543210",
        linkedin_url="https://linkedin.com/in/johndoe",
        designation="Senior Recruiter",
        notes="Very responsive, prefers email"
    )
    
    assert hr_repo.save(hr_contact), "Failed to save HR contact"
    print("✓ Created HR contact")
    
    # Link HR contact to application
    app1.hr_contact_id = hr_contact.id
    assert app_repo.update(app1), "Failed to link HR contact to application"
    print("✓ Linked HR contact to application")
    
    # Retrieve HR contact
    retrieved_contact = hr_repo.find_by_id(hr_contact.id)
    assert retrieved_contact is not None, "Failed to retrieve HR contact"
    assert retrieved_contact.name == "John Doe", "HR contact name mismatch"
    print("✓ Retrieved HR contact successfully")
    
    # Find HR contacts by application
    app_contacts = hr_repo.find_by_application(app1.id)
    assert len(app_contacts) == 1, f"Expected 1 HR contact, got {len(app_contacts)}"
    print(f"✓ Found {len(app_contacts)} HR contact for application")
    
    print("\n5. Testing HR Contact Search")
    print("-" * 60)
    
    # Search by name
    name_results = hr_repo.search({'name': 'John'})
    assert len(name_results) == 1, f"Expected 1 result for name search, got {len(name_results)}"
    print("✓ Search by name works")
    
    # Search by email
    email_results = hr_repo.search({'email': 'techcorp'})
    assert len(email_results) == 1, f"Expected 1 result for email search, got {len(email_results)}"
    print("✓ Search by email works")
    
    # Search by designation
    designation_results = hr_repo.search({'designation': 'Recruiter'})
    assert len(designation_results) == 1, f"Expected 1 result for designation search, got {len(designation_results)}"
    print("✓ Search by designation works")
    
    print("\n6. Testing Application Status Update")
    print("-" * 60)
    
    # Update status
    assert app_repo.update_status(app1.id, "offered"), "Failed to update status"
    print("✓ Updated application status to 'offered'")
    
    # Verify update
    updated_app = app_repo.find_by_id(app1.id)
    assert updated_app.status == "offered", f"Expected status 'offered', got '{updated_app.status}'"
    print("✓ Status update verified")
    
    # Check updated statistics
    updated_stats = app_repo.get_statistics(user_id)
    assert updated_stats['by_status']['offered'] == 1, "Expected 1 offered application"
    print("✓ Statistics updated correctly")
    
    print("\n7. Testing HR Contact Update")
    print("-" * 60)
    
    # Update HR contact
    hr_contact.phone = "+91-9999999999"
    hr_contact.notes = "Updated phone number"
    assert hr_repo.update(hr_contact), "Failed to update HR contact"
    print("✓ Updated HR contact")
    
    # Verify update
    updated_contact = hr_repo.find_by_id(hr_contact.id)
    assert updated_contact.phone == "+91-9999999999", "Phone number not updated"
    print("✓ HR contact update verified")
    
    print("\n8. Testing Export Data Preparation")
    print("-" * 60)
    
    # Prepare export data (simulating what the UI does)
    export_data = []
    for app in app_repo.find_by_user(user_id):
        job = job_repo.find_by_id(app.job_id)
        
        hr_name = ""
        hr_email = ""
        
        if app.hr_contact_id:
            hr = hr_repo.find_by_id(app.hr_contact_id)
            if hr:
                hr_name = hr.name
                hr_email = hr.email or ""
        
        export_data.append({
            'Job Title': job.title if job else "Unknown",
            'Company': job.company if job else "Unknown",
            'Status': app.status,
            'HR Name': hr_name,
            'HR Email': hr_email
        })
    
    assert len(export_data) == 2, f"Expected 2 export records, got {len(export_data)}"
    assert export_data[0]['HR Name'] == "John Doe" or export_data[1]['HR Name'] == "John Doe", "HR name not in export data"
    print("✓ Export data prepared successfully")
    print(f"  - {len(export_data)} records ready for export")
    
    print("\n9. Testing HR Directory")
    print("-" * 60)
    
    # Get all HR contacts
    all_contacts = hr_repo.find_all()
    assert len(all_contacts) == 1, f"Expected 1 HR contact, got {len(all_contacts)}"
    print(f"✓ Retrieved {len(all_contacts)} HR contacts for directory")
    
    print("\n10. Testing Application Deletion")
    print("-" * 60)
    
    # Delete application
    assert app_repo.delete(app2.id), "Failed to delete application"
    print("✓ Deleted application")
    
    # Verify deletion
    remaining_apps = app_repo.find_by_user(user_id)
    assert len(remaining_apps) == 1, f"Expected 1 remaining application, got {len(remaining_apps)}"
    print("✓ Application deletion verified")
    
    print("\n11. Testing HR Contact Deletion")
    print("-" * 60)
    
    # Unlink HR contact from application first
    updated_app = app_repo.find_by_id(app1.id)
    updated_app.hr_contact_id = None
    assert app_repo.update(updated_app), "Failed to unlink HR contact"
    print("✓ Unlinked HR contact from application")
    
    # Delete HR contact
    assert hr_repo.delete(hr_contact.id), "Failed to delete HR contact"
    print("✓ Deleted HR contact")
    
    # Verify deletion
    remaining_contacts = hr_repo.find_all()
    assert len(remaining_contacts) == 0, f"Expected 0 remaining contacts, got {len(remaining_contacts)}"
    print("✓ HR contact deletion verified")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nApplications UI is ready for use!")
    print("\nKey Features Validated:")
    print("  ✓ Application creation and tracking")
    print("  ✓ Status updates with validation")
    print("  ✓ Application statistics calculation")
    print("  ✓ HR contact management")
    print("  ✓ HR contact search functionality")
    print("  ✓ Export data preparation")
    print("  ✓ HR directory view")
    print("  ✓ Application and HR contact deletion")
    
    # Cleanup (best effort - may fail on Windows due to file locking)
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass  # File is locked, will be cleaned up later


if __name__ == "__main__":
    try:
        test_applications_ui()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
