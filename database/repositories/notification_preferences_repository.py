"""
Notification Preferences Repository for CRUD operations
"""

from typing import Optional
from datetime import datetime
import logging
from models.notification import NotificationPreferences
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class NotificationPreferencesRepository:
    """Repository for notification preferences database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize notification preferences repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, preferences: NotificationPreferences) -> bool:
        """
        Save notification preferences to database
        
        Args:
            preferences: NotificationPreferences instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO notification_preferences (
                    user_id, email_enabled, email_address, whatsapp_enabled,
                    whatsapp_number, daily_digest, interview_reminders,
                    status_updates, digest_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = preferences.to_db_dict()
            params = (
                db_dict['user_id'], db_dict['email_enabled'], db_dict['email_address'],
                db_dict['whatsapp_enabled'], db_dict['whatsapp_number'],
                db_dict['daily_digest'], db_dict['interview_reminders'],
                db_dict['status_updates'], db_dict['digest_time']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save notification preferences: {e}")
            return False
    
    def update(self, preferences: NotificationPreferences) -> bool:
        """
        Update notification preferences in database
        
        Args:
            preferences: NotificationPreferences instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE notification_preferences 
                SET email_enabled = ?, email_address = ?, whatsapp_enabled = ?,
                    whatsapp_number = ?, daily_digest = ?, interview_reminders = ?,
                    status_updates = ?, digest_time = ?
                WHERE user_id = ?
            """
            
            db_dict = preferences.to_db_dict()
            params = (
                db_dict['email_enabled'], db_dict['email_address'],
                db_dict['whatsapp_enabled'], db_dict['whatsapp_number'],
                db_dict['daily_digest'], db_dict['interview_reminders'],
                db_dict['status_updates'], db_dict['digest_time'],
                db_dict['user_id']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update notification preferences: {e}")
            return False
    
    def find_by_user_id(self, user_id: str) -> Optional[NotificationPreferences]:
        """
        Find notification preferences by user ID
        
        Args:
            user_id: User ID to search for
            
        Returns:
            NotificationPreferences if found, None otherwise
        """
        try:
            query = "SELECT * FROM notification_preferences WHERE user_id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            
            if results:
                return NotificationPreferences.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find notification preferences by user ID: {e}")
            return None
    
    def delete(self, user_id: str) -> bool:
        """
        Delete notification preferences by user ID
        
        Args:
            user_id: User ID to delete preferences for
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM notification_preferences WHERE user_id = ?"
            rows_affected = self.db_manager.execute_update(query, (user_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete notification preferences: {e}")
            return False
    
    def exists(self, user_id: str) -> bool:
        """
        Check if notification preferences exist for user
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if preferences exist, False otherwise
        """
        try:
            query = "SELECT COUNT(*) as count FROM notification_preferences WHERE user_id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            return results[0]['count'] > 0 if results else False
            
        except Exception as e:
            logger.error(f"Failed to check notification preferences existence: {e}")
            return False
