"""
Job Search Agent - Orchestrates job discovery, filtering, and persistence.
Implements autonomous job search with GenAI-focused filtering.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import re

from models.job import JobListing
from database.repositories.job_repository import JobRepository
from scrapers.naukri_scraper import NaukriScraper

logger = logging.getLogger(__name__)


class SearchCriteria:
    """Search criteria configuration for job search."""
    
    def __init__(
        self,
        keywords: List[str],
        min_salary_lakhs: int = 35,
        location: Optional[str] = None,
        experience: Optional[str] = None,
        max_pages: int = 5
    ):
        """
        Initialize search criteria.
        
        Args:
            keywords: List of keywords to search for
            min_salary_lakhs: Minimum salary threshold in lakhs
            location: Location filter (optional)
            experience: Experience filter (optional)
            max_pages: Maximum pages to scrape
        """
        self.keywords = keywords
        self.min_salary_lakhs = min_salary_lakhs
        self.location = location
        self.experience = experience
        self.max_pages = max_pages


class JobSearchAgent:
    """
    Agent responsible for discovering job listings, applying filters,
    and storing results in the database.
    """
    
    # GenAI-related keywords for filtering
    GENAI_KEYWORDS = [
        "genai",
        "gen ai",
        "llm",
        "large language model",
        "autonomous agents",
        "langchain",
        "langgraph",
        "gpt",
        "claude",
        "gemini",
        "llama",
        "mistral",
        "rag",
        "retrieval augmented generation",
        "prompt engineering",
        "fine-tuning",
        "foundation models",
        "transformer",
        "nlp",
        "natural language processing",
        "conversational ai",
        "chatbot",
        "ai agent"
    ]
    
    def __init__(
        self,
        job_repository: JobRepository,
        scraper: Optional[NaukriScraper] = None
    ):
        """
        Initialize Job Search Agent.
        
        Args:
            job_repository: Repository for job persistence
            scraper: Naukri scraper instance (optional, will create if not provided)
        """
        self.job_repository = job_repository
        self.scraper = scraper
        self._scraper_owned = scraper is None
    
    def search(self, criteria: SearchCriteria) -> List[JobListing]:
        """
        Execute job search with filtering and persistence.
        
        This is the main orchestration method that:
        1. Scrapes jobs from Naukri
        2. Applies keyword filters
        3. Applies salary filters
        4. Deduplicates against database
        5. Converts to JobListing objects
        6. Persists to database
        
        Args:
            criteria: Search criteria configuration
            
        Returns:
            List of newly discovered and stored JobListing objects
        """
        logger.info(f"Starting job search with criteria: keywords={criteria.keywords}, "
                   f"min_salary={criteria.min_salary_lakhs}L")
        
        try:
            # Initialize scraper if needed
            if self.scraper is None:
                self.scraper = NaukriScraper(rate_limit_delay=2.0, headless=True)
            
            # Start scraper
            if self._scraper_owned:
                self.scraper.start()
            
            # Step 1: Scrape jobs from Naukri
            logger.info("Step 1: Scraping jobs from Naukri.com")
            raw_jobs = self.scraper.search_jobs(
                keywords=criteria.keywords,
                min_salary=criteria.min_salary_lakhs,
                location=criteria.location,
                experience=criteria.experience,
                max_pages=criteria.max_pages
            )
            
            logger.info(f"Scraped {len(raw_jobs)} jobs from Naukri")
            
            # Step 2: Apply keyword filter for GenAI-related terms
            logger.info("Step 2: Applying GenAI keyword filter")
            filtered_by_keywords = self.filter_by_keywords(raw_jobs, self.GENAI_KEYWORDS)
            
            # Step 3: Apply salary filter
            logger.info("Step 3: Applying salary filter")
            filtered_by_salary = self.filter_by_salary(
                filtered_by_keywords,
                criteria.min_salary_lakhs
            )
            
            # Step 4: Deduplicate against existing database entries
            logger.info("Step 4: Deduplicating against database")
            unique_jobs = self.deduplicate(filtered_by_salary)
            
            # Step 5: Convert to JobListing objects
            logger.info("Step 5: Converting to JobListing objects")
            job_listings = self._convert_to_job_listings(unique_jobs)
            
            # Step 6: Persist to database
            logger.info("Step 6: Persisting jobs to database")
            stored_count = self._persist_jobs(job_listings)
            
            logger.info(f"Job search complete: {stored_count} new jobs stored")
            
            return job_listings
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            raise
        
        finally:
            # Clean up scraper if we own it
            if self._scraper_owned and self.scraper:
                self.scraper.stop()
    
    def filter_by_keywords(
        self,
        jobs: List[Dict[str, Any]],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by GenAI-related keywords.
        
        Checks if job title, description, or skills contain at least one
        of the specified keywords (case-insensitive).
        
        Args:
            jobs: List of raw job dictionaries
            keywords: List of keywords to match
            
        Returns:
            Filtered list of jobs containing at least one keyword
        """
        filtered_jobs = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for job in jobs:
            # Gather all searchable text
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            description_snippet = job.get('description_snippet', '').lower()
            skills = ' '.join(job.get('skills', [])).lower()
            
            search_text = f"{title} {description} {description_snippet} {skills}"
            
            # Check if any keyword is present
            if any(keyword in search_text for keyword in keywords_lower):
                filtered_jobs.append(job)
                logger.debug(f"Job matched keywords: {job.get('title', 'Unknown')}")
            else:
                logger.debug(f"Job filtered out (no keyword match): {job.get('title', 'Unknown')}")
        
        logger.info(f"Keyword filter: {len(jobs)} -> {len(filtered_jobs)} jobs")
        return filtered_jobs
    
    def filter_by_salary(
        self,
        jobs: List[Dict[str, Any]],
        min_salary_lakhs: int
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by minimum salary threshold.
        
        Parses salary strings and filters jobs that meet the minimum
        salary requirement. Jobs with undisclosed salaries are included
        to avoid missing opportunities.
        
        Args:
            jobs: List of job dictionaries
            min_salary_lakhs: Minimum salary in lakhs (e.g., 35 for ₹35L)
            
        Returns:
            Filtered list of jobs meeting salary requirement
        """
        filtered_jobs = []
        
        for job in jobs:
            salary_str = job.get('salary', '')
            
            # Include jobs with no salary information
            if not salary_str or salary_str.lower() in ['not disclosed', 'not specified', '']:
                filtered_jobs.append(job)
                logger.debug(f"Job included (salary not disclosed): {job.get('title', 'Unknown')}")
                continue
            
            # Try to parse salary
            try:
                salary_value = self._parse_salary(salary_str)
                
                if salary_value is None:
                    # If we can't parse, include it to be safe
                    filtered_jobs.append(job)
                    logger.debug(f"Job included (salary unparseable): {job.get('title', 'Unknown')}")
                elif salary_value >= min_salary_lakhs:
                    filtered_jobs.append(job)
                    logger.debug(f"Job matched salary (₹{salary_value}L): {job.get('title', 'Unknown')}")
                else:
                    logger.debug(f"Job filtered out (salary ₹{salary_value}L < ₹{min_salary_lakhs}L): "
                               f"{job.get('title', 'Unknown')}")
                    
            except Exception as e:
                logger.warning(f"Error parsing salary '{salary_str}': {str(e)}")
                # Include job if salary parsing fails
                filtered_jobs.append(job)
        
        logger.info(f"Salary filter (≥₹{min_salary_lakhs}L): {len(jobs)} -> {len(filtered_jobs)} jobs")
        return filtered_jobs
    
    def _parse_salary(self, salary_str: str) -> Optional[int]:
        """
        Parse salary string to extract maximum salary in lakhs.
        
        Handles various formats:
        - "15-20 Lacs PA"
        - "₹15-20 Lakhs"
        - "35 LPA"
        - "50,00,000 - 60,00,000 PA"
        
        Args:
            salary_str: Salary string to parse
            
        Returns:
            Maximum salary in lakhs, or None if unparseable
        """
        if not salary_str:
            return None
        
        salary_lower = salary_str.lower()
        
        # Extract all numbers from the string
        numbers = re.findall(r'(\d+(?:,\d+)*)', salary_str)
        
        if not numbers:
            return None
        
        # Remove commas and convert to integers
        numbers = [int(n.replace(',', '')) for n in numbers]
        
        # Determine if values are in lakhs or absolute amounts
        if 'lakh' in salary_lower or 'lac' in salary_lower or 'lpa' in salary_lower:
            # Values are already in lakhs
            return max(numbers)
        elif any(n > 1000 for n in numbers):
            # Values appear to be absolute amounts (e.g., 50,00,000)
            # Convert to lakhs
            return max(numbers) // 100000
        else:
            # Assume values are in lakhs if small numbers
            return max(numbers)
    
    def deduplicate(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate jobs based on source URL.
        
        Checks against existing database entries to avoid storing
        duplicate job listings.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of unique jobs not already in database
        """
        unique_jobs = []
        
        for job in jobs:
            job_url = job.get('url')
            
            if not job_url:
                logger.warning(f"Job has no URL, skipping: {job.get('title', 'Unknown')}")
                continue
            
            # Check if job already exists in database
            if not self.job_repository.exists_by_url(job_url):
                unique_jobs.append(job)
                logger.debug(f"New job: {job.get('title', 'Unknown')}")
            else:
                logger.debug(f"Duplicate job (already in DB): {job.get('title', 'Unknown')}")
        
        logger.info(f"Deduplication: {len(jobs)} -> {len(unique_jobs)} unique jobs")
        return unique_jobs
    
    def _convert_to_job_listings(
        self,
        raw_jobs: List[Dict[str, Any]]
    ) -> List[JobListing]:
        """
        Convert raw job dictionaries to JobListing objects.
        
        Args:
            raw_jobs: List of raw job dictionaries from scraper
            
        Returns:
            List of JobListing objects
        """
        job_listings = []
        
        for raw_job in raw_jobs:
            try:
                # Parse salary range
                salary_min, salary_max = self._parse_salary_range(raw_job.get('salary', ''))
                
                # Parse posted date
                posted_date = self._parse_posted_date(raw_job.get('posted_date'))
                
                # Detect remote type
                remote_type = self._detect_remote_type(raw_job)
                
                # Create JobListing object
                job_listing = JobListing(
                    title=raw_job.get('title', 'Unknown Title'),
                    company=raw_job.get('company', 'Unknown Company'),
                    description=raw_job.get('description', raw_job.get('description_snippet', '')),
                    source=raw_job.get('source', 'naukri'),
                    source_url=raw_job.get('url', ''),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    location=raw_job.get('location', ''),
                    remote_type=remote_type,
                    required_skills=raw_job.get('skills', []),
                    posted_date=posted_date,
                    raw_html=raw_job.get('raw_html', ''),
                    created_at=datetime.now()
                )
                
                job_listings.append(job_listing)
                
            except Exception as e:
                logger.error(f"Error converting job to JobListing: {str(e)}")
                logger.debug(f"Problematic job data: {raw_job}")
                continue
        
        logger.info(f"Converted {len(job_listings)} jobs to JobListing objects")
        return job_listings
    
    def _parse_salary_range(self, salary_str: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse salary string to extract min and max salary in lakhs.
        
        Args:
            salary_str: Salary string to parse
            
        Returns:
            Tuple of (min_salary, max_salary) in lakhs, or (None, None)
        """
        if not salary_str or salary_str.lower() in ['not disclosed', 'not specified']:
            return None, None
        
        try:
            salary_lower = salary_str.lower()
            
            # Extract all numbers
            numbers = re.findall(r'(\d+(?:,\d+)*)', salary_str)
            
            if not numbers:
                return None, None
            
            # Remove commas and convert to integers
            numbers = [int(n.replace(',', '')) for n in numbers]
            
            # Determine if values are in lakhs or absolute amounts
            if 'lakh' in salary_lower or 'lac' in salary_lower or 'lpa' in salary_lower:
                # Values are already in lakhs
                if len(numbers) >= 2:
                    return min(numbers), max(numbers)
                else:
                    return numbers[0], numbers[0]
            elif any(n > 1000 for n in numbers):
                # Values appear to be absolute amounts
                # Convert to lakhs
                numbers_in_lakhs = [n // 100000 for n in numbers]
                if len(numbers_in_lakhs) >= 2:
                    return min(numbers_in_lakhs), max(numbers_in_lakhs)
                else:
                    return numbers_in_lakhs[0], numbers_in_lakhs[0]
            else:
                # Assume values are in lakhs
                if len(numbers) >= 2:
                    return min(numbers), max(numbers)
                else:
                    return numbers[0], numbers[0]
                    
        except Exception as e:
            logger.warning(f"Error parsing salary range '{salary_str}': {str(e)}")
            return None, None
    
    def _parse_posted_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse posted date string to datetime object.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            datetime object or None if unparseable
        """
        if not date_str:
            return None
        
        try:
            # Handle relative dates like "2 days ago", "1 week ago"
            date_lower = date_str.lower()
            
            if 'today' in date_lower or 'just now' in date_lower:
                return datetime.now()
            elif 'yesterday' in date_lower:
                from datetime import timedelta
                return datetime.now() - timedelta(days=1)
            elif 'day' in date_lower:
                # Extract number of days
                match = re.search(r'(\d+)\s*day', date_lower)
                if match:
                    from datetime import timedelta
                    days = int(match.group(1))
                    return datetime.now() - timedelta(days=days)
            elif 'week' in date_lower:
                # Extract number of weeks
                match = re.search(r'(\d+)\s*week', date_lower)
                if match:
                    from datetime import timedelta
                    weeks = int(match.group(1))
                    return datetime.now() - timedelta(weeks=weeks)
            
            # If we can't parse, return None
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing posted date '{date_str}': {str(e)}")
            return None
    
    def _detect_remote_type(self, job: Dict[str, Any]) -> str:
        """
        Detect if job is remote, hybrid, or onsite.
        
        Args:
            job: Job dictionary
            
        Returns:
            "remote", "hybrid", or "onsite"
        """
        # Gather all text to search
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        description_snippet = job.get('description_snippet', '').lower()
        location = job.get('location', '').lower()
        
        search_text = f"{title} {description} {description_snippet} {location}"
        
        # Check for remote indicators
        remote_keywords = ['remote', 'work from home', 'wfh', 'work from anywhere']
        if any(keyword in search_text for keyword in remote_keywords):
            return 'remote'
        
        # Check for hybrid indicators
        hybrid_keywords = ['hybrid', 'flexible', 'part remote', 'partially remote']
        if any(keyword in search_text for keyword in hybrid_keywords):
            return 'hybrid'
        
        # Default to onsite
        return 'onsite'
    
    def _persist_jobs(self, job_listings: List[JobListing]) -> int:
        """
        Persist job listings to database.
        
        Args:
            job_listings: List of JobListing objects to save
            
        Returns:
            Number of jobs successfully stored
        """
        stored_count = 0
        
        for job in job_listings:
            try:
                if self.job_repository.save(job):
                    stored_count += 1
                    logger.debug(f"Stored job: {job.title} at {job.company}")
                else:
                    logger.warning(f"Failed to store job: {job.title}")
            except Exception as e:
                logger.error(f"Error storing job {job.title}: {str(e)}")
                continue
        
        logger.info(f"Successfully stored {stored_count}/{len(job_listings)} jobs")
        return stored_count
