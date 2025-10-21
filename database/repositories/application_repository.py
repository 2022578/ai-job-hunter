"""
Application Repository for CRUD operations on job applications
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from models.application import Application
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ApplicationRepository:
    """Repository for application database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize application repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, application: Application) -> bool:
        """
        Save application to database
        
        Args:
            application: Application instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO applications (
                    id, job_id, user_id, status, applied_date, interview_date,
                    notes, cover_letter, hr_contact_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = application.to_db_dict()
            params = (
                db_dict['id'], db_dict['job_id'], db_dict['user_id'],
                db_dict['status'], db_dict['applied_date'], db_dict['interview_date'],
                db_dict['notes'], db_dict['cover_letter'], db_dict['hr_contact_id'],
                db_dict['created_at'], db_dict['updated_at']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save application: {e}")
            return False
    
    def update_status(self, application_id: str, new_status: str) -> bool:
        """
        Update application status
        
        Args:
            application_id: Application ID to update
            new_status: New status value
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate status
            if new_status not in Application.VALID_STATUSES:
                logger.error(f"Invalid status: {new_status}")
                return False
            
            query = """
                UPDATE applications 
                SET status = ?, updated_at = ? 
                WHERE id = ?
            """
            
            rows_affected = self.db_manager.execute_update(
                query, 
                (new_status, datetime.now().isoformat(), application_id)
            )
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update application status: {e}")
            return False
    
    def find_by_user(self, user_id: str, status: Optional[str] = None) -> List[Application]:
        """
        Find applications by user ID with optional status filter
        
        Args:
            user_id: User ID to search for
            status: Optional status filter
            
        Returns:
            List of Application instances
        """
        try:
            query = "SELECT * FROM applications WHERE user_id = ?"
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            results = self.db_manager.execute_query(query, tuple(params))
            return [Application.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find applications by user: {e}")
            return []
    
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get application statistics for a user
        
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
            # Get total count
            total_query = "SELECT COUNT(*) as count FROM applications WHERE user_id = ?"
            total_result = self.db_manager.execute_query(total_query, (user_id,))
            total = total_result[0]['count'] if total_result else 0
            
            # Get count by status
            status_query = """
                SELECT status, COUNT(*) as count 
                FROM applications 
                WHERE user_id = ? 
                GROUP BY status
            """
            status_results = self.db_manager.execute_query(status_query, (user_id,))
            by_status = {row['status']: row['count'] for row in status_results}
            
            # Calculate rates
            # Count applications that were applied (excluding saved and not_interested)
            applied_count = by_status.get('applied', 0)
            interview_count = by_status.get('interview', 0)
            offered_count = by_status.get('offered', 0)
            rejected_count = by_status.get('rejected', 0)
            
            # Total applications that were actually applied (not just saved)
            total_applied = applied_count + interview_count + offered_count + rejected_count
            
            interview_rate = (interview_count / total_applied * 100) if total_applied > 0 else 0
            offer_rate = (offered_count / total_applied * 100) if total_applied > 0 else 0
            
            return {
                'total': total,
                'by_status': by_status,
                'interview_rate': round(interview_rate, 2),
                'offer_rate': round(offer_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get application statistics: {e}")
            return {
                'total': 0,
                'by_status': {},
                'interview_rate': 0,
                'offer_rate': 0
            }
    
    def find_by_id(self, application_id: str) -> Optional[Application]:
        """
        Find application by ID
        
        Args:
            application_id: Application ID to search for
            
        Returns:
            Application if found, None otherwise
        """
        try:
            query = "SELECT * FROM applications WHERE id = ?"
            results = self.db_manager.execute_query(query, (application_id,))
            
            if results:
                return Application.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find application by ID: {e}")
            return None
    
    def update(self, application: Application) -> bool:
        """
        Update application in database
        
        Args:
            application: Application instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE applications 
                SET job_id = ?, user_id = ?, status = ?, applied_date = ?,
                    interview_date = ?, notes = ?, cover_letter = ?,
                    hr_contact_id = ?, updated_at = ?
                WHERE id = ?
            """
            
            application.updated_at = datetime.now()
            db_dict = application.to_db_dict()
            
            params = (
                db_dict['job_id'], db_dict['user_id'], db_dict['status'],
                db_dict['applied_date'], db_dict['interview_date'], db_dict['notes'],
                db_dict['cover_letter'], db_dict['hr_contact_id'],
                db_dict['updated_at'], db_dict['id']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update application: {e}")
            return False
    
    def delete(self, application_id: str) -> bool:
        """
        Delete application by ID
        
        Args:
            application_id: Application ID to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM applications WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (application_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete application: {e}")
            return False
