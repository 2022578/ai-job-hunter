"""
Scrapers module for GenAI Job Assistant.
Contains web scraping logic for job portals like Naukri.com.
"""

from scrapers.base_scraper import BaseScraper, with_retry
from scrapers.naukri_scraper import NaukriScraper, CaptchaDetectedException

__all__ = ['BaseScraper', 'with_retry', 'NaukriScraper', 'CaptchaDetectedException']
