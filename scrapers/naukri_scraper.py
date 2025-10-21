"""
Naukri.com scraper with anti-detection measures.
Handles job search, login, and data extraction with Selenium.
"""

import logging
import time
import random
from typing import List, Dict, Optional, Any
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains

from scrapers.base_scraper import BaseScraper, with_retry
from utils.security import CredentialManager

logger = logging.getLogger(__name__)


class CaptchaDetectedException(Exception):
    """Raised when a CAPTCHA is detected on the page."""
    pass


class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com with anti-detection measures."""
    
    NAUKRI_BASE_URL = "https://www.naukri.com"
    NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
    NAUKRI_SEARCH_URL = "https://www.naukri.com/jobs-in-india"
    
    def __init__(self, rate_limit_delay: float = 2.0, max_retries: int = 3, headless: bool = True):
        """
        Initialize Naukri scraper.
        
        Args:
            rate_limit_delay: Minimum delay between requests in seconds
            max_retries: Maximum number of retry attempts
            headless: Whether to run browser in headless mode
        """
        super().__init__(rate_limit_delay, max_retries)
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.is_logged_in = False
        
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Set up Selenium WebDriver with anti-detection configurations.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        chrome_options = Options()
        
        # Headless mode
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set random user agent
        user_agent = self.get_random_user_agent()
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-notifications')
        
        # Disable images for faster loading (optional)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Execute CDP commands to hide webdriver property
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent
            })
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            logger.info("Chrome WebDriver initialized successfully")
            return driver
            
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            raise
    
    def start(self):
        """Start the scraper by initializing the WebDriver."""
        if self.driver is None:
            self.driver = self._setup_driver()
            logger.info("Naukri scraper started")
    
    def stop(self):
        """Stop the scraper and close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.is_logged_in = False
            logger.info("Naukri scraper stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def _check_for_captcha(self) -> bool:
        """
        Check if a CAPTCHA is present on the current page.
        
        Returns:
            True if CAPTCHA detected, False otherwise
        """
        if not self.driver:
            return False
        
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "g-recaptcha",
            "hcaptcha",
            "challenge",
            "verify you are human"
        ]
        
        try:
            page_source = self.driver.page_source.lower()
            
            for indicator in captcha_indicators:
                if indicator in page_source:
                    logger.warning(f"CAPTCHA detected: found '{indicator}' in page source")
                    return True
            
            # Check for common CAPTCHA elements
            captcha_selectors = [
                "//iframe[contains(@src, 'recaptcha')]",
                "//iframe[contains(@src, 'captcha')]",
                "//*[contains(@class, 'captcha')]",
                "//*[contains(@id, 'captcha')]"
            ]
            
            for selector in captcha_selectors:
                try:
                    self.driver.find_element(By.XPATH, selector)
                    logger.warning(f"CAPTCHA detected: found element matching '{selector}'")
                    return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {str(e)}")
            return False
    
    def _handle_captcha(self):
        """
        Handle CAPTCHA detection.
        
        Raises:
            CaptchaDetectedException: Always raised to notify caller
        """
        logger.error("CAPTCHA detected. Manual intervention required.")
        
        if not self.headless and self.driver:
            logger.info("Browser is visible. Please solve the CAPTCHA manually.")
            logger.info("Waiting 60 seconds for manual CAPTCHA resolution...")
            time.sleep(60)
            
            # Check if CAPTCHA is still present
            if self._check_for_captcha():
                raise CaptchaDetectedException("CAPTCHA still present after waiting")
            else:
                logger.info("CAPTCHA appears to be resolved")
                return
        
        raise CaptchaDetectedException("CAPTCHA detected and cannot be resolved automatically")
    
    def _simulate_human_typing(self, element, text: str):
        """
        Simulate human-like typing behavior.
        
        Args:
            element: Selenium WebElement to type into
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _simulate_mouse_movement(self, element):
        """
        Simulate human-like mouse movement to an element.
        
        Args:
            element: Selenium WebElement to move to
        """
        if self.driver:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            self.add_random_delay(0.2, 0.5)

    
    @with_retry(max_retries=3)
    def login(self, username: str, password: str) -> bool:
        """
        Login to Naukri.com with encrypted credentials.
        
        Args:
            username: Naukri username/email
            password: Naukri password
            
        Returns:
            True if login successful, False otherwise
            
        Raises:
            CaptchaDetectedException: If CAPTCHA is detected
        """
        if not self.driver:
            self.start()
        
        try:
            logger.info("Navigating to Naukri login page")
            self.driver.get(self.NAUKRI_LOGIN_URL)
            self.rate_limit()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                self._handle_captcha()
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 10)
            
            # Find and fill username field
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            self._simulate_mouse_movement(username_field)
            username_field.clear()
            self._simulate_human_typing(username_field, username)
            
            self.add_random_delay(0.5, 1.0)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "passwordField")
            self._simulate_mouse_movement(password_field)
            password_field.clear()
            self._simulate_human_typing(password_field, password)
            
            self.add_random_delay(0.5, 1.0)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self._simulate_mouse_movement(login_button)
            login_button.click()
            
            logger.info("Login form submitted")
            self.rate_limit()
            
            # Check for CAPTCHA after login attempt
            if self._check_for_captcha():
                self._handle_captcha()
            
            # Wait for redirect or error message
            time.sleep(3)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "nlogin" not in current_url or "mnjuser" in self.driver.page_source:
                logger.info("Login successful")
                self.is_logged_in = True
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except TimeoutException:
            logger.error("Timeout waiting for login elements")
            return False
        except NoSuchElementException as e:
            logger.error(f"Login element not found: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise
    
    def search_jobs(
        self, 
        keywords: List[str], 
        min_salary: Optional[int] = None,
        location: Optional[str] = None,
        experience: Optional[str] = None,
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs on Naukri.com with filters.
        
        Args:
            keywords: List of keywords to search for
            min_salary: Minimum salary in lakhs (e.g., 35 for ₹35L)
            location: Location filter
            experience: Experience filter (e.g., "5-10")
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of job listings with basic information
        """
        if not self.driver:
            self.start()
        
        all_jobs = []
        
        try:
            # Build search URL
            search_query = " ".join(keywords)
            search_url = f"{self.NAUKRI_SEARCH_URL}?k={search_query.replace(' ', '%20')}"
            
            if location:
                search_url += f"&l={location.replace(' ', '%20')}"
            
            logger.info(f"Searching for jobs with query: {search_query}")
            self.driver.get(search_url)
            self.rate_limit()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                self._handle_captcha()
            
            # Extract jobs from multiple pages
            for page in range(1, max_pages + 1):
                logger.info(f"Scraping page {page}/{max_pages}")
                
                jobs_on_page = self._extract_job_listings_from_page()
                all_jobs.extend(jobs_on_page)
                
                logger.info(f"Found {len(jobs_on_page)} jobs on page {page}")
                
                # Try to navigate to next page
                if page < max_pages:
                    if not self._go_to_next_page():
                        logger.info("No more pages available")
                        break
                    
                    self.rate_limit()
            
            logger.info(f"Total jobs found: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            raise
    
    def _extract_job_listings_from_page(self) -> List[Dict[str, Any]]:
        """
        Extract job listings from the current search results page.
        
        Returns:
            List of job dictionaries with basic information
        """
        jobs = []
        
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for job listings to load
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobTuple"))
            )
            
            # Find all job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "jobTuple")
            
            for card in job_cards:
                try:
                    job_data = self._parse_job_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error parsing job card: {str(e)}")
                    continue
            
        except TimeoutException:
            logger.warning("Timeout waiting for job listings")
        except Exception as e:
            logger.error(f"Error extracting job listings: {str(e)}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Parse a single job card element.
        
        Args:
            card: Selenium WebElement representing a job card
            
        Returns:
            Dictionary with job information or None if parsing fails
        """
        try:
            job_data = {
                'scraped_at': datetime.now().isoformat(),
                'source': 'naukri'
            }
            
            # Job title and URL
            try:
                title_element = card.find_element(By.CLASS_NAME, "title")
                job_data['title'] = title_element.text.strip()
                job_data['url'] = title_element.get_attribute('href')
            except NoSuchElementException:
                return None
            
            # Company name
            try:
                company_element = card.find_element(By.CLASS_NAME, "companyInfo")
                job_data['company'] = company_element.text.strip()
            except NoSuchElementException:
                job_data['company'] = "Unknown"
            
            # Experience
            try:
                exp_element = card.find_element(By.CLASS_NAME, "expwdth")
                job_data['experience'] = exp_element.text.strip()
            except NoSuchElementException:
                job_data['experience'] = None
            
            # Salary
            try:
                salary_element = card.find_element(By.CLASS_NAME, "salaryInfo")
                job_data['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                job_data['salary'] = None
            
            # Location
            try:
                location_element = card.find_element(By.CLASS_NAME, "locWdth")
                job_data['location'] = location_element.text.strip()
            except NoSuchElementException:
                job_data['location'] = None
            
            # Job description snippet
            try:
                desc_element = card.find_element(By.CLASS_NAME, "job-description")
                job_data['description_snippet'] = desc_element.text.strip()
            except NoSuchElementException:
                job_data['description_snippet'] = None
            
            # Posted date
            try:
                date_element = card.find_element(By.CLASS_NAME, "jobTupleFooter")
                job_data['posted_date'] = date_element.text.strip()
            except NoSuchElementException:
                job_data['posted_date'] = None
            
            return job_data
            
        except Exception as e:
            logger.warning(f"Error parsing job card: {str(e)}")
            return None
    
    def _go_to_next_page(self) -> bool:
        """
        Navigate to the next page of search results.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Find next page button
            next_button = self.driver.find_element(
                By.XPATH, 
                "//a[contains(@class, 'fright') and contains(text(), 'Next')]"
            )
            
            if next_button.is_enabled():
                self._simulate_mouse_movement(next_button)
                next_button.click()
                self.add_random_delay(1.0, 2.0)
                return True
            else:
                return False
                
        except NoSuchElementException:
            logger.info("Next page button not found")
            return False
        except Exception as e:
            logger.warning(f"Error navigating to next page: {str(e)}")
            return False
    
    def get_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information from a job posting page.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dictionary with detailed job information
        """
        if not self.driver:
            self.start()
        
        try:
            logger.info(f"Fetching job details from: {job_url}")
            self.driver.get(job_url)
            self.rate_limit()
            
            # Check for CAPTCHA
            if self._check_for_captcha():
                self._handle_captcha()
            
            wait = WebDriverWait(self.driver, 10)
            
            job_details = {
                'url': job_url,
                'scraped_at': datetime.now().isoformat(),
                'source': 'naukri'
            }
            
            # Job title
            try:
                title = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jd-header-title"))
                )
                job_details['title'] = title.text.strip()
            except TimeoutException:
                logger.warning("Could not find job title")
            
            # Company name
            try:
                company = self.driver.find_element(By.CLASS_NAME, "jd-header-comp-name")
                job_details['company'] = company.text.strip()
            except NoSuchElementException:
                pass
            
            # Experience
            try:
                exp_element = self.driver.find_element(
                    By.XPATH, 
                    "//span[contains(text(), 'Experience')]/following-sibling::span"
                )
                job_details['experience'] = exp_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Salary
            try:
                salary_element = self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'Salary')]/following-sibling::span"
                )
                job_details['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Location
            try:
                location_element = self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'Location')]/following-sibling::span"
                )
                job_details['location'] = location_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Job description
            try:
                desc_element = self.driver.find_element(By.CLASS_NAME, "jd-desc")
                job_details['description'] = desc_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Skills
            try:
                skills_section = self.driver.find_element(By.CLASS_NAME, "key-skill")
                skill_elements = skills_section.find_elements(By.TAG_NAME, "a")
                job_details['skills'] = [skill.text.strip() for skill in skill_elements]
            except NoSuchElementException:
                job_details['skills'] = []
            
            # Remote type (if mentioned)
            job_details['remote_type'] = self._detect_remote_type(
                job_details.get('description', '') + ' ' + job_details.get('title', '')
            )
            
            # Store raw HTML for future re-parsing
            job_details['raw_html'] = self.driver.page_source
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error fetching job details: {str(e)}")
            return None
    
    def _detect_remote_type(self, text: str) -> str:
        """
        Detect if job is remote, hybrid, or onsite from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            "remote", "hybrid", or "onsite"
        """
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['remote', 'work from home', 'wfh']):
            return 'remote'
        elif any(keyword in text_lower for keyword in ['hybrid', 'flexible']):
            return 'hybrid'
        else:
            return 'onsite'
    
    def deduplicate_jobs(
        self, 
        new_jobs: List[Dict[str, Any]], 
        existing_urls: set
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate jobs based on URL.
        
        Args:
            new_jobs: List of newly scraped jobs
            existing_urls: Set of URLs already in database
            
        Returns:
            List of unique jobs not in database
        """
        unique_jobs = []
        
        for job in new_jobs:
            job_url = job.get('url')
            if job_url and job_url not in existing_urls:
                unique_jobs.append(job)
            else:
                logger.debug(f"Skipping duplicate job: {job.get('title', 'Unknown')}")
        
        logger.info(f"Deduplicated: {len(new_jobs)} -> {len(unique_jobs)} unique jobs")
        return unique_jobs
    
    def filter_by_keywords(
        self, 
        jobs: List[Dict[str, Any]], 
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by required keywords in title or description.
        
        Args:
            jobs: List of job dictionaries
            keywords: List of keywords to match (case-insensitive)
            
        Returns:
            Filtered list of jobs containing at least one keyword
        """
        filtered_jobs = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for job in jobs:
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            description_snippet = job.get('description_snippet', '').lower()
            
            search_text = f"{title} {description} {description_snippet}"
            
            if any(keyword in search_text for keyword in keywords_lower):
                filtered_jobs.append(job)
        
        logger.info(f"Keyword filter: {len(jobs)} -> {len(filtered_jobs)} jobs")
        return filtered_jobs
    
    def filter_by_salary(
        self, 
        jobs: List[Dict[str, Any]], 
        min_salary_lakhs: int
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by minimum salary threshold.
        
        Args:
            jobs: List of job dictionaries
            min_salary_lakhs: Minimum salary in lakhs (e.g., 35 for ₹35L)
            
        Returns:
            Filtered list of jobs meeting salary requirement
        """
        filtered_jobs = []
        
        for job in jobs:
            salary_str = job.get('salary', '')
            
            if not salary_str or salary_str == 'Not disclosed':
                # Include jobs with undisclosed salary
                filtered_jobs.append(job)
                continue
            
            # Try to extract salary numbers
            try:
                # Look for patterns like "15-20 Lacs PA" or "₹15-20 Lakhs"
                import re
                numbers = re.findall(r'(\d+)', salary_str)
                
                if numbers:
                    # Take the maximum salary mentioned
                    max_salary = max([int(n) for n in numbers])
                    
                    if max_salary >= min_salary_lakhs:
                        filtered_jobs.append(job)
                else:
                    # If we can't parse, include it to be safe
                    filtered_jobs.append(job)
                    
            except Exception as e:
                logger.warning(f"Error parsing salary '{salary_str}': {str(e)}")
                # Include job if salary parsing fails
                filtered_jobs.append(job)
        
        logger.info(f"Salary filter (≥{min_salary_lakhs}L): {len(jobs)} -> {len(filtered_jobs)} jobs")
        return filtered_jobs
