"""
HR Contact Repository for CRUD operations on HR contacts
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from models.hr_contact import HRContact
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class HRContactRepository:
    """Repository for HR contact database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize HR contact repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, hr_contact: HRContact) -> bool:
        """
        Save HR contact to database
        
        Args:
            hr_contact: HRContact instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO hr_contacts (
                    id, application_id, name, email, phone, linkedin_url,
                    designation, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = hr_contact.to_db_dict()
            params = (
                db_dict['id'], db_dict['application_id'], db_dict['name'],
                db_dict['email'], db_dict['phone'], db_dict['linkedin_url'],
                db_dict['designation'], db_dict['notes'],
                db_dict['created_at'], db_dict['updated_at']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save HR contact: {e}")
            return False
    
    def update(self, hr_contact: HRContact) -> bool:
        """
        Update HR contact in database
        
        Args:
            hr_contact: HRContact instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE hr_contacts 
                SET application_id = ?, name = ?, email = ?, phone = ?,
                    linkedin_url = ?, designation = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """
            
            hr_contact.updated_at = datetime.now()
            db_dict = hr_contact.to_db_dict()
            
            params = (
                db_dict['application_id'], db_dict['name'], db_dict['email'],
                db_dict['phone'], db_dict['linkedin_url'], db_dict['designation'],
                db_dict['notes'], db_dict['updated_at'], db_dict['id']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update HR contact: {e}")
            return False
    
    def find_by_application(self, application_id: str) -> List[HRContact]:
        """
        Find HR contacts by application ID
        
        Args:
            application_id: Application ID to search for
            
        Returns:
            List of HRContact instances
        """
        try:
            query = "SELECT * FROM hr_contacts WHERE application_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (application_id,))
            return [HRContact.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find HR contacts by application: {e}")
            return []
    
    def search(self, criteria: Dict[str, Any]) -> List[HRContact]:
        """
        Search HR contacts by criteria
        
        Args:
            criteria: Dictionary of search criteria
                - name: Contact name (partial match)
                - email: Contact email (partial match)
                - designation: Contact designation (partial match)
                
        Returns:
            List of matching HRContact instances
        """
        try:
            query = "SELECT * FROM hr_contacts WHERE 1=1"
            params = []
            
            if 'name' in criteria:
                query += " AND name LIKE ?"
                params.append(f"%{criteria['name']}%")
            
            if 'email' in criteria:
                query += " AND email LIKE ?"
                params.append(f"%{criteria['email']}%")
            
            if 'designation' in criteria:
                query += " AND designation LIKE ?"
                params.append(f"%{criteria['designation']}%")
            
            query += " ORDER BY name ASC"
            
            results = self.db_manager.execute_query(query, tuple(params))
            return [HRContact.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to search HR contacts: {e}")
            return []
    
    def find_by_id(self, contact_id: str) -> Optional[HRContact]:
        """
        Find HR contact by ID
        
        Args:
            contact_id: Contact ID to search for
            
        Returns:
            HRContact if found, None otherwise
        """
        try:
            query = "SELECT * FROM hr_contacts WHERE id = ?"
            results = self.db_manager.execute_query(query, (contact_id,))
            
            if results:
                return HRContact.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find HR contact by ID: {e}")
            return None
    
    def find_all(self, limit: Optional[int] = None) -> List[HRContact]:
        """
        Find all HR contacts with optional limit
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of HRContact instances
        """
        try:
            query = "SELECT * FROM hr_contacts ORDER BY name ASC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            results = self.db_manager.execute_query(query)
            return [HRContact.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find all HR contacts: {e}")
            return []
    
    def delete(self, contact_id: str) -> bool:
        """
        Delete HR contact by ID
        
        Args:
            contact_id: Contact ID to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM hr_contacts WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (contact_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete HR contact: {e}")
            return False
