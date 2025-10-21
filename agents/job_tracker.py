"""
Job Tracker Agent for managing job applications and HR contacts
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import csv
import io
from models.application import Application
from models.hr_contact import HRContact
from database.repositories.application_repository import ApplicationRepository
from database.repositories.hr_contact_repository import HRContactRepository
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class JobTracker:
    """
    Job Tracker agent for managing application history, status, and HR contacts
    
    Responsibilities:
    - Track job applications and their status
    - Manage HR contact information
    - Provide application statistics
    - Export application history
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize Job Tracker
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.application_repo = ApplicationRepository(db_manager)
        self.hr_contact_repo = HRContactRepository(db_manager)
        logger.info("Job Tracker initialized")
    
    def add_application(
        self,
        job_id: str,
        user_id: str,
        status: str = "saved",
        applied_date: Optional[datetime] = None,
        interview_date: Optional[datetime] = None,
        notes: str = "",
        cover_letter: Optional[str] = None
    ) -> Optional[Application]:
        """
        Record a new job application
        
        Args:
            job_id: ID of the job being applied to
            user_id: ID of the user applying
            status: Initial status (default: "saved")
            applied_date: Date when application was submitted
            interview_date: Date of scheduled interview
            notes: Additional notes about the application
            cover_letter: Cover letter text
            
        Returns:
            Application instance if successful, None otherwise
        """
        try:
            # Create application instance
            application = Application(
                job_id=job_id,
                user_id=user_id,
                status=status,
                applied_date=applied_date,
                interview_date=interview_date,
                notes=notes,
                cover_letter=cover_letter
            )
            
            # Save to database
            success = self.application_repo.save(application)
            
            if success:
                logger.info(f"Added application {application.id} for job {job_id}")
                return application
            else:
                logger.error(f"Failed to save application for job {job_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding application: {e}")
            return None
    
    def update_status(
        self,
        application_id: str,
        new_status: str,
        applied_date: Optional[datetime] = None,
        interview_date: Optional[datetime] = None
    ) -> bool:
        """
        Update application status with validation
        
        Args:
            application_id: ID of the application to update
            new_status: New status value
            applied_date: Optional applied date to set
            interview_date: Optional interview date to set
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate status
            if new_status not in Application.VALID_STATUSES:
                logger.error(f"Invalid status: {new_status}")
                return False
            
            # Get existing application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                logger.error(f"Application {application_id} not found")
                return False
            
            # Validate status transitions
            if not self._validate_status_transition(application.status, new_status):
                logger.warning(
                    f"Invalid status transition from {application.status} to {new_status}"
                )
            
            # Update status
            application.update_status(new_status)
            
            # Update dates if provided
            if applied_date:
                application.applied_date = applied_date
            if interview_date:
                application.interview_date = interview_date
            
            # Save to database
            success = self.application_repo.update(application)
            
            if success:
                logger.info(
                    f"Updated application {application_id} status to {new_status}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    def _validate_status_transition(self, old_status: str, new_status: str) -> bool:
        """
        Validate status transition logic
        
        Args:
            old_status: Current status
            new_status: Desired new status
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            "saved": ["applied", "not_interested"],
            "applied": ["interview", "rejected", "not_interested"],
            "interview": ["offered", "rejected"],
            "offered": ["rejected"],  # Can reject an offer
            "rejected": [],  # Terminal state
            "not_interested": []  # Terminal state
        }
        
        # Allow same status (no-op)
        if old_status == new_status:
            return True
        
        # Check if transition is valid
        return new_status in valid_transitions.get(old_status, [])
    
    def mark_as_saved(self, job_id: str, user_id: str, notes: str = "") -> Optional[Application]:
        """
        Mark a job as saved for later
        
        Args:
            job_id: ID of the job to save
            user_id: ID of the user
            notes: Optional notes about why job was saved
            
        Returns:
            Application instance if successful, None otherwise
        """
        return self.add_application(
            job_id=job_id,
            user_id=user_id,
            status="saved",
            notes=notes
        )
    
    def mark_as_not_interested(self, application_id: str) -> bool:
        """
        Mark an application as not interested
        
        Args:
            application_id: ID of the application
            
        Returns:
            True if update successful, False otherwise
        """
        return self.update_status(application_id, "not_interested")
    
    def add_hr_contact(
        self,
        application_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        designation: Optional[str] = None,
        notes: str = ""
    ) -> Optional[HRContact]:
        """
        Store HR contact information for an application
        
        Args:
            application_id: ID of the associated application
            name: HR contact name
            email: HR contact email
            phone: HR contact phone number
            linkedin_url: HR contact LinkedIn profile URL
            designation: HR contact job title/designation
            notes: Additional notes about the contact
            
        Returns:
            HRContact instance if successful, None otherwise
        """
        try:
            # Verify application exists
            application = self.application_repo.find_by_id(application_id)
            if not application:
                logger.error(f"Application {application_id} not found")
                return None
            
            # Create HR contact instance
            hr_contact = HRContact(
                application_id=application_id,
                name=name,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
                designation=designation,
                notes=notes
            )
            
            # Save to database
            success = self.hr_contact_repo.save(hr_contact)
            
            if success:
                # Update application with HR contact ID
                application.hr_contact_id = hr_contact.id
                self.application_repo.update(application)
                
                logger.info(
                    f"Added HR contact {hr_contact.id} for application {application_id}"
                )
                return hr_contact
            else:
                logger.error(f"Failed to save HR contact for application {application_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding HR contact: {e}")
            return None
    
    def update_hr_contact(
        self,
        contact_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        designation: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update HR contact details
        
        Args:
            contact_id: ID of the HR contact to update
            name: Updated name
            email: Updated email
            phone: Updated phone
            linkedin_url: Updated LinkedIn URL
            designation: Updated designation
            notes: Updated notes
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get existing contact
            hr_contact = self.hr_contact_repo.find_by_id(contact_id)
            if not hr_contact:
                logger.error(f"HR contact {contact_id} not found")
                return False
            
            # Update fields if provided
            if name is not None:
                hr_contact.name = name
            if email is not None:
                hr_contact.email = email
            if phone is not None:
                hr_contact.phone = phone
            if linkedin_url is not None:
                hr_contact.linkedin_url = linkedin_url
            if designation is not None:
                hr_contact.designation = designation
            if notes is not None:
                hr_contact.notes = notes
            
            # Save to database
            success = self.hr_contact_repo.update(hr_contact)
            
            if success:
                logger.info(f"Updated HR contact {contact_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating HR contact: {e}")
            return False
    
    def get_hr_contacts(
        self,
        application_id: Optional[str] = None,
        search_name: Optional[str] = None,
        search_email: Optional[str] = None,
        search_designation: Optional[str] = None
    ) -> List[HRContact]:
        """
        Get HR contacts with search and filter capabilities
        
        Args:
            application_id: Filter by application ID
            search_name: Search by name (partial match)
            search_email: Search by email (partial match)
            search_designation: Search by designation (partial match)
            
        Returns:
            List of matching HRContact instances
        """
        try:
            # If application_id provided, get contacts for that application
            if application_id:
                return self.hr_contact_repo.find_by_application(application_id)
            
            # Otherwise, search by criteria
            criteria = {}
            if search_name:
                criteria['name'] = search_name
            if search_email:
                criteria['email'] = search_email
            if search_designation:
                criteria['designation'] = search_designation
            
            if criteria:
                return self.hr_contact_repo.search(criteria)
            
            # If no filters, return all contacts
            return self.hr_contact_repo.find_all()
            
        except Exception as e:
            logger.error(f"Error getting HR contacts: {e}")
            return []
    
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate application metrics and statistics
        
        Args:
            user_id: User ID to get statistics for
            
        Returns:
            Dictionary with statistics:
                - total: Total applications
                - by_status: Count by status
                - interview_rate: Percentage reaching interview
                - offer_rate: Percentage receiving offers
        """
        try:
            return self.application_repo.get_statistics(user_id)
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total': 0,
                'by_status': {},
                'interview_rate': 0,
                'offer_rate': 0
            }
    
    def export_history(
        self,
        user_id: str,
        format: str = "csv",
        include_hr_contacts: bool = True
    ) -> str:
        """
        Generate CSV/Excel file with application history and HR contacts
        
        Args:
            user_id: User ID to export history for
            format: Export format ("csv" or "excel")
            include_hr_contacts: Whether to include HR contact details
            
        Returns:
            CSV string or file path for Excel
        """
        try:
            # Get all applications for user
            applications = self.application_repo.find_by_user(user_id)
            
            if format.lower() == "csv":
                return self._export_to_csv(applications, include_hr_contacts)
            else:
                logger.warning(f"Unsupported export format: {format}. Using CSV.")
                return self._export_to_csv(applications, include_hr_contacts)
                
        except Exception as e:
            logger.error(f"Error exporting history: {e}")
            return ""
    
    def _export_to_csv(
        self,
        applications: List[Application],
        include_hr_contacts: bool
    ) -> str:
        """
        Export applications to CSV format
        
        Args:
            applications: List of applications to export
            include_hr_contacts: Whether to include HR contact details
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        
        # Define CSV headers
        headers = [
            'Application ID', 'Job ID', 'Status', 'Applied Date',
            'Interview Date', 'Notes', 'Created At', 'Updated At'
        ]
        
        if include_hr_contacts:
            headers.extend([
                'HR Name', 'HR Email', 'HR Phone', 'HR LinkedIn',
                'HR Designation', 'HR Notes'
            ])
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Write application data
        for app in applications:
            row = [
                app.id,
                app.job_id,
                app.status,
                app.applied_date.isoformat() if app.applied_date else '',
                app.interview_date.isoformat() if app.interview_date else '',
                app.notes,
                app.created_at.isoformat() if app.created_at else '',
                app.updated_at.isoformat() if app.updated_at else ''
            ]
            
            if include_hr_contacts:
                # Get HR contact for this application
                hr_contacts = self.hr_contact_repo.find_by_application(app.id)
                if hr_contacts:
                    hr = hr_contacts[0]  # Take first contact
                    row.extend([
                        hr.name,
                        hr.email or '',
                        hr.phone or '',
                        hr.linkedin_url or '',
                        hr.designation or '',
                        hr.notes
                    ])
                else:
                    row.extend(['', '', '', '', '', ''])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def get_applications(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Application]:
        """
        Get applications for a user with optional status filter
        
        Args:
            user_id: User ID to get applications for
            status: Optional status filter
            
        Returns:
            List of Application instances
        """
        try:
            return self.application_repo.find_by_user(user_id, status)
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return []
