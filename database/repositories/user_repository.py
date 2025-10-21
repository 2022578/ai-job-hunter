"""
User Repository for CRUD operations on user profiles
"""

from typing import Optional, List
from datetime import datetime
import logging
from models.user import UserProfile
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user profile database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize user repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, user: UserProfile) -> bool:
        """
        Save user profile to database
        
        Args:
            user: UserProfile instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO users (
                    id, name, email, resume_text, resume_path, skills,
                    experience_years, target_salary, preferred_locations,
                    preferred_remote, desired_tech_stack, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = user.to_db_dict()
            params = (
                db_dict['id'], db_dict['name'], db_dict['email'],
                db_dict['resume_text'], db_dict['resume_path'], db_dict['skills'],
                db_dict['experience_years'], db_dict['target_salary'],
                db_dict['preferred_locations'], db_dict['preferred_remote'],
                db_dict['desired_tech_stack'], db_dict['created_at'], db_dict['updated_at']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False
    
    def update(self, user: UserProfile) -> bool:
        """
        Update user profile in database
        
        Args:
            user: UserProfile instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE users 
                SET name = ?, email = ?, resume_text = ?, resume_path = ?,
                    skills = ?, experience_years = ?, target_salary = ?,
                    preferred_locations = ?, preferred_remote = ?,
                    desired_tech_stack = ?, updated_at = ?
                WHERE id = ?
            """
            
            user.updated_at = datetime.now()
            db_dict = user.to_db_dict()
            
            params = (
                db_dict['name'], db_dict['email'], db_dict['resume_text'],
                db_dict['resume_path'], db_dict['skills'], db_dict['experience_years'],
                db_dict['target_salary'], db_dict['preferred_locations'],
                db_dict['preferred_remote'], db_dict['desired_tech_stack'],
                db_dict['updated_at'], db_dict['id']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False
    
    def find_by_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Find user profile by ID
        
        Args:
            user_id: User ID to search for
            
        Returns:
            UserProfile if found, None otherwise
        """
        try:
            query = "SELECT * FROM users WHERE id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            
            if results:
                return UserProfile.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by ID: {e}")
            return None
    
    def find_by_email(self, email: str) -> Optional[UserProfile]:
        """
        Find user profile by email
        
        Args:
            email: Email address to search for
            
        Returns:
            UserProfile if found, None otherwise
        """
        try:
            query = "SELECT * FROM users WHERE email = ?"
            results = self.db_manager.execute_query(query, (email,))
            
            if results:
                return UserProfile.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find user by email: {e}")
            return None
    
    def find_all(self) -> List[UserProfile]:
        """
        Find all user profiles
        
        Returns:
            List of UserProfile instances
        """
        try:
            query = "SELECT * FROM users ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query)
            return [UserProfile.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find all users: {e}")
            return []
    
    def delete(self, user_id: str) -> bool:
        """
        Delete user profile by ID
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM users WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (user_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete user profile: {e}")
            return False
    
    def exists(self, user_id: str) -> bool:
        """
        Check if user exists by ID
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            query = "SELECT COUNT(*) as count FROM users WHERE id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            return results[0]['count'] > 0 if results else False
            
        except Exception as e:
            logger.error(f"Failed to check user existence: {e}")
            return False
