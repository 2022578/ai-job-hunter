"""
Cover Letter Generator Agent
Creates personalized cover letters for job applications using LLM
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import uuid
from utils.llm_client import OllamaClient, LLMResponse
from utils.prompts import cover_letter_prompt
from models.job import JobListing
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class CoverLetter:
    """Generated cover letter data"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    user_id: str = ""
    content: str = ""
    tone: str = "professional"
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))


class CoverLetterGenerator:
    """Agent for generating personalized cover letters"""
    
    # Cache duration in days
    CACHE_DURATION_DAYS = 7
    
    # Valid tone options
    VALID_TONES = ["professional", "enthusiastic", "technical"]
    
    def __init__(
        self,
        llm_client: OllamaClient,
        db_manager: DatabaseManager
    ):
        """
        Initialize Cover Letter Generator
        
        Args:
            llm_client: LLM client for text generation
            db_manager: Database manager for storing letters
        """
        self.llm_client = llm_client
        self.db_manager = db_manager
        self._ensure_cover_letters_table()
    
    def _ensure_cover_letters_table(self):
        """Create cover_letters table if it doesn't exist"""
        try:
            conn = self.db_manager.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cover_letters (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tone TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cover_letters_job_user 
                ON cover_letters(job_id, user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cover_letters_expires 
                ON cover_letters(expires_at)
            """)
            conn.commit()
            logger.info("Cover letters table ensured")
        except Exception as e:
            logger.error(f"Failed to create cover_letters table: {e}")

    def generate(
        self,
        job: JobListing,
        resume_summary: str,
        user_id: Optional[str] = None,
        relevant_projects: Optional[list] = None,
        tone: str = "professional"
    ) -> str:
        """
        Generate personalized cover letter for job
        
        Args:
            job: Job listing to generate cover letter for
            resume_summary: Summary of candidate's experience
            user_id: Optional user ID for caching
            relevant_projects: Optional list of relevant projects to highlight
            tone: Desired tone (professional, enthusiastic, technical)
            
        Returns:
            Generated cover letter text
        """
        try:
            # Validate tone
            if tone not in self.VALID_TONES:
                logger.warning(f"Invalid tone '{tone}', using 'professional'")
                tone = "professional"
            
            # Check cache if user_id provided
            if user_id:
                cached_letter = self._get_cached_letter(job.id, user_id, tone)
                if cached_letter:
                    logger.info(f"Using cached cover letter for job {job.id}")
                    return cached_letter
            
            logger.info(f"Generating cover letter for {job.title} at {job.company} with {tone} tone")
            
            # Generate prompt
            prompts = cover_letter_prompt(
                job_title=job.title,
                company_name=job.company,
                job_description=job.description,
                resume_summary=resume_summary,
                relevant_projects=relevant_projects,
                tone=tone
            )
            
            # Generate cover letter using LLM
            response = self.llm_client.generate_with_retry(
                prompt=prompts['user'],
                system_prompt=prompts['system'],
                temperature=0.7,
                max_tokens=1500
            )
            
            cover_letter_text = response.text.strip()
            
            # Cache the generated letter if user_id provided
            if user_id:
                self._cache_letter(
                    job_id=job.id,
                    user_id=user_id,
                    content=cover_letter_text,
                    tone=tone
                )
            
            logger.info("Cover letter generated successfully")
            return cover_letter_text
            
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            return f"Failed to generate cover letter: {str(e)}"
    
    def regenerate_with_tone(
        self,
        job_id: str,
        resume_summary: str,
        tone: str,
        user_id: Optional[str] = None,
        relevant_projects: Optional[list] = None
    ) -> str:
        """
        Regenerate cover letter with different tone
        
        Args:
            job_id: Job ID to generate letter for
            resume_summary: Summary of candidate's experience
            tone: Desired tone (professional, enthusiastic, technical)
            user_id: Optional user ID for caching
            relevant_projects: Optional list of relevant projects
            
        Returns:
            Regenerated cover letter text
        """
        try:
            # Validate tone
            if tone not in self.VALID_TONES:
                raise ValueError(f"Invalid tone: {tone}. Must be one of {self.VALID_TONES}")
            
            # Get job from database
            job = self._get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            logger.info(f"Regenerating cover letter with {tone} tone")
            
            # Generate new letter (bypassing cache)
            prompts = cover_letter_prompt(
                job_title=job.title,
                company_name=job.company,
                job_description=job.description,
                resume_summary=resume_summary,
                relevant_projects=relevant_projects,
                tone=tone
            )
            
            response = self.llm_client.generate_with_retry(
                prompt=prompts['user'],
                system_prompt=prompts['system'],
                temperature=0.8,  # Slightly higher for variation
                max_tokens=1500
            )
            
            cover_letter_text = response.text.strip()
            
            # Update cache with new tone
            if user_id:
                self._cache_letter(
                    job_id=job_id,
                    user_id=user_id,
                    content=cover_letter_text,
                    tone=tone
                )
            
            logger.info("Cover letter regenerated successfully")
            return cover_letter_text
            
        except Exception as e:
            logger.error(f"Cover letter regeneration failed: {e}")
            return f"Failed to regenerate cover letter: {str(e)}"
    
    def save_letter(
        self,
        job_id: str,
        user_id: str,
        content: str,
        tone: str = "professional"
    ) -> bool:
        """
        Save cover letter to database
        
        Args:
            job_id: Job ID
            user_id: User ID
            content: Cover letter content
            tone: Tone used for generation
            
        Returns:
            True if saved successfully
        """
        try:
            return self._cache_letter(job_id, user_id, content, tone)
        except Exception as e:
            logger.error(f"Failed to save cover letter: {e}")
            return False
    
    def _cache_letter(
        self,
        job_id: str,
        user_id: str,
        content: str,
        tone: str
    ) -> bool:
        """
        Cache generated cover letter in database
        
        Args:
            job_id: Job ID
            user_id: User ID
            content: Cover letter content
            tone: Tone used
            
        Returns:
            True if cached successfully
        """
        try:
            # Delete existing cached letter for this job/user/tone
            delete_query = """
                DELETE FROM cover_letters 
                WHERE job_id = ? AND user_id = ? AND tone = ?
            """
            self.db_manager.execute_update(delete_query, (job_id, user_id, tone))
            
            # Insert new cached letter
            letter = CoverLetter(
                job_id=job_id,
                user_id=user_id,
                content=content,
                tone=tone
            )
            
            insert_query = """
                INSERT INTO cover_letters (
                    id, job_id, user_id, content, tone, generated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                letter.id,
                letter.job_id,
                letter.user_id,
                letter.content,
                letter.tone,
                letter.generated_at.isoformat(),
                letter.expires_at.isoformat()
            )
            
            rows = self.db_manager.execute_update(insert_query, params)
            
            if rows > 0:
                logger.info(f"Cover letter cached for job {job_id}, user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cache cover letter: {e}")
            return False
    
    def _get_cached_letter(
        self,
        job_id: str,
        user_id: str,
        tone: str
    ) -> Optional[str]:
        """
        Get cached cover letter if not expired
        
        Args:
            job_id: Job ID
            user_id: User ID
            tone: Tone to match
            
        Returns:
            Cached cover letter content if found and valid, None otherwise
        """
        try:
            query = """
                SELECT content, expires_at 
                FROM cover_letters 
                WHERE job_id = ? AND user_id = ? AND tone = ?
                ORDER BY generated_at DESC
                LIMIT 1
            """
            
            results = self.db_manager.execute_query(query, (job_id, user_id, tone))
            
            if results:
                row = results[0]
                expires_at = datetime.fromisoformat(row['expires_at'])
                
                # Check if expired
                if datetime.now() < expires_at:
                    logger.info(f"Found valid cached cover letter")
                    return row['content']
                else:
                    logger.info(f"Cached cover letter expired")
                    # Clean up expired entry
                    self._delete_expired_letters()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached letter: {e}")
            return None
    
    def _delete_expired_letters(self):
        """Delete expired cover letters from cache"""
        try:
            query = "DELETE FROM cover_letters WHERE expires_at < ?"
            rows = self.db_manager.execute_update(
                query,
                (datetime.now().isoformat(),)
            )
            if rows > 0:
                logger.info(f"Deleted {rows} expired cover letters")
        except Exception as e:
            logger.error(f"Failed to delete expired letters: {e}")
    
    def _get_job_by_id(self, job_id: str) -> Optional[JobListing]:
        """
        Get job listing by ID from database
        
        Args:
            job_id: Job ID to retrieve
            
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
            logger.error(f"Failed to get job by ID: {e}")
            return None
    
    def get_letter_by_job(
        self,
        job_id: str,
        user_id: str,
        tone: Optional[str] = None
    ) -> Optional[str]:
        """
        Get cover letter for specific job
        
        Args:
            job_id: Job ID
            user_id: User ID
            tone: Optional tone filter
            
        Returns:
            Cover letter content if found, None otherwise
        """
        try:
            if tone:
                return self._get_cached_letter(job_id, user_id, tone)
            else:
                # Get any valid cached letter
                query = """
                    SELECT content, expires_at 
                    FROM cover_letters 
                    WHERE job_id = ? AND user_id = ? AND expires_at > ?
                    ORDER BY generated_at DESC
                    LIMIT 1
                """
                
                results = self.db_manager.execute_query(
                    query,
                    (job_id, user_id, datetime.now().isoformat())
                )
                
                if results:
                    return results[0]['content']
                return None
                
        except Exception as e:
            logger.error(f"Failed to get letter by job: {e}")
            return None
    
    def get_all_letters(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> list:
        """
        Get all cover letters for user
        
        Args:
            user_id: User ID
            include_expired: Whether to include expired letters
            
        Returns:
            List of cover letter dictionaries
        """
        try:
            if include_expired:
                query = """
                    SELECT * FROM cover_letters 
                    WHERE user_id = ?
                    ORDER BY generated_at DESC
                """
                params = (user_id,)
            else:
                query = """
                    SELECT * FROM cover_letters 
                    WHERE user_id = ? AND expires_at > ?
                    ORDER BY generated_at DESC
                """
                params = (user_id, datetime.now().isoformat())
            
            results = self.db_manager.execute_query(query, params)
            return results
            
        except Exception as e:
            logger.error(f"Failed to get all letters: {e}")
            return []
    
    def delete_letter(self, letter_id: str) -> bool:
        """
        Delete cover letter by ID
        
        Args:
            letter_id: Cover letter ID
            
        Returns:
            True if deleted successfully
        """
        try:
            query = "DELETE FROM cover_letters WHERE id = ?"
            rows = self.db_manager.execute_update(query, (letter_id,))
            return rows > 0
        except Exception as e:
            logger.error(f"Failed to delete letter: {e}")
            return False
