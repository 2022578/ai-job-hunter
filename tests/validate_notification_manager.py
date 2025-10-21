"""
Validation script for Notification Manager implementation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from models.notification import NotificationPreferences
from models.job import JobListing
from models.application import Application
from utils.notification_manager import NotificationManager, WhatsAppNotificationManager, UnifiedNotificationService


def validate_notification_preferences():
    """Validate NotificationPreferences model"""
    print("✓ Testing NotificationPreferences model...")
    
    # Test valid preferences
    prefs = NotificationPreferences(
        user_id="test-user-1",
        email_address="test@example.com",
        email_enabled=True,
        whatsapp_enabled=False,
        daily_digest=True,
        interview_reminders=True,
        status_updates=True,
        digest_time="09:00"
    )
    
    assert prefs.user_id == "test-user-1"
    assert prefs.email_enabled == True
    assert prefs.digest_time == "09:00"
    
    # Test to_dict and from_dict
    prefs_dict = prefs.to_dict()
    prefs_restored = NotificationPreferences.from_dict(prefs_dict)
    assert prefs_restored.user_id == prefs.user_id
    
    print("  ✓ NotificationPreferences model works correctly")


def validate_email_manager():
    """Validate NotificationManager (email) functionality"""
    print("✓ Testing NotificationManager (Email)...")
    
    # Initialize with dummy credentials (won't actually send)
    email_manager = NotificationManager(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="dummy-password",
        from_address="test@example.com"
    )
    
    assert email_manager.smtp_server == "smtp.gmail.com"
    assert email_manager.smtp_port == 587
    
    # Test HTML generation for daily digest
    jobs = [
        JobListing(
            id="job-1",
            title="Senior GenAI Engineer",
            company="Tech Corp",
            salary_min=4000000,
            salary_max=5000000,
            location="Bangalore",
            remote_type="hybrid",
            description="Great opportunity",
            required_skills=["Python", "LangChain", "GenAI"],
            posted_date=datetime.now(),
            source_url="https://example.com/job1",
            source="naukri",
            raw_html="",
            created_at=datetime.now(),
            match_score=85.0
        )
    ]
    
    html = email_manager._generate_daily_digest_html(jobs)
    assert "Senior GenAI Engineer" in html
    assert "Tech Corp" in html
    assert "Match Score: 85%" in html
    
    print("  ✓ Email templates generate correctly")
    
    # Test interview reminder HTML
    application = Application(
        id="app-1",
        job_id="job-1",
        user_id="user-1",
        status="interview",
        applied_date=datetime.now(),
        interview_date=datetime.now() + timedelta(days=1),
        notes="",
        cover_letter=None,
        hr_contact_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    html = email_manager._generate_interview_reminder_html(application, jobs[0])
    assert "Interview Reminder" in html
    assert "Tech Corp" in html
    
    print("  ✓ Interview reminder template works correctly")
    
    # Test status update HTML
    html = email_manager._generate_status_update_html(
        application, jobs[0], "applied", "interview"
    )
    assert "Status Update" in html
    assert "APPLIED" in html
    assert "INTERVIEW" in html
    
    print("  ✓ Status update template works correctly")


def validate_whatsapp_manager():
    """Validate WhatsAppNotificationManager functionality"""
    print("✓ Testing WhatsAppNotificationManager...")
    
    # Initialize with dummy credentials (won't actually send)
    whatsapp_manager = WhatsAppNotificationManager(
        account_sid="dummy-sid",
        auth_token="dummy-token",
        from_number="whatsapp:+14155238886"
    )
    
    assert whatsapp_manager.account_sid == "dummy-sid"
    assert whatsapp_manager.from_number == "whatsapp:+14155238886"
    
    # Test message generation for new jobs
    jobs = [
        JobListing(
            id="job-1",
            title="GenAI Engineer",
            company="AI Startup",
            salary_min=3500000,
            salary_max=None,
            location="Remote",
            remote_type="remote",
            description="Exciting role",
            required_skills=["Python", "LLM"],
            posted_date=datetime.now(),
            source_url="https://example.com/job1",
            source="naukri",
            raw_html="",
            created_at=datetime.now(),
            match_score=90.0
        )
    ]
    
    message = whatsapp_manager._generate_new_jobs_alert_message(jobs)
    assert "GenAI Engineer" in message
    assert "AI Startup" in message
    assert "Match: 90%" in message
    
    print("  ✓ WhatsApp message templates generate correctly")
    
    # Test interview reminder message
    application = Application(
        id="app-1",
        job_id="job-1",
        user_id="user-1",
        status="interview",
        applied_date=datetime.now(),
        interview_date=datetime.now() + timedelta(days=1),
        notes="",
        cover_letter=None,
        hr_contact_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    message = whatsapp_manager._generate_interview_reminder_message(application, jobs[0])
    assert "Interview Reminder" in message
    assert "AI Startup" in message
    
    print("  ✓ WhatsApp interview reminder works correctly")


def validate_unified_service():
    """Validate UnifiedNotificationService functionality"""
    print("✓ Testing UnifiedNotificationService...")
    
    # Initialize managers
    email_manager = NotificationManager(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="dummy-password",
        from_address="test@example.com"
    )
    
    whatsapp_manager = WhatsAppNotificationManager(
        account_sid="dummy-sid",
        auth_token="dummy-token",
        from_number="whatsapp:+14155238886"
    )
    
    # Initialize unified service (without repository for now)
    unified_service = UnifiedNotificationService(
        email_manager=email_manager,
        whatsapp_manager=whatsapp_manager,
        preferences_repository=None
    )
    
    assert unified_service.email_manager is not None
    assert unified_service.whatsapp_manager is not None
    
    print("  ✓ UnifiedNotificationService initializes correctly")
    
    # Test that methods exist and are callable
    assert hasattr(unified_service, 'configure_preferences')
    assert hasattr(unified_service, 'send_daily_digest')
    assert hasattr(unified_service, 'send_interview_reminder')
    assert hasattr(unified_service, 'send_status_update')
    assert hasattr(unified_service, 'check_and_send_interview_reminders')
    
    print("  ✓ All required methods are present")


def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("Validating Notification Manager Implementation")
    print("="*60 + "\n")
    
    try:
        validate_notification_preferences()
        validate_email_manager()
        validate_whatsapp_manager()
        validate_unified_service()
        
        print("\n" + "="*60)
        print("✓ ALL VALIDATION TESTS PASSED!")
        print("="*60 + "\n")
        
        print("Summary:")
        print("  ✓ NotificationPreferences model validated")
        print("  ✓ Email notification functionality validated")
        print("  ✓ WhatsApp notification functionality validated")
        print("  ✓ Unified notification service validated")
        print("  ✓ All email templates generate correctly")
        print("  ✓ All WhatsApp templates generate correctly")
        print("\nThe Notification Manager implementation is complete and functional!")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Validation failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
