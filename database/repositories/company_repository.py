"""
Company Repository for CRUD operations on company profiles
"""

from typing import Optional, List
from datetime import datetime
import logging
from models.company import CompanyProfile
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository for company profile database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize company repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, company: CompanyProfile) -> bool:
        """
        Save company profile to database
        
        Args:
            company: CompanyProfile instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO company_profiles (
                    id, company_name, glassdoor_rating, employee_count,
                    funding_stage, recent_news, genai_focus_score,
                    culture_summary, cached_at, cache_expiry
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = company.to_db_dict()
            params = (
                db_dict['id'], db_dict['company_name'], db_dict['glassdoor_rating'],
                db_dict['employee_count'], db_dict['funding_stage'], db_dict['recent_news'],
                db_dict['genai_focus_score'], db_dict['culture_summary'],
                db_dict['cached_at'], db_dict['cache_expiry']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save company profile: {e}")
            return False
    
    def find_by_name(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Find company profile by name
        
        Args:
            company_name: Company name to search for
            
        Returns:
            CompanyProfile if found, None otherwise
        """
        try:
            query = "SELECT * FROM company_profiles WHERE company_name = ?"
            results = self.db_manager.execute_query(query, (company_name,))
            
            if results:
                return CompanyProfile.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find company by name: {e}")
            return None
    
    def get_cached(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Get cached company profile if valid
        
        Args:
            company_name: Company name to search for
            
        Returns:
            CompanyProfile if found and cache is valid, None otherwise
        """
        try:
            company = self.find_by_name(company_name)
            
            if company and company.is_cache_valid():
                return company
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached company: {e}")
            return None
    
    def update(self, company: CompanyProfile) -> bool:
        """
        Update company profile in database
        
        Args:
            company: CompanyProfile instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE company_profiles 
                SET glassdoor_rating = ?, employee_count = ?, funding_stage = ?,
                    recent_news = ?, genai_focus_score = ?, culture_summary = ?,
                    cached_at = ?, cache_expiry = ?
                WHERE company_name = ?
            """
            
            db_dict = company.to_db_dict()
            params = (
                db_dict['glassdoor_rating'], db_dict['employee_count'],
                db_dict['funding_stage'], db_dict['recent_news'],
                db_dict['genai_focus_score'], db_dict['culture_summary'],
                db_dict['cached_at'], db_dict['cache_expiry'],
                db_dict['company_name']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update company profile: {e}")
            return False
    
    def save_or_update(self, company: CompanyProfile) -> bool:
        """
        Save or update company profile (upsert operation)
        
        Args:
            company: CompanyProfile instance to save or update
            
        Returns:
            True if operation successful, False otherwise
        """
        try:
            existing = self.find_by_name(company.company_name)
            
            if existing:
                return self.update(company)
            else:
                return self.save(company)
                
        except Exception as e:
            logger.error(f"Failed to save or update company profile: {e}")
            return False
    
    def delete(self, company_name: str) -> bool:
        """
        Delete company profile by name
        
        Args:
            company_name: Company name to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM company_profiles WHERE company_name = ?"
            rows_affected = self.db_manager.execute_update(query, (company_name,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete company profile: {e}")
            return False
    
    def find_all(self, limit: Optional[int] = None) -> List[CompanyProfile]:
        """
        Find all company profiles with optional limit
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of CompanyProfile instances
        """
        try:
            query = "SELECT * FROM company_profiles ORDER BY company_name ASC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            results = self.db_manager.execute_query(query)
            return [CompanyProfile.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find all company profiles: {e}")
            return []
    
    def clean_expired_cache(self) -> int:
        """
        Remove expired company profiles from cache
        
        Returns:
            Number of profiles deleted
        """
        try:
            query = "DELETE FROM company_profiles WHERE cache_expiry < ?"
            rows_affected = self.db_manager.execute_update(
                query, 
                (datetime.now().isoformat(),)
            )
            return rows_affected
            
        except Exception as e:
            logger.error(f"Failed to clean expired cache: {e}")
            return 0
