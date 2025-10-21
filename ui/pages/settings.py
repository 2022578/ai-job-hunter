"""
Settings Page - User preferences, credentials, and configuration
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from database.repositories.user_repository import UserRepository
from database.repositories.notification_preferences_repository import NotificationPreferencesRepository
from database.repositories.credential_repository import CredentialRepository
from models.user import UserProfile
from models.notification import NotificationPreferences
from utils.security import CredentialManager

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables for settings page"""
    if 'settings_saved' not in st.session_state:
        st.session_state.settings_saved = False
    
    if 'credential_manager' not in st.session_state:
        st.session_state.credential_manager = CredentialManager()


def load_user_profile(user_id: str, user_repo: UserRepository) -> Optional[UserProfile]:
    """
    Load user profile from database
    
    Args:
        user_id: User ID to load
        user_repo: User repository instance
        
    Returns:
        UserProfile if found, None otherwise
    """
    try:
        return user_repo.find_by_id(user_id)
    except Exception as e:
        logger.error(f"Failed to load user profile: {e}")
        return None


def load_notification_preferences(user_id: str, notif_repo: NotificationPreferencesRepository) -> Optional[NotificationPreferences]:
    """
    Load notification preferences from database
    
    Args:
        user_id: User ID to load preferences for
        notif_repo: Notification preferences repository instance
        
    Returns:
        NotificationPreferences if found, None otherwise
    """
    try:
        return notif_repo.find_by_user_id(user_id)
    except Exception as e:
        logger.error(f"Failed to load notification preferences: {e}")
        return None


def render_user_profile_section(user_id: str, user_repo: UserRepository):
    """
    Render user profile form section
    
    Args:
        user_id: User ID
        user_repo: User repository instance
    """
    st.subheader("👤 User Profile")
    
    # Load existing profile
    user_profile = load_user_profile(user_id, user_repo)
    
    with st.form("user_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Full Name *",
                value=user_profile.name if user_profile else "",
                help="Your full name"
            )
            
            email = st.text_input(
                "Email Address *",
                value=user_profile.email if user_profile else "",
                help="Your email address"
            )
            
            experience_years = st.number_input(
                "Years of Experience",
                min_value=0,
                max_value=50,
                value=user_profile.experience_years if user_profile else 0,
                step=1,
                help="Total years of professional experience"
            )
        
        with col2:
            target_salary = st.number_input(
                "Target Salary (Lakhs)",
                min_value=0,
                max_value=500,
                value=user_profile.target_salary if user_profile else 35,
                step=5,
                help="Desired annual salary in lakhs"
            )
            
            preferred_remote = st.checkbox(
                "Prefer Remote Work",
                value=user_profile.preferred_remote if user_profile else False,
                help="Check if you prefer remote or hybrid positions"
            )
        
        # Skills
        skills_str = ", ".join(user_profile.skills) if user_profile and user_profile.skills else ""
        skills_input = st.text_area(
            "Skills (comma-separated)",
            value=skills_str,
            help="List your technical skills separated by commas (e.g., Python, LangChain, GenAI)"
        )
        
        # Preferred locations
        locations_str = ", ".join(user_profile.preferred_locations) if user_profile and user_profile.preferred_locations else ""
        locations_input = st.text_area(
            "Preferred Locations (comma-separated)",
            value=locations_str,
            help="List your preferred work locations separated by commas (e.g., Bangalore, Mumbai, Remote)"
        )
        
        # Desired tech stack
        tech_stack_str = ", ".join(user_profile.desired_tech_stack) if user_profile and user_profile.desired_tech_stack else ""
        tech_stack_input = st.text_area(
            "Desired Tech Stack (comma-separated)",
            value=tech_stack_str,
            help="Technologies you want to work with (e.g., LangChain, LangGraph, LLMs, RAG)"
        )
        
        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)
        
        if submitted:
            save_user_profile(
                user_id, name, email, experience_years, target_salary,
                preferred_remote, skills_input, locations_input, tech_stack_input,
                user_repo, user_profile
            )


def save_user_profile(
    user_id: str, name: str, email: str, experience_years: int,
    target_salary: int, preferred_remote: bool, skills_str: str,
    locations_str: str, tech_stack_str: str, user_repo: UserRepository,
    existing_profile: Optional[UserProfile]
):
    """
    Save user profile to database
    
    Args:
        user_id: User ID
        name: User name
        email: User email
        experience_years: Years of experience
        target_salary: Target salary
        preferred_remote: Remote preference
        skills_str: Comma-separated skills
        locations_str: Comma-separated locations
        tech_stack_str: Comma-separated tech stack
        user_repo: User repository instance
        existing_profile: Existing user profile if any
    """
    try:
        # Validate required fields
        if not name or not name.strip():
            st.error("Name is required")
            return
        
        if not email or not email.strip():
            st.error("Email is required")
            return
        
        # Parse comma-separated values
        skills = [s.strip() for s in skills_str.split(',') if s.strip()]
        locations = [l.strip() for l in locations_str.split(',') if l.strip()]
        tech_stack = [t.strip() for t in tech_stack_str.split(',') if t.strip()]
        
        # Create or update profile
        if existing_profile:
            # Update existing profile
            existing_profile.name = name
            existing_profile.email = email
            existing_profile.experience_years = experience_years
            existing_profile.target_salary = target_salary
            existing_profile.preferred_remote = preferred_remote
            existing_profile.skills = skills
            existing_profile.preferred_locations = locations
            existing_profile.desired_tech_stack = tech_stack
            existing_profile.updated_at = datetime.now()
            
            if user_repo.update(existing_profile):
                st.success("✅ Profile updated successfully!")
                st.session_state.settings_saved = True
            else:
                st.error("Failed to update profile")
        else:
            # Create new profile
            new_profile = UserProfile(
                id=user_id,
                name=name,
                email=email,
                experience_years=experience_years,
                target_salary=target_salary,
                preferred_remote=preferred_remote,
                skills=skills,
                preferred_locations=locations,
                desired_tech_stack=tech_stack
            )
            
            if user_repo.save(new_profile):
                st.success("✅ Profile created successfully!")
                st.session_state.settings_saved = True
            else:
                st.error("Failed to create profile")
                
    except Exception as e:
        logger.error(f"Failed to save user profile: {e}", exc_info=True)
        st.error(f"Failed to save profile: {str(e)}")


def render_resume_section(user_id: str, user_repo: UserRepository):
    """
    Render resume upload and management section
    
    Args:
        user_id: User ID
        user_repo: User repository instance
    """
    st.subheader("📄 Resume Management")
    
    # Load existing profile
    user_profile = load_user_profile(user_id, user_repo)
    
    # Display current resume info
    if user_profile and user_profile.resume_path:
        st.info(f"Current resume: {user_profile.resume_path}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Remove Resume"):
                remove_resume(user_id, user_repo, user_profile)
        
        with col2:
            if user_profile.resume_path and Path(user_profile.resume_path).exists():
                with open(user_profile.resume_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Resume",
                        data=f,
                        file_name=Path(user_profile.resume_path).name,
                        mime="application/octet-stream"
                    )
    
    st.markdown("---")
    
    # Upload new resume
    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=['pdf', 'docx', 'txt'],
        help="Upload your resume in PDF, DOCX, or TXT format"
    )
    
    if uploaded_file:
        if st.button("💾 Save Resume"):
            save_resume(user_id, uploaded_file, user_repo, user_profile)
    
    st.markdown("---")
    
    # Manual resume text input
    st.markdown("**Or paste your resume text:**")
    resume_text = st.text_area(
        "Resume Text",
        value=user_profile.resume_text if user_profile else "",
        height=200,
        help="Paste your resume text here"
    )
    
    if st.button("💾 Save Resume Text"):
        save_resume_text(user_id, resume_text, user_repo, user_profile)


def save_resume(user_id: str, uploaded_file, user_repo: UserRepository, existing_profile: Optional[UserProfile]):
    """
    Save uploaded resume file
    
    Args:
        user_id: User ID
        uploaded_file: Uploaded file object
        user_repo: User repository instance
        existing_profile: Existing user profile if any
    """
    try:
        # Create resumes directory if not exists
        resume_dir = Path("data/resumes")
        resume_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = resume_dir / f"{user_id}_{uploaded_file.name}"
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Update profile
        if existing_profile:
            existing_profile.resume_path = str(file_path)
            existing_profile.updated_at = datetime.now()
            
            if user_repo.update(existing_profile):
                st.success(f"✅ Resume saved: {uploaded_file.name}")
            else:
                st.error("Failed to save resume")
        else:
            st.warning("Please create your profile first")
            
    except Exception as e:
        logger.error(f"Failed to save resume: {e}", exc_info=True)
        st.error(f"Failed to save resume: {str(e)}")


def save_resume_text(user_id: str, resume_text: str, user_repo: UserRepository, existing_profile: Optional[UserProfile]):
    """
    Save resume text
    
    Args:
        user_id: User ID
        resume_text: Resume text content
        user_repo: User repository instance
        existing_profile: Existing user profile if any
    """
    try:
        if existing_profile:
            existing_profile.resume_text = resume_text
            existing_profile.updated_at = datetime.now()
            
            if user_repo.update(existing_profile):
                st.success("✅ Resume text saved!")
            else:
                st.error("Failed to save resume text")
        else:
            st.warning("Please create your profile first")
            
    except Exception as e:
        logger.error(f"Failed to save resume text: {e}", exc_info=True)
        st.error(f"Failed to save resume text: {str(e)}")


def remove_resume(user_id: str, user_repo: UserRepository, existing_profile: UserProfile):
    """
    Remove resume file
    
    Args:
        user_id: User ID
        user_repo: User repository instance
        existing_profile: Existing user profile
    """
    try:
        # Delete file if exists
        if existing_profile.resume_path and Path(existing_profile.resume_path).exists():
            Path(existing_profile.resume_path).unlink()
        
        # Update profile
        existing_profile.resume_path = ""
        existing_profile.updated_at = datetime.now()
        
        if user_repo.update(existing_profile):
            st.success("✅ Resume removed!")
            st.rerun()
        else:
            st.error("Failed to remove resume")
            
    except Exception as e:
        logger.error(f"Failed to remove resume: {e}", exc_info=True)
        st.error(f"Failed to remove resume: {str(e)}")


def render_notification_preferences_section(user_id: str, notif_repo: NotificationPreferencesRepository):
    """
    Render notification preferences form section
    
    Args:
        user_id: User ID
        notif_repo: Notification preferences repository instance
    """
    st.subheader("🔔 Notification Preferences")
    
    # Load existing preferences
    notif_prefs = load_notification_preferences(user_id, notif_repo)
    
    with st.form("notification_preferences_form"):
        # Email settings
        st.markdown("**Email Notifications**")
        col1, col2 = st.columns(2)
        
        with col1:
            email_enabled = st.checkbox(
                "Enable Email Notifications",
                value=notif_prefs.email_enabled if notif_prefs else True,
                help="Receive notifications via email"
            )
            
            email_address = st.text_input(
                "Email Address *",
                value=notif_prefs.email_address if notif_prefs else "",
                help="Email address for notifications"
            )
        
        with col2:
            daily_digest = st.checkbox(
                "Daily Digest",
                value=notif_prefs.daily_digest if notif_prefs else True,
                help="Receive daily summary of new jobs"
            )
            
            digest_time = st.time_input(
                "Digest Time",
                value=datetime.strptime(notif_prefs.digest_time if notif_prefs else "09:00", "%H:%M").time(),
                help="Time to receive daily digest"
            )
        
        st.markdown("---")
        
        # WhatsApp settings
        st.markdown("**WhatsApp Notifications**")
        col1, col2 = st.columns(2)
        
        with col1:
            whatsapp_enabled = st.checkbox(
                "Enable WhatsApp Notifications",
                value=notif_prefs.whatsapp_enabled if notif_prefs else False,
                help="Receive notifications via WhatsApp"
            )
            
            whatsapp_number = st.text_input(
                "WhatsApp Number",
                value=notif_prefs.whatsapp_number if notif_prefs else "",
                help="WhatsApp number with country code (e.g., +919876543210)"
            )
        
        with col2:
            interview_reminders = st.checkbox(
                "Interview Reminders",
                value=notif_prefs.interview_reminders if notif_prefs else True,
                help="Receive reminders 24 hours before interviews"
            )
            
            status_updates = st.checkbox(
                "Status Updates",
                value=notif_prefs.status_updates if notif_prefs else True,
                help="Receive notifications when application status changes"
            )
        
        submitted = st.form_submit_button("💾 Save Preferences", use_container_width=True)
        
        if submitted:
            save_notification_preferences(
                user_id, email_enabled, email_address, whatsapp_enabled,
                whatsapp_number, daily_digest, digest_time.strftime("%H:%M"),
                interview_reminders, status_updates, notif_repo, notif_prefs
            )


def save_notification_preferences(
    user_id: str, email_enabled: bool, email_address: str,
    whatsapp_enabled: bool, whatsapp_number: str, daily_digest: bool,
    digest_time: str, interview_reminders: bool, status_updates: bool,
    notif_repo: NotificationPreferencesRepository, existing_prefs: Optional[NotificationPreferences]
):
    """
    Save notification preferences to database
    
    Args:
        user_id: User ID
        email_enabled: Email notifications enabled
        email_address: Email address
        whatsapp_enabled: WhatsApp notifications enabled
        whatsapp_number: WhatsApp number
        daily_digest: Daily digest enabled
        digest_time: Digest time
        interview_reminders: Interview reminders enabled
        status_updates: Status updates enabled
        notif_repo: Notification preferences repository instance
        existing_prefs: Existing preferences if any
    """
    try:
        # Validate required fields
        if not email_address or not email_address.strip():
            st.error("Email address is required")
            return
        
        if whatsapp_enabled and (not whatsapp_number or not whatsapp_number.strip()):
            st.error("WhatsApp number is required when WhatsApp notifications are enabled")
            return
        
        # Create or update preferences
        if existing_prefs:
            # Update existing preferences
            existing_prefs.email_enabled = email_enabled
            existing_prefs.email_address = email_address
            existing_prefs.whatsapp_enabled = whatsapp_enabled
            existing_prefs.whatsapp_number = whatsapp_number
            existing_prefs.daily_digest = daily_digest
            existing_prefs.digest_time = digest_time
            existing_prefs.interview_reminders = interview_reminders
            existing_prefs.status_updates = status_updates
            
            if notif_repo.update(existing_prefs):
                st.success("✅ Notification preferences updated successfully!")
                st.session_state.settings_saved = True
            else:
                st.error("Failed to update notification preferences")
        else:
            # Create new preferences
            new_prefs = NotificationPreferences(
                user_id=user_id,
                email_enabled=email_enabled,
                email_address=email_address,
                whatsapp_enabled=whatsapp_enabled,
                whatsapp_number=whatsapp_number,
                daily_digest=daily_digest,
                digest_time=digest_time,
                interview_reminders=interview_reminders,
                status_updates=status_updates
            )
            
            if notif_repo.save(new_prefs):
                st.success("✅ Notification preferences saved successfully!")
                st.session_state.settings_saved = True
            else:
                st.error("Failed to save notification preferences")
                
    except Exception as e:
        logger.error(f"Failed to save notification preferences: {e}", exc_info=True)
        st.error(f"Failed to save preferences: {str(e)}")


def render_credential_management_section(cred_repo: CredentialRepository):
    """
    Render credential management section
    
    Args:
        cred_repo: Credential repository instance
    """
    st.subheader("🔐 Credential Management")
    
    st.info("All credentials are encrypted before storage. Your data is secure.")
    
    # Tabs for different credential types
    tab1, tab2, tab3 = st.tabs(["Naukri Login", "SMTP Settings", "Twilio Settings"])
    
    with tab1:
        render_naukri_credentials(cred_repo)
    
    with tab2:
        render_smtp_credentials(cred_repo)
    
    with tab3:
        render_twilio_credentials(cred_repo)


def render_naukri_credentials(cred_repo: CredentialRepository):
    """
    Render Naukri credentials form
    
    Args:
        cred_repo: Credential repository instance
    """
    st.markdown("**Naukri.com Login Credentials**")
    st.caption("Required for automated job search")
    
    # Load existing credentials
    existing_creds = cred_repo.retrieve("naukri")
    
    with st.form("naukri_credentials_form"):
        username = st.text_input(
            "Username/Email",
            value=existing_creds.get('username', '') if existing_creds else "",
            help="Your Naukri.com username or email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            help="Your Naukri.com password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            save_btn = st.form_submit_button("💾 Save Credentials", use_container_width=True)
        
        with col2:
            delete_btn = st.form_submit_button("🗑️ Delete Credentials", use_container_width=True)
        
        if save_btn:
            if username and password:
                credentials = {'username': username, 'password': password}
                if cred_repo.update("naukri", credentials):
                    st.success("✅ Naukri credentials saved!")
                else:
                    st.error("Failed to save credentials")
            else:
                st.error("Both username and password are required")
        
        if delete_btn:
            if cred_repo.delete("naukri"):
                st.success("✅ Naukri credentials deleted!")
                st.rerun()
            else:
                st.error("Failed to delete credentials")


def render_smtp_credentials(cred_repo: CredentialRepository):
    """
    Render SMTP credentials form
    
    Args:
        cred_repo: Credential repository instance
    """
    st.markdown("**SMTP Email Settings**")
    st.caption("Required for sending email notifications")
    
    # Load existing credentials
    existing_creds = cred_repo.retrieve("smtp")
    
    with st.form("smtp_credentials_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input(
                "SMTP Server",
                value=existing_creds.get('server', '') if existing_creds else "smtp.gmail.com",
                help="SMTP server address (e.g., smtp.gmail.com)"
            )
            
            smtp_port = st.number_input(
                "SMTP Port",
                min_value=1,
                max_value=65535,
                value=int(existing_creds.get('port', 587)) if existing_creds and existing_creds.get('port') else 587,
                help="SMTP port (usually 587 for TLS)"
            )
        
        with col2:
            smtp_username = st.text_input(
                "Username/Email",
                value=existing_creds.get('username', '') if existing_creds else "",
                help="Your email address"
            )
            
            smtp_password = st.text_input(
                "Password/App Password",
                type="password",
                help="Your email password or app-specific password"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            save_btn = st.form_submit_button("💾 Save Credentials", use_container_width=True)
        
        with col2:
            delete_btn = st.form_submit_button("🗑️ Delete Credentials", use_container_width=True)
        
        if save_btn:
            if smtp_server and smtp_username and smtp_password:
                credentials = {
                    'server': smtp_server,
                    'port': str(smtp_port),
                    'username': smtp_username,
                    'password': smtp_password
                }
                if cred_repo.update("smtp", credentials):
                    st.success("✅ SMTP credentials saved!")
                else:
                    st.error("Failed to save credentials")
            else:
                st.error("All fields are required")
        
        if delete_btn:
            if cred_repo.delete("smtp"):
                st.success("✅ SMTP credentials deleted!")
                st.rerun()
            else:
                st.error("Failed to delete credentials")


def render_twilio_credentials(cred_repo: CredentialRepository):
    """
    Render Twilio credentials form
    
    Args:
        cred_repo: Credential repository instance
    """
    st.markdown("**Twilio WhatsApp Settings**")
    st.caption("Required for sending WhatsApp notifications")
    
    # Load existing credentials
    existing_creds = cred_repo.retrieve("twilio")
    
    with st.form("twilio_credentials_form"):
        account_sid = st.text_input(
            "Account SID",
            value=existing_creds.get('account_sid', '') if existing_creds else "",
            help="Your Twilio Account SID"
        )
        
        auth_token = st.text_input(
            "Auth Token",
            type="password",
            value=existing_creds.get('auth_token', '') if existing_creds else "",
            help="Your Twilio Auth Token"
        )
        
        whatsapp_from = st.text_input(
            "WhatsApp From Number",
            value=existing_creds.get('whatsapp_from', '') if existing_creds else "",
            help="Your Twilio WhatsApp number (e.g., whatsapp:+14155238886)"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            save_btn = st.form_submit_button("💾 Save Credentials", use_container_width=True)
        
        with col2:
            delete_btn = st.form_submit_button("🗑️ Delete Credentials", use_container_width=True)
        
        if save_btn:
            if account_sid and auth_token and whatsapp_from:
                credentials = {
                    'account_sid': account_sid,
                    'auth_token': auth_token,
                    'whatsapp_from': whatsapp_from
                }
                if cred_repo.update("twilio", credentials):
                    st.success("✅ Twilio credentials saved!")
                else:
                    st.error("Failed to save credentials")
            else:
                st.error("All fields are required")
        
        if delete_btn:
            if cred_repo.delete("twilio"):
                st.success("✅ Twilio credentials deleted!")
                st.rerun()
            else:
                st.error("Failed to delete credentials")


def render_search_criteria_section(user_id: str, user_repo: UserRepository):
    """
    Render search criteria configuration section
    
    Args:
        user_id: User ID
        user_repo: User repository instance
    """
    st.subheader("🔍 Search Criteria Configuration")
    
    # Load existing profile
    user_profile = load_user_profile(user_id, user_repo)
    
    with st.form("search_criteria_form"):
        # Keywords
        keywords_str = ", ".join(user_profile.desired_tech_stack) if user_profile and user_profile.desired_tech_stack else "GenAI, LLM, LangChain, LangGraph"
        keywords_input = st.text_area(
            "Search Keywords (comma-separated)",
            value=keywords_str,
            help="Keywords to search for in job listings"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            salary_threshold = st.number_input(
                "Minimum Salary (Lakhs)",
                min_value=0,
                max_value=500,
                value=user_profile.target_salary if user_profile else 35,
                step=5,
                help="Minimum salary threshold for job filtering"
            )
        
        with col2:
            remote_preference = st.selectbox(
                "Remote Preference",
                options=["Any", "Remote Only", "Hybrid", "Onsite"],
                index=0 if not user_profile or not user_profile.preferred_remote else 1,
                help="Preferred work arrangement"
            )
        
        submitted = st.form_submit_button("💾 Save Search Criteria", use_container_width=True)
        
        if submitted:
            save_search_criteria(
                user_id, keywords_input, salary_threshold,
                remote_preference, user_repo, user_profile
            )


def save_search_criteria(
    user_id: str, keywords_str: str, salary_threshold: int,
    remote_preference: str, user_repo: UserRepository,
    existing_profile: Optional[UserProfile]
):
    """
    Save search criteria to user profile
    
    Args:
        user_id: User ID
        keywords_str: Comma-separated keywords
        salary_threshold: Minimum salary threshold
        remote_preference: Remote work preference
        user_repo: User repository instance
        existing_profile: Existing user profile if any
    """
    try:
        # Parse keywords
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        
        # Determine remote preference boolean
        prefer_remote = remote_preference in ["Remote Only", "Hybrid"]
        
        if existing_profile:
            # Update existing profile
            existing_profile.desired_tech_stack = keywords
            existing_profile.target_salary = salary_threshold
            existing_profile.preferred_remote = prefer_remote
            existing_profile.updated_at = datetime.now()
            
            if user_repo.update(existing_profile):
                st.success("✅ Search criteria updated successfully!")
                st.session_state.settings_saved = True
            else:
                st.error("Failed to update search criteria")
        else:
            st.warning("Please create your profile first")
            
    except Exception as e:
        logger.error(f"Failed to save search criteria: {e}", exc_info=True)
        st.error(f"Failed to save search criteria: {str(e)}")


def render_database_management_section(db_manager):
    """
    Render database backup and restore section
    
    Args:
        db_manager: Database manager instance
    """
    st.subheader("💾 Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Backup Database**")
        st.caption("Create a backup of your data")
        
        if st.button("📦 Create Backup", use_container_width=True):
            create_database_backup(db_manager)
    
    with col2:
        st.markdown("**Restore Database**")
        st.caption("Restore from a previous backup")
        
        uploaded_backup = st.file_uploader(
            "Upload Backup File",
            type=['db'],
            help="Select a backup file to restore"
        )
        
        if uploaded_backup:
            if st.button("♻️ Restore from Backup", use_container_width=True):
                restore_database_from_backup(db_manager, uploaded_backup)
    
    st.markdown("---")
    
    # Display backup history
    st.markdown("**Recent Backups**")
    display_backup_history()


def create_database_backup(db_manager):
    """
    Create database backup
    
    Args:
        db_manager: Database manager instance
    """
    try:
        with st.spinner("Creating backup..."):
            backup_path = db_manager.backup_database()
        
        if backup_path:
            st.success(f"✅ Backup created successfully!")
            st.info(f"Backup saved to: {backup_path}")
            
            # Offer download
            if Path(backup_path).exists():
                with open(backup_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Backup",
                        data=f,
                        file_name=Path(backup_path).name,
                        mime="application/octet-stream"
                    )
        else:
            st.error("Failed to create backup")
            
    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        st.error(f"Failed to create backup: {str(e)}")


def restore_database_from_backup(db_manager, uploaded_backup):
    """
    Restore database from backup file
    
    Args:
        db_manager: Database manager instance
        uploaded_backup: Uploaded backup file
    """
    try:
        # Save uploaded file temporarily
        temp_backup_path = Path("data/temp_restore.db")
        with open(temp_backup_path, 'wb') as f:
            f.write(uploaded_backup.getbuffer())
        
        # Confirm restore
        st.warning("⚠️ This will replace your current database. Are you sure?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Yes, Restore", use_container_width=True):
                with st.spinner("Restoring database..."):
                    if db_manager.restore_database(str(temp_backup_path)):
                        st.success("✅ Database restored successfully!")
                        st.info("Please refresh the page to see the changes")
                        
                        # Clean up temp file
                        if temp_backup_path.exists():
                            temp_backup_path.unlink()
                    else:
                        st.error("Failed to restore database")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                # Clean up temp file
                if temp_backup_path.exists():
                    temp_backup_path.unlink()
                st.info("Restore cancelled")
                
    except Exception as e:
        logger.error(f"Failed to restore database: {e}", exc_info=True)
        st.error(f"Failed to restore database: {str(e)}")


def display_backup_history():
    """Display list of recent backups"""
    try:
        backup_dir = Path("data/backups")
        
        if not backup_dir.exists():
            st.info("No backups found")
            return
        
        # Get all backup files
        backup_files = sorted(backup_dir.glob("*.db"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backup_files:
            st.info("No backups found")
            return
        
        # Display recent backups (max 5)
        for backup_file in backup_files[:5]:
            file_stat = backup_file.stat()
            file_size = file_stat.st_size / (1024 * 1024)  # Convert to MB
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(backup_file.name)
            
            with col2:
                st.text(f"{file_size:.2f} MB")
            
            with col3:
                st.text(modified_time.strftime("%Y-%m-%d %H:%M"))
                
    except Exception as e:
        logger.error(f"Failed to display backup history: {e}")
        st.warning("Unable to load backup history")


def render_settings():
    """Main settings page rendering function"""
    st.title("⚙️ Settings")
    st.markdown("Configure your profile, preferences, and credentials")
    st.markdown("---")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Get repositories
        user_id = st.session_state.user_id
        db_manager = st.session_state.db_manager
        
        user_repo = UserRepository(db_manager)
        notif_repo = NotificationPreferencesRepository(db_manager)
        
        # Initialize credential repository with db_manager's db_path
        cred_repo = CredentialRepository(
            db_path=db_manager.db_path,
            credential_manager=st.session_state.credential_manager
        )
        
        # Create tabs for different settings sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👤 Profile",
            "📄 Resume",
            "🔔 Notifications",
            "🔐 Credentials",
            "🔍 Search & Database"
        ])
        
        with tab1:
            render_user_profile_section(user_id, user_repo)
        
        with tab2:
            render_resume_section(user_id, user_repo)
        
        with tab3:
            render_notification_preferences_section(user_id, notif_repo)
        
        with tab4:
            render_credential_management_section(cred_repo)
        
        with tab5:
            render_search_criteria_section(user_id, user_repo)
            st.markdown("---")
            render_database_management_section(db_manager)
        
    except Exception as e:
        logger.error(f"Settings page error: {e}", exc_info=True)
        st.error(f"Failed to load settings page: {str(e)}")
