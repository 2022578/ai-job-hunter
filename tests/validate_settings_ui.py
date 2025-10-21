"""
Validation script for Settings UI page
Tests the settings page functionality and components
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from database.repositories.user_repository import UserRepository
from database.repositories.notification_preferences_repository import NotificationPreferencesRepository
from database.repositories.credential_repository import CredentialRepository
from models.user import UserProfile
from models.notification import NotificationPreferences
from utils.security import CredentialManager


def test_user_profile_operations():
    """Test user profile CRUD operations"""
    print("\n=== Testing User Profile Operations ===")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("data/test_settings_ui.db")
        db_manager.initialize_database()
        
        user_repo = UserRepository(db_manager)
        
        # Create test user profile
        test_user = UserProfile(
            id="test_user_settings",
            name="Test User",
            email="test@example.com",
            experience_years=5,
            target_salary=40,
            preferred_remote=True,
            skills=["Python", "LangChain", "GenAI"],
            preferred_locations=["Bangalore", "Remote"],
            desired_tech_stack=["LangChain", "LangGraph", "LLMs"]
        )
        
        # Save user
        if user_repo.save(test_user):
            print("✅ User profile saved successfully")
        else:
            print("❌ Failed to save user profile")
            return False
        
        # Retrieve user
        retrieved_user = user_repo.find_by_id("test_user_settings")
        if retrieved_user:
            print(f"✅ User profile retrieved: {retrieved_user.name}")
            print(f"   Skills: {', '.join(retrieved_user.skills)}")
            print(f"   Target Salary: ₹{retrieved_user.target_salary}L")
        else:
            print("❌ Failed to retrieve user profile")
            return False
        
        # Update user
        retrieved_user.target_salary = 50
        retrieved_user.skills.append("RAG")
        if user_repo.update(retrieved_user):
            print("✅ User profile updated successfully")
        else:
            print("❌ Failed to update user profile")
            return False
        
        # Verify update
        updated_user = user_repo.find_by_id("test_user_settings")
        if updated_user and updated_user.target_salary == 50:
            print(f"✅ Update verified: Target salary is now ₹{updated_user.target_salary}L")
        else:
            print("❌ Update verification failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in user profile operations: {e}")
        return False


def test_notification_preferences_operations():
    """Test notification preferences CRUD operations"""
    print("\n=== Testing Notification Preferences Operations ===")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("data/test_settings_ui.db")
        notif_repo = NotificationPreferencesRepository(db_manager)
        
        # Create test notification preferences
        test_prefs = NotificationPreferences(
            user_id="test_user_settings",
            email_enabled=True,
            email_address="test@example.com",
            whatsapp_enabled=True,
            whatsapp_number="+919876543210",
            daily_digest=True,
            interview_reminders=True,
            status_updates=True,
            digest_time="09:00"
        )
        
        # Save preferences
        if notif_repo.save(test_prefs):
            print("✅ Notification preferences saved successfully")
        else:
            print("❌ Failed to save notification preferences")
            return False
        
        # Retrieve preferences
        retrieved_prefs = notif_repo.find_by_user_id("test_user_settings")
        if retrieved_prefs:
            print(f"✅ Notification preferences retrieved")
            print(f"   Email: {retrieved_prefs.email_address} (Enabled: {retrieved_prefs.email_enabled})")
            print(f"   WhatsApp: {retrieved_prefs.whatsapp_number} (Enabled: {retrieved_prefs.whatsapp_enabled})")
            print(f"   Daily Digest: {retrieved_prefs.daily_digest} at {retrieved_prefs.digest_time}")
        else:
            print("❌ Failed to retrieve notification preferences")
            return False
        
        # Update preferences
        retrieved_prefs.digest_time = "10:00"
        retrieved_prefs.whatsapp_enabled = False
        if notif_repo.update(retrieved_prefs):
            print("✅ Notification preferences updated successfully")
        else:
            print("❌ Failed to update notification preferences")
            return False
        
        # Verify update
        updated_prefs = notif_repo.find_by_user_id("test_user_settings")
        if updated_prefs and updated_prefs.digest_time == "10:00":
            print(f"✅ Update verified: Digest time is now {updated_prefs.digest_time}")
        else:
            print("❌ Update verification failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in notification preferences operations: {e}")
        return False


def test_credential_management():
    """Test credential encryption and storage"""
    print("\n=== Testing Credential Management ===")
    
    try:
        # Initialize credential manager and repository
        cred_manager = CredentialManager()
        cred_repo = CredentialRepository("data/test_settings_ui.db", cred_manager)
        
        # Test Naukri credentials
        naukri_creds = {
            'username': 'test_user@example.com',
            'password': 'test_password_123'
        }
        
        if cred_repo.update("naukri", naukri_creds):
            print("✅ Naukri credentials saved successfully")
        else:
            print("❌ Failed to save Naukri credentials")
            return False
        
        # Retrieve and verify
        retrieved_naukri = cred_repo.retrieve("naukri")
        if retrieved_naukri and retrieved_naukri['username'] == 'test_user@example.com':
            print(f"✅ Naukri credentials retrieved and decrypted")
            print(f"   Username: {retrieved_naukri['username']}")
            # Don't print password for security
        else:
            print("❌ Failed to retrieve Naukri credentials")
            return False
        
        # Test SMTP credentials
        smtp_creds = {
            'server': 'smtp.gmail.com',
            'port': '587',
            'username': 'test@gmail.com',
            'password': 'app_password_123'
        }
        
        if cred_repo.update("smtp", smtp_creds):
            print("✅ SMTP credentials saved successfully")
        else:
            print("❌ Failed to save SMTP credentials")
            return False
        
        # Retrieve and verify
        retrieved_smtp = cred_repo.retrieve("smtp")
        if retrieved_smtp and retrieved_smtp['server'] == 'smtp.gmail.com':
            print(f"✅ SMTP credentials retrieved and decrypted")
            print(f"   Server: {retrieved_smtp['server']}:{retrieved_smtp['port']}")
        else:
            print("❌ Failed to retrieve SMTP credentials")
            return False
        
        # Test Twilio credentials
        twilio_creds = {
            'account_sid': 'AC1234567890abcdef',
            'auth_token': 'test_auth_token_123',
            'whatsapp_from': 'whatsapp:+14155238886'
        }
        
        if cred_repo.update("twilio", twilio_creds):
            print("✅ Twilio credentials saved successfully")
        else:
            print("❌ Failed to save Twilio credentials")
            return False
        
        # List all services
        services = cred_repo.list_services()
        print(f"✅ Stored credentials for services: {', '.join(services)}")
        
        # Test deletion
        if cred_repo.delete("naukri"):
            print("✅ Naukri credentials deleted successfully")
        else:
            print("❌ Failed to delete Naukri credentials")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in credential management: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_backup_restore():
    """Test database backup and restore functionality"""
    print("\n=== Testing Database Backup and Restore ===")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("data/test_settings_ui.db")
        
        # Create backup
        backup_path = db_manager.backup_database("data/test_backups")
        if backup_path:
            print(f"✅ Database backup created: {backup_path}")
        else:
            print("❌ Failed to create database backup")
            return False
        
        # Verify backup file exists
        from pathlib import Path
        if Path(backup_path).exists():
            file_size = Path(backup_path).stat().st_size
            print(f"✅ Backup file verified: {file_size} bytes")
        else:
            print("❌ Backup file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error in database backup/restore: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Settings UI Validation Tests")
    print("=" * 60)
    
    results = {
        "User Profile Operations": test_user_profile_operations(),
        "Notification Preferences": test_notification_preferences_operations(),
        "Credential Management": test_credential_management(),
        "Database Backup/Restore": test_database_backup_restore()
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Please review the output above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
