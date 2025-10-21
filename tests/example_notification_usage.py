"""
Example usage of the Notification Manager

This script demonstrates how to use the notification system for:
1. Configuring notification preferences
2. Sending daily job digests
3. Sending interview reminders
4. Sending status update notifications
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from models.notification import NotificationPreferences
from models.job import JobListing
from models.application import Application
from utils.notification_manager import (
    NotificationManager, 
    WhatsAppNotificationManager, 
    UnifiedNotificationService
)
from database.db_manager import DatabaseManager
from database.repositories.notification_preferences_repository import NotificationPreferencesRepository


def example_email_only():
    """Example: Send notifications via email only"""
    print("\n" + "="*60)
    print("Example 1: Email-Only Notifications")
    print("="*60 + "\n")
    
    # Initialize email manager with your SMTP settings
    email_manager = NotificationManager(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your-email@gmail.com",
        smtp_password="your-app-password",  # Use app-specific password
        from_address="your-email@gmail.com"
    )
    
    # Create sample job listings
    jobs = [
        JobListing(
            id="job-1",
            title="Senior GenAI Engineer",
            company="Tech Corp",
            salary_min=4000000,
            salary_max=5000000,
            location="Bangalore",
            remote_type="hybrid",
            description="Work on cutting-edge LLM applications",
            required_skills=["Python", "LangChain", "GenAI", "RAG"],
            posted_date=datetime.now(),
            source_url="https://example.com/job1",
            source="naukri",
            raw_html="",
            created_at=datetime.now(),
            match_score=85.0
        ),
        JobListing(
            id="job-2",
            title="LLM Engineer",
            company="AI Startup",
            salary_min=3500000,
            salary_max=4500000,
            location="Remote",
            remote_type="remote",
            description="Build autonomous agents with LangGraph",
            required_skills=["Python", "LangGraph", "Autonomous Agents"],
            posted_date=datetime.now(),
            source_url="https://example.com/job2",
            source="naukri",
            raw_html="",
            created_at=datetime.now(),
            match_score=92.0
        )
    ]
    
    # Send daily digest (this would actually send if credentials are valid)
    print("Sending daily digest email...")
    # success = email_manager.send_daily_digest_email("recipient@example.com", jobs)
    # print(f"Email sent: {success}")
    print("(Skipped actual sending - configure SMTP credentials to test)")
    
    print("\n✓ Email notification example complete")


def example_whatsapp_only():
    """Example: Send notifications via WhatsApp only"""
    print("\n" + "="*60)
    print("Example 2: WhatsApp-Only Notifications")
    print("="*60 + "\n")
    
    # Initialize WhatsApp manager with Twilio credentials
    whatsapp_manager = WhatsAppNotificationManager(
        account_sid="your-twilio-account-sid",
        auth_token="your-twilio-auth-token",
        from_number="whatsapp:+14155238886"  # Twilio sandbox number
    )
    
    # Create sample job
    job = JobListing(
        id="job-1",
        title="GenAI Engineer",
        company="AI Company",
        salary_min=3800000,
        salary_max=None,
        location="Bangalore",
        remote_type="hybrid",
        description="Exciting GenAI role",
        required_skills=["Python", "LLM", "Fine-tuning"],
        posted_date=datetime.now(),
        source_url="https://example.com/job1",
        source="naukri",
        raw_html="",
        created_at=datetime.now(),
        match_score=88.0
    )
    
    # Send new jobs alert (this would actually send if Twilio is configured)
    print("Sending WhatsApp alert...")
    # success = whatsapp_manager.send_new_jobs_alert("whatsapp:+919876543210", [job])
    # print(f"WhatsApp sent: {success}")
    print("(Skipped actual sending - configure Twilio credentials to test)")
    
    print("\n✓ WhatsApp notification example complete")


def example_unified_service():
    """Example: Use unified service with both email and WhatsApp"""
    print("\n" + "="*60)
    print("Example 3: Unified Notification Service")
    print("="*60 + "\n")
    
    # Initialize both managers
    email_manager = NotificationManager(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your-email@gmail.com",
        smtp_password="your-app-password",
        from_address="your-email@gmail.com"
    )
    
    whatsapp_manager = WhatsAppNotificationManager(
        account_sid="your-twilio-account-sid",
        auth_token="your-twilio-auth-token",
        from_number="whatsapp:+14155238886"
    )
    
    # Create unified service without repository for this example
    # In production, you would initialize with a proper database and repository
    unified_service = UnifiedNotificationService(
        email_manager=email_manager,
        whatsapp_manager=whatsapp_manager,
        preferences_repository=None  # Would be initialized with actual DB in production
    )
    
    # Configure user preferences (example - would use repository in production)
    preferences = NotificationPreferences(
        user_id="user-123",
        email_address="user@example.com",
        email_enabled=True,
        whatsapp_enabled=True,
        whatsapp_number="whatsapp:+919876543210",
        daily_digest=True,
        interview_reminders=True,
        status_updates=True,
        digest_time="09:00"
    )
    
    print("Notification preferences configured (example):")
    print(f"  Email: {preferences.email_enabled} ({preferences.email_address})")
    print(f"  WhatsApp: {preferences.whatsapp_enabled} ({preferences.whatsapp_number})")
    print(f"  Daily digest: {preferences.daily_digest} at {preferences.digest_time}")
    
    # Create sample jobs
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
    
    # Send daily digest via both channels
    print("\nSending daily digest via configured channels...")
    # results = unified_service.send_daily_digest("user-123", jobs)
    # print(f"Results: Email={results['email']}, WhatsApp={results['whatsapp']}")
    print("(Skipped actual sending - configure credentials to test)")
    
    # Create sample application with interview
    application = Application(
        id="app-1",
        job_id="job-1",
        user_id="user-123",
        status="interview",
        applied_date=datetime.now(),
        interview_date=datetime.now() + timedelta(hours=24),
        notes="",
        cover_letter=None,
        hr_contact_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Send interview reminder
    print("\nSending interview reminder...")
    # results = unified_service.send_interview_reminder("user-123", application, jobs[0])
    # print(f"Results: Email={results['email']}, WhatsApp={results['whatsapp']}")
    print("(Skipped actual sending - configure credentials to test)")
    
    # Send status update
    print("\nSending status update notification...")
    # results = unified_service.send_status_update("user-123", application, jobs[0], "applied", "interview")
    # print(f"Results: Email={results['email']}, WhatsApp={results['whatsapp']}")
    print("(Skipped actual sending - configure credentials to test)")
    
    print("\n✓ Unified service example complete")


def example_interview_reminder_scheduling():
    """Example: Check and send interview reminders for upcoming interviews"""
    print("\n" + "="*60)
    print("Example 4: Automated Interview Reminder Scheduling")
    print("="*60 + "\n")
    
    # Initialize unified service
    email_manager = NotificationManager(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your-email@gmail.com",
        smtp_password="your-app-password",
        from_address="your-email@gmail.com"
    )
    
    unified_service = UnifiedNotificationService(
        email_manager=email_manager,
        whatsapp_manager=None,
        preferences_repository=None
    )
    
    # Create sample applications with interviews at different times
    now = datetime.now()
    
    applications_with_jobs = [
        # Interview in 24 hours - should send reminder
        (
            "user-1",
            Application(
                id="app-1",
                job_id="job-1",
                user_id="user-1",
                status="interview",
                applied_date=now - timedelta(days=5),
                interview_date=now + timedelta(hours=24),
                notes="",
                cover_letter=None,
                hr_contact_id=None,
                created_at=now,
                updated_at=now
            ),
            JobListing(
                id="job-1",
                title="GenAI Engineer",
                company="Tech Corp",
                salary_min=4000000,
                salary_max=None,
                location="Bangalore",
                remote_type="hybrid",
                description="Great role",
                required_skills=["Python", "GenAI"],
                posted_date=now,
                source_url="https://example.com/job1",
                source="naukri",
                raw_html="",
                created_at=now,
                match_score=85.0
            )
        ),
        # Interview in 48 hours - should NOT send reminder
        (
            "user-2",
            Application(
                id="app-2",
                job_id="job-2",
                user_id="user-2",
                status="interview",
                applied_date=now - timedelta(days=3),
                interview_date=now + timedelta(hours=48),
                notes="",
                cover_letter=None,
                hr_contact_id=None,
                created_at=now,
                updated_at=now
            ),
            JobListing(
                id="job-2",
                title="LLM Engineer",
                company="AI Startup",
                salary_min=3500000,
                salary_max=None,
                location="Remote",
                remote_type="remote",
                description="Exciting opportunity",
                required_skills=["Python", "LLM"],
                posted_date=now,
                source_url="https://example.com/job2",
                source="naukri",
                raw_html="",
                created_at=now,
                match_score=90.0
            )
        )
    ]
    
    print("Checking for interviews requiring reminders...")
    # reminders_sent = unified_service.check_and_send_interview_reminders(applications_with_jobs)
    # print(f"Reminders sent: {reminders_sent}")
    print("(Skipped actual sending - configure credentials to test)")
    print("Expected: 1 reminder (for interview in 24 hours)")
    
    print("\n✓ Interview reminder scheduling example complete")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("NOTIFICATION MANAGER - USAGE EXAMPLES")
    print("="*70)
    
    print("\nThese examples demonstrate how to use the notification system.")
    print("To actually send notifications, update the credentials in each example.")
    
    example_email_only()
    example_whatsapp_only()
    example_unified_service()
    example_interview_reminder_scheduling()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)
    
    print("\nNext Steps:")
    print("1. Update config.yaml with your SMTP and Twilio credentials")
    print("2. Configure notification preferences for users")
    print("3. Integrate with job search and application tracking workflows")
    print("4. Set up scheduled tasks for daily digests and interview reminders")


if __name__ == "__main__":
    main()
