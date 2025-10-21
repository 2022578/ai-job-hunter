"""
Base scraper infrastructure with common utilities for web scraping.
Provides rate limiting, retry logic, and user agent rotation.
"""

import time
import random
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for web scrapers with common utilities."""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    def __init__(self, rate_limit_delay: float = 2.0, max_retries: int = 3):
        """
        Initialize base scraper.
        
        Args:
            rate_limit_delay: Minimum delay between requests in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.last_request_time = 0
        
    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.USER_AGENTS)
    
    def rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            # Add small random jitter to appear more human-like
            sleep_time += random.uniform(0, 0.5)
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def retry_on_failure(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry a function call on failure with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    backoff_time = 2 ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}. "
                        f"Retrying in {backoff_time} seconds..."
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception
    
    def add_random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """
        Add a random delay to simulate human behavior.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Adding random delay: {delay:.2f} seconds")
        time.sleep(delay)


def with_retry(max_retries: int = 3):
    """
    Decorator to add retry logic to a method.
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        backoff_time = 2 ** attempt
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {backoff_time} seconds..."
                        )
                        time.sleep(backoff_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator
