"""
Job Repository for CRUD operations on job listings
"""

from typing import List, Optional, Dict, Any
import logging
from models.job import JobListing
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository for job listing database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize job repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, job: JobListing) -> bool:
        """
        Save job listing to database
        
        Args:
            job: JobListing instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO jobs (
                    id, title, company, salary_min, salary_max, location,
                    remote_type, description, required_skills, posted_date,
                    source_url, source, raw_html, created_at, match_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = job.to_db_dict()
            params = (
                db_dict['id'], db_dict['title'], db_dict['company'],
                db_dict['salary_min'], db_dict['salary_max'], db_dict['location'],
                db_dict['remote_type'], db_dict['description'], db_dict['required_skills'],
                db_dict['posted_date'], db_dict['source_url'], db_dict['source'],
                db_dict['raw_html'], db_dict['created_at'], db_dict['match_score']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save job: {e}")
            return False
    
    def find_by_id(self, job_id: str) -> Optional[JobListing]:
        """
        Find job by ID
        
        Args:
            job_id: Job ID to search for
            
        Returns:
            JobListing if found, None otherwise
        """
        try:
            query = "SELECT * FROM jobs WHERE id = ?"
            results = self.db_manager.execute_query(query, (job_id,))
            
            if results:
                return JobListing.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find job by ID: {e}")
            return None
    
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[JobListing]:
        """
        Find all jobs with optional pagination
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of JobListing instances
        """
        try:
            query = "SELECT * FROM jobs ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            results = self.db_manager.execute_query(query)
            return [JobListing.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find all jobs: {e}")
            return []
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[JobListing]:
        """
        Find jobs matching criteria
        
        Args:
            criteria: Dictionary of search criteria
                - company: Company name (partial match)
                - min_salary: Minimum salary threshold
                - remote_type: Remote work type
                - min_match_score: Minimum match score
                
        Returns:
            List of matching JobListing instances
        """
        try:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []
            
            if 'company' in criteria:
                query += " AND company LIKE ?"
                params.append(f"%{criteria['company']}%")
            
            if 'min_salary' in criteria:
                query += " AND (salary_min >= ? OR salary_max >= ?)"
                params.extend([criteria['min_salary'], criteria['min_salary']])
            
            if 'remote_type' in criteria:
                query += " AND remote_type = ?"
                params.append(criteria['remote_type'])
            
            if 'min_match_score' in criteria:
                query += " AND match_score >= ?"
                params.append(criteria['min_match_score'])
            
            query += " ORDER BY match_score DESC, created_at DESC"
            
            results = self.db_manager.execute_query(query, tuple(params))
            return [JobListing.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find jobs by criteria: {e}")
            return []
    
    def update_match_score(self, job_id: str, match_score: float) -> bool:
        """
        Update match score for a job
        
        Args:
            job_id: Job ID to update
            match_score: New match score value
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = "UPDATE jobs SET match_score = ? WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (match_score, job_id))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update match score: {e}")
            return False
    
    def delete(self, job_id: str) -> bool:
        """
        Delete job by ID
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM jobs WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (job_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete job: {e}")
            return False
    
    def exists_by_url(self, source_url: str) -> bool:
        """
        Check if job with given URL already exists
        
        Args:
            source_url: Job source URL to check
            
        Returns:
            True if job exists, False otherwise
        """
        try:
            query = "SELECT COUNT(*) as count FROM jobs WHERE source_url = ?"
            results = self.db_manager.execute_query(query, (source_url,))
            return results[0]['count'] > 0 if results else False
            
        except Exception as e:
            logger.error(f"Failed to check job existence: {e}")
            return False
