"""
Notification Manager for Email and WhatsApp notifications
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.notification import NotificationPreferences
from models.job import JobListing
from models.application import Application

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages email and WhatsApp notifications for the job assistant"""
    
    def __init__(self, smtp_server: str, smtp_port: int, smtp_username: str, 
                 smtp_password: str, from_address: str):
        """
        Initialize notification manager
        
        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (typically 587 for TLS)
            smtp_username: SMTP username for authentication
            smtp_password: SMTP password or app-specific password
            from_address: Email address to send from
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_address = from_address
        
        logger.info(f"NotificationManager initialized with SMTP server: {smtp_server}")
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Send email notification
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            html: Whether body is HTML formatted
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_address
            msg['To'] = to
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
    
    def _generate_daily_digest_html(self, jobs: List[JobListing]) -> str:
        """
        Generate HTML email template for daily job digest
        
        Args:
            jobs: List of job listings to include
            
        Returns:
            HTML formatted email body
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .job-card { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }
                .job-title { font-size: 18px; font-weight: bold; color: #2196F3; }
                .company { font-size: 16px; color: #666; margin: 5px 0; }
                .details { font-size: 14px; color: #888; margin: 5px 0; }
                .match-score { display: inline-block; padding: 5px 10px; background-color: #4CAF50; 
                              color: white; border-radius: 3px; font-weight: bold; }
                .footer { text-align: center; padding: 20px; color: #888; font-size: 12px; }
                .cta-button { display: inline-block; padding: 10px 20px; background-color: #2196F3; 
                             color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 GenAI Job Assistant - Daily Digest</h1>
                <p>Your personalized job opportunities for """ + datetime.now().strftime('%B %d, %Y') + """</p>
            </div>
            <div style="padding: 20px;">
                <h2>Found """ + str(len(jobs)) + """ New Matching Jobs</h2>
        """
        
        for job in jobs:
            salary_str = ""
            if job.salary_min and job.salary_max:
                salary_str = f"₹{job.salary_min/100000:.1f}L - ₹{job.salary_max/100000:.1f}L"
            elif job.salary_min:
                salary_str = f"₹{job.salary_min/100000:.1f}L+"
            
            match_score_display = f"{job.match_score:.0f}" if job.match_score else "N/A"
            
            html += f"""
                <div class="job-card">
                    <div class="job-title">{job.title}</div>
                    <div class="company">🏢 {job.company}</div>
                    <div class="details">📍 {job.location} | {job.remote_type}</div>
                    {f'<div class="details">💰 {salary_str}</div>' if salary_str else ''}
                    <div class="details">
                        <span class="match-score">Match Score: {match_score_display}%</span>
                    </div>
                    <div class="details" style="margin-top: 10px;">
                        <strong>Skills:</strong> {', '.join(job.required_skills[:5])}
                    </div>
                    <a href="{job.source_url}" class="cta-button">View Job</a>
                </div>
            """
        
        html += """
            </div>
            <div class="footer">
                <p>This is an automated notification from GenAI Job Assistant</p>
                <p>To update your notification preferences, visit the Settings page</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_interview_reminder_html(self, application: Application, 
                                         job: JobListing) -> str:
        """
        Generate HTML email template for interview reminder
        
        Args:
            application: Application with interview details
            job: Associated job listing
            
        Returns:
            HTML formatted email body
        """
        interview_date_str = application.interview_date.strftime('%B %d, %Y at %I:%M %p')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .interview-details {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; 
                                     margin: 15px 0; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
                .cta-button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; 
                              color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⏰ Interview Reminder</h1>
                <p>Your interview is coming up soon!</p>
            </div>
            <div class="content">
                <h2>Interview Details</h2>
                <div class="interview-details">
                    <div class="detail-row">
                        <span class="label">Company:</span> {job.company}
                    </div>
                    <div class="detail-row">
                        <span class="label">Position:</span> {job.title}
                    </div>
                    <div class="detail-row">
                        <span class="label">Date & Time:</span> {interview_date_str}
                    </div>
                    <div class="detail-row">
                        <span class="label">Location:</span> {job.location}
                    </div>
                </div>
                
                <h3>Preparation Tips:</h3>
                <ul>
                    <li>Review the job description and required skills</li>
                    <li>Prepare examples from your experience with GenAI/LLM projects</li>
                    <li>Research the company's AI initiatives</li>
                    <li>Practice common technical and behavioral questions</li>
                    <li>Prepare questions to ask the interviewer</li>
                </ul>
                
                <a href="{job.source_url}" class="cta-button">View Job Details</a>
            </div>
            <div class="footer">
                <p>Good luck with your interview! 🍀</p>
                <p>This is an automated reminder from GenAI Job Assistant</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_status_update_html(self, application: Application, job: JobListing,
                                    old_status: str, new_status: str) -> str:
        """
        Generate HTML email template for application status update
        
        Args:
            application: Application with updated status
            job: Associated job listing
            old_status: Previous status
            new_status: New status
            
        Returns:
            HTML formatted email body
        """
        status_colors = {
            'applied': '#2196F3',
            'interview': '#FF9800',
            'offered': '#4CAF50',
            'rejected': '#F44336',
            'saved': '#9E9E9E',
            'not_interested': '#757575'
        }
        
        color = status_colors.get(new_status.lower(), '#2196F3')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .status-update {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; 
                                 margin: 15px 0; text-align: center; }}
                .status-badge {{ display: inline-block; padding: 10px 20px; border-radius: 5px; 
                                font-weight: bold; margin: 5px; }}
                .old-status {{ background-color: #e0e0e0; color: #666; }}
                .new-status {{ background-color: {color}; color: white; }}
                .arrow {{ font-size: 24px; margin: 0 10px; }}
                .job-details {{ margin: 20px 0; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
                .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Application Status Update</h1>
            </div>
            <div class="content">
                <div class="status-update">
                    <span class="status-badge old-status">{old_status.upper()}</span>
                    <span class="arrow">→</span>
                    <span class="status-badge new-status">{new_status.upper()}</span>
                </div>
                
                <div class="job-details">
                    <h2>Job Details</h2>
                    <div class="detail-row">
                        <span class="label">Position:</span> {job.title}
                    </div>
                    <div class="detail-row">
                        <span class="label">Company:</span> {job.company}
                    </div>
                    <div class="detail-row">
                        <span class="label">Location:</span> {job.location}
                    </div>
                    <div class="detail-row">
                        <span class="label">Updated:</span> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                    </div>
                </div>
            </div>
            <div class="footer">
                <p>This is an automated notification from GenAI Job Assistant</p>
            </div>
        </body>
        </html>
        """
        
        return html



    def send_daily_digest_email(self, to: str, jobs: List[JobListing]) -> bool:
        """
        Send daily digest email with new job listings
        
        Args:
            to: Recipient email address
            jobs: List of new job listings
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not jobs:
            logger.info("No jobs to send in daily digest")
            return True
        
        subject = f"🤖 Daily Job Digest - {len(jobs)} New GenAI Opportunities"
        html_body = self._generate_daily_digest_html(jobs)
        
        return self.send_email(to, subject, html_body, html=True)
    
    def send_interview_reminder_email(self, to: str, application: Application, 
                                     job: JobListing) -> bool:
        """
        Send interview reminder email
        
        Args:
            to: Recipient email address
            application: Application with interview details
            job: Associated job listing
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not application.interview_date:
            logger.warning("Cannot send interview reminder: no interview date set")
            return False
        
        subject = f"⏰ Interview Reminder: {job.company} - {job.title}"
        html_body = self._generate_interview_reminder_html(application, job)
        
        return self.send_email(to, subject, html_body, html=True)
    
    def send_status_update_email(self, to: str, application: Application, 
                                job: JobListing, old_status: str, 
                                new_status: str) -> bool:
        """
        Send application status update email
        
        Args:
            to: Recipient email address
            application: Application with updated status
            job: Associated job listing
            old_status: Previous status
            new_status: New status
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"📋 Status Update: {job.company} - {new_status.upper()}"
        html_body = self._generate_status_update_html(application, job, old_status, new_status)
        
        return self.send_email(to, subject, html_body, html=True)



class WhatsAppNotificationManager:
    """Manages WhatsApp notifications using Twilio API"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """
        Initialize WhatsApp notification manager
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio WhatsApp number (format: whatsapp:+14155238886)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        
        # Import Twilio client (lazy import to avoid dependency if not used)
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
            logger.info("WhatsAppNotificationManager initialized successfully")
        except ImportError:
            logger.error("Twilio library not installed. Install with: pip install twilio")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.client = None
    
    def send_whatsapp(self, to: str, message: str) -> bool:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to: Recipient WhatsApp number (format: whatsapp:+919876543210)
            message: Message text to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized. Cannot send WhatsApp message.")
            return False
        
        try:
            # Ensure number is in correct format
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            
            logger.info(f"WhatsApp message sent successfully to {to}. SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to}: {e}")
            return False
    
    def _generate_new_jobs_alert_message(self, jobs: List[JobListing]) -> str:
        """
        Generate WhatsApp message template for new jobs alert
        
        Args:
            jobs: List of new job listings
            
        Returns:
            Formatted message text
        """
        if not jobs:
            return ""
        
        message = f"🤖 *GenAI Job Assistant*\n\n"
        message += f"Found *{len(jobs)}* new matching jobs!\n\n"
        
        # Show top 3 jobs
        for i, job in enumerate(jobs[:3], 1):
            salary_str = ""
            if job.salary_min:
                salary_str = f"₹{job.salary_min/100000:.1f}L+"
            
            match_score = f"{job.match_score:.0f}%" if job.match_score else "N/A"
            
            message += f"*{i}. {job.title}*\n"
            message += f"🏢 {job.company}\n"
            message += f"📍 {job.location} | {job.remote_type}\n"
            if salary_str:
                message += f"💰 {salary_str}\n"
            message += f"⭐ Match: {match_score}\n"
            message += f"🔗 {job.source_url}\n\n"
        
        if len(jobs) > 3:
            message += f"_...and {len(jobs) - 3} more jobs_\n\n"
        
        message += "Check your dashboard for full details!"
        
        return message
    
    def _generate_interview_reminder_message(self, application: Application, 
                                            job: JobListing) -> str:
        """
        Generate WhatsApp message template for interview reminder
        
        Args:
            application: Application with interview details
            job: Associated job listing
            
        Returns:
            Formatted message text
        """
        if not application.interview_date:
            return ""
        
        interview_date_str = application.interview_date.strftime('%B %d, %Y at %I:%M %p')
        
        message = f"⏰ *Interview Reminder*\n\n"
        message += f"Your interview is coming up!\n\n"
        message += f"*Company:* {job.company}\n"
        message += f"*Position:* {job.title}\n"
        message += f"*Date & Time:* {interview_date_str}\n"
        message += f"*Location:* {job.location}\n\n"
        message += f"🍀 Good luck with your interview!\n\n"
        message += f"🔗 Job Details: {job.source_url}"
        
        return message
    
    def send_new_jobs_alert(self, to: str, jobs: List[JobListing]) -> bool:
        """
        Send WhatsApp alert for new job listings
        
        Args:
            to: Recipient WhatsApp number
            jobs: List of new job listings
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not jobs:
            logger.info("No jobs to send in WhatsApp alert")
            return True
        
        message = self._generate_new_jobs_alert_message(jobs)
        return self.send_whatsapp(to, message)
    
    def send_interview_reminder(self, to: str, application: Application, 
                               job: JobListing) -> bool:
        """
        Send WhatsApp interview reminder
        
        Args:
            to: Recipient WhatsApp number
            application: Application with interview details
            job: Associated job listing
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not application.interview_date:
            logger.warning("Cannot send interview reminder: no interview date set")
            return False
        
        message = self._generate_interview_reminder_message(application, job)
        return self.send_whatsapp(to, message)



class UnifiedNotificationService:
    """
    Unified notification service that manages both email and WhatsApp notifications
    with preference checking and scheduling support
    """
    
    def __init__(self, email_manager: Optional[NotificationManager] = None,
                 whatsapp_manager: Optional[WhatsAppNotificationManager] = None,
                 preferences_repository = None):
        """
        Initialize unified notification service
        
        Args:
            email_manager: Email notification manager instance
            whatsapp_manager: WhatsApp notification manager instance
            preferences_repository: Repository for notification preferences
        """
        self.email_manager = email_manager
        self.whatsapp_manager = whatsapp_manager
        self.preferences_repository = preferences_repository
        
        logger.info("UnifiedNotificationService initialized")
    
    def configure_preferences(self, user_id: str, preferences: NotificationPreferences) -> bool:
        """
        Configure notification preferences for a user
        
        Args:
            user_id: User ID
            preferences: NotificationPreferences instance
            
        Returns:
            True if configuration successful, False otherwise
        """
        if not self.preferences_repository:
            logger.error("Preferences repository not configured")
            return False
        
        try:
            # Check if preferences already exist
            existing = self.preferences_repository.find_by_user_id(user_id)
            
            if existing:
                # Update existing preferences
                success = self.preferences_repository.update(preferences)
                logger.info(f"Updated notification preferences for user {user_id}")
            else:
                # Create new preferences
                success = self.preferences_repository.save(preferences)
                logger.info(f"Created notification preferences for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to configure preferences for user {user_id}: {e}")
            return False
    
    def _get_user_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """
        Get notification preferences for a user
        
        Args:
            user_id: User ID
            
        Returns:
            NotificationPreferences if found, None otherwise
        """
        if not self.preferences_repository:
            logger.warning("Preferences repository not configured")
            return None
        
        return self.preferences_repository.find_by_user_id(user_id)
    
    def send_daily_digest(self, user_id: str, jobs: List[JobListing]) -> Dict[str, bool]:
        """
        Send daily digest notification via configured channels
        
        Args:
            user_id: User ID
            jobs: List of new job listings
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {'email': False, 'whatsapp': False}
        
        if not jobs:
            logger.info("No jobs to send in daily digest")
            return results
        
        # Get user preferences
        preferences = self._get_user_preferences(user_id)
        if not preferences:
            logger.warning(f"No notification preferences found for user {user_id}")
            return results
        
        # Check if daily digest is enabled
        if not preferences.daily_digest:
            logger.info(f"Daily digest disabled for user {user_id}")
            return results
        
        # Send email if enabled
        if preferences.email_enabled and self.email_manager:
            try:
                results['email'] = self.email_manager.send_daily_digest_email(
                    preferences.email_address, jobs
                )
            except Exception as e:
                logger.error(f"Failed to send daily digest email: {e}")
        
        # Send WhatsApp if enabled
        if preferences.whatsapp_enabled and self.whatsapp_manager:
            try:
                results['whatsapp'] = self.whatsapp_manager.send_new_jobs_alert(
                    preferences.whatsapp_number, jobs
                )
            except Exception as e:
                logger.error(f"Failed to send daily digest WhatsApp: {e}")
        
        return results
    
    def send_interview_reminder(self, user_id: str, application: Application,
                               job: JobListing) -> Dict[str, bool]:
        """
        Send interview reminder notification via configured channels
        Triggered 24 hours before interview
        
        Args:
            user_id: User ID
            application: Application with interview details
            job: Associated job listing
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {'email': False, 'whatsapp': False}
        
        if not application.interview_date:
            logger.warning("Cannot send interview reminder: no interview date set")
            return results
        
        # Check if reminder should be sent (24 hours before)
        time_until_interview = application.interview_date - datetime.now()
        if time_until_interview.total_seconds() < 0:
            logger.info("Interview date has passed, not sending reminder")
            return results
        
        # Get user preferences
        preferences = self._get_user_preferences(user_id)
        if not preferences:
            logger.warning(f"No notification preferences found for user {user_id}")
            return results
        
        # Check if interview reminders are enabled
        if not preferences.interview_reminders:
            logger.info(f"Interview reminders disabled for user {user_id}")
            return results
        
        # Send email if enabled
        if preferences.email_enabled and self.email_manager:
            try:
                results['email'] = self.email_manager.send_interview_reminder_email(
                    preferences.email_address, application, job
                )
            except Exception as e:
                logger.error(f"Failed to send interview reminder email: {e}")
        
        # Send WhatsApp if enabled
        if preferences.whatsapp_enabled and self.whatsapp_manager:
            try:
                results['whatsapp'] = self.whatsapp_manager.send_interview_reminder(
                    preferences.whatsapp_number, application, job
                )
            except Exception as e:
                logger.error(f"Failed to send interview reminder WhatsApp: {e}")
        
        return results
    
    def send_status_update(self, user_id: str, application: Application,
                          job: JobListing, old_status: str, 
                          new_status: str) -> Dict[str, bool]:
        """
        Send application status update notification via configured channels
        
        Args:
            user_id: User ID
            application: Application with updated status
            job: Associated job listing
            old_status: Previous status
            new_status: New status
            
        Returns:
            Dictionary with success status for each channel
        """
        results = {'email': False, 'whatsapp': False}
        
        # Get user preferences
        preferences = self._get_user_preferences(user_id)
        if not preferences:
            logger.warning(f"No notification preferences found for user {user_id}")
            return results
        
        # Check if status updates are enabled
        if not preferences.status_updates:
            logger.info(f"Status updates disabled for user {user_id}")
            return results
        
        # Send email if enabled
        if preferences.email_enabled and self.email_manager:
            try:
                results['email'] = self.email_manager.send_status_update_email(
                    preferences.email_address, application, job, old_status, new_status
                )
            except Exception as e:
                logger.error(f"Failed to send status update email: {e}")
        
        # WhatsApp status updates are typically not sent to avoid spam
        # Only email notifications for status changes
        
        return results
    
    def check_and_send_interview_reminders(self, applications_with_jobs: List[tuple]) -> int:
        """
        Check all applications and send reminders for interviews within 24 hours
        
        Args:
            applications_with_jobs: List of tuples (user_id, application, job)
            
        Returns:
            Number of reminders sent
        """
        reminders_sent = 0
        now = datetime.now()
        
        for user_id, application, job in applications_with_jobs:
            if not application.interview_date:
                continue
            
            # Check if interview is within 24 hours
            time_until_interview = application.interview_date - now
            hours_until = time_until_interview.total_seconds() / 3600
            
            # Send reminder if interview is between 23-25 hours away
            if 23 <= hours_until <= 25:
                results = self.send_interview_reminder(user_id, application, job)
                if results['email'] or results['whatsapp']:
                    reminders_sent += 1
                    logger.info(f"Sent interview reminder for application {application.id}")
        
        return reminders_sent
