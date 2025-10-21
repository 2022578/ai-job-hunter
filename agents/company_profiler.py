"""
Company Profiler Agent
Researches companies, generates fit analysis, and caches profiles.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import random

from models.company import CompanyProfile
from database.repositories.company_repository import CompanyRepository
from utils.llm_client import OllamaClient
from utils.prompts import company_summary_prompt

logger = logging.getLogger(__name__)


class CompanyProfiler:
    """
    Agent for profiling companies and assessing candidate fit.
    Aggregates data from multiple sources and uses LLM for analysis.
    """
    
    def __init__(
        self,
        company_repository: CompanyRepository,
        llm_client: OllamaClient,
        cache_duration_days: int = 30,
        rate_limit_delay: float = 2.0
    ):
        """
        Initialize Company Profiler agent.
        
        Args:
            company_repository: Repository for company data persistence
            llm_client: LLM client for generating summaries
            cache_duration_days: Number of days to cache company profiles
            rate_limit_delay: Delay between external API calls in seconds
        """
        self.company_repository = company_repository
        self.llm_client = llm_client
        self.cache_duration_days = cache_duration_days
        self.rate_limit_delay = rate_limit_delay
        
        # User agents for web scraping
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    
    def profile_company(
        self,
        company_name: str,
        force_refresh: bool = False
    ) -> Optional[CompanyProfile]:
        """
        Profile a company by aggregating data from multiple sources.
        Uses cached data if available and valid.
        
        Args:
            company_name: Name of the company to profile
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            CompanyProfile object or None if profiling fails
        """
        try:
            # Check cache first
            if not force_refresh:
                cached_profile = self.get_cached_profile(company_name)
                if cached_profile:
                    logger.info(f"Using cached profile for {company_name}")
                    return cached_profile
            
            logger.info(f"Profiling company: {company_name}")
            
            # Gather data from multiple sources
            company_data = {
                'company_name': company_name,
                'glassdoor_rating': None,
                'employee_count': None,
                'funding_stage': None,
                'recent_news': [],
                'genai_focus_score': 0.0,
                'culture_summary': ""
            }
            
            # Try to get Glassdoor data
            glassdoor_data = self._scrape_glassdoor(company_name)
            if glassdoor_data:
                company_data['glassdoor_rating'] = glassdoor_data.get('rating')
                company_data['employee_count'] = glassdoor_data.get('employee_count')
            
            # Get recent news
            news_articles = self._fetch_company_news(company_name)
            company_data['recent_news'] = news_articles
            
            # Assess GenAI focus
            genai_score = self.assess_genai_focus(company_name, news_articles)
            company_data['genai_focus_score'] = genai_score
            
            # Create company profile
            profile = CompanyProfile(
                company_name=company_data['company_name'],
                glassdoor_rating=company_data['glassdoor_rating'],
                employee_count=company_data['employee_count'],
                funding_stage=company_data['funding_stage'],
                recent_news=company_data['recent_news'],
                genai_focus_score=company_data['genai_focus_score'],
                culture_summary=company_data['culture_summary']
            )
            
            # Save to cache
            self.company_repository.save_or_update(profile)
            logger.info(f"Successfully profiled and cached {company_name}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to profile company {company_name}: {e}")
            return None
    
    def get_cached_profile(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Get cached company profile if valid.
        
        Args:
            company_name: Name of the company
            
        Returns:
            CompanyProfile if cache is valid, None otherwise
        """
        try:
            return self.company_repository.get_cached(company_name)
        except Exception as e:
            logger.error(f"Failed to get cached profile: {e}")
            return None
    
    def _scrape_glassdoor(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Scrape Glassdoor for company ratings and reviews.
        Implements rate limiting and user agent rotation.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Dictionary with rating and employee count, or None if scraping fails
        """
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            # Note: Glassdoor scraping is complex and may require authentication
            # This is a simplified implementation
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Glassdoor search URL (simplified)
            search_url = f"https://www.glassdoor.com/Search/results.htm?keyword={company_name.replace(' ', '+')}"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # This is a placeholder - actual Glassdoor scraping requires
                # more sophisticated parsing and may require authentication
                # For production, consider using Glassdoor API if available
                
                logger.info(f"Glassdoor scraping attempted for {company_name}")
                return {
                    'rating': None,  # Would parse from HTML
                    'employee_count': None  # Would parse from HTML
                }
            else:
                logger.warning(f"Glassdoor request failed with status {response.status_code}")
                return None
                
        except RequestException as e:
            logger.warning(f"Failed to scrape Glassdoor for {company_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping Glassdoor: {e}")
            return None
    
    def _fetch_company_news(self, company_name: str, max_articles: int = 5) -> List[str]:
        """
        Fetch recent company news articles.
        
        Args:
            company_name: Name of the company
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of news article titles/summaries
        """
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            news_articles = []
            
            # Try Google News RSS feed (no API key required)
            search_query = f"{company_name} AI GenAI"
            rss_url = f"https://news.google.com/rss/search?q={search_query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            
            headers = {
                'User-Agent': random.choice(self.user_agents)
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item', limit=max_articles)
                
                for item in items:
                    title = item.find('title')
                    if title:
                        news_articles.append(title.text)
                
                logger.info(f"Fetched {len(news_articles)} news articles for {company_name}")
            else:
                logger.warning(f"News fetch failed with status {response.status_code}")
            
            return news_articles
            
        except Exception as e:
            logger.warning(f"Failed to fetch news for {company_name}: {e}")
            return []
    
    def assess_genai_focus(
        self,
        company_name: str,
        news_articles: Optional[List[str]] = None
    ) -> float:
        """
        Assess company's focus on GenAI and AI technologies.
        
        Args:
            company_name: Name of the company
            news_articles: Optional list of news articles about the company
            
        Returns:
            GenAI focus score from 0.0 to 10.0
        """
        try:
            # Keywords indicating GenAI focus
            genai_keywords = [
                'genai', 'generative ai', 'llm', 'large language model',
                'gpt', 'chatgpt', 'ai model', 'machine learning',
                'artificial intelligence', 'langchain', 'autonomous agent',
                'rag', 'retrieval augmented', 'fine-tuning', 'prompt engineering'
            ]
            
            score = 0.0
            
            # Analyze news articles
            if news_articles:
                keyword_matches = 0
                total_articles = len(news_articles)
                
                for article in news_articles:
                    article_lower = article.lower()
                    for keyword in genai_keywords:
                        if keyword in article_lower:
                            keyword_matches += 1
                            break  # Count each article only once
                
                if total_articles > 0:
                    # Score based on percentage of articles mentioning GenAI
                    article_score = (keyword_matches / total_articles) * 10.0
                    score = min(article_score, 10.0)
            
            # If no news data, return a neutral score
            if score == 0.0 and not news_articles:
                score = 5.0  # Neutral score when no data available
            
            logger.info(f"GenAI focus score for {company_name}: {score:.1f}/10")
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Failed to assess GenAI focus: {e}")
            return 5.0  # Return neutral score on error
    
    def summarize_fit(
        self,
        company_profile: CompanyProfile,
        user_preferences: Dict[str, Any]
    ) -> str:
        """
        Generate LLM-powered summary assessing company-candidate fit.
        
        Args:
            company_profile: CompanyProfile object
            user_preferences: Dictionary with user preferences
            
        Returns:
            Fit analysis summary as string
        """
        try:
            # Prepare company info for prompt
            company_info = {
                'glassdoor_rating': company_profile.glassdoor_rating,
                'employee_count': company_profile.employee_count,
                'funding_stage': company_profile.funding_stage,
                'recent_news': company_profile.recent_news,
                'genai_focus_score': company_profile.genai_focus_score
            }
            
            # Generate prompt
            prompts = company_summary_prompt(
                company_name=company_profile.company_name,
                company_info=company_info,
                user_preferences=user_preferences
            )
            
            # Generate summary using LLM
            response = self.llm_client.generate_with_retry(
                prompt=prompts['user'],
                system_prompt=prompts['system'],
                temperature=0.7,
                max_tokens=1000
            )
            
            summary = response.text.strip()
            
            # Update company profile with summary
            company_profile.culture_summary = summary
            self.company_repository.save_or_update(company_profile)
            
            logger.info(f"Generated fit summary for {company_profile.company_name}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate fit summary: {e}")
            return f"Unable to generate fit analysis for {company_profile.company_name}. Please try again later."
    
    def refresh_profile(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Force refresh a company profile, bypassing cache.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Updated CompanyProfile or None if refresh fails
        """
        return self.profile_company(company_name, force_refresh=True)
    
    def clean_expired_profiles(self) -> int:
        """
        Remove expired company profiles from cache.
        
        Returns:
            Number of profiles removed
        """
        try:
            count = self.company_repository.clean_expired_cache()
            logger.info(f"Cleaned {count} expired company profiles")
            return count
        except Exception as e:
            logger.error(f"Failed to clean expired profiles: {e}")
            return 0
    
    def get_all_profiles(self, limit: Optional[int] = None) -> List[CompanyProfile]:
        """
        Get all cached company profiles.
        
        Args:
            limit: Optional limit on number of profiles to return
            
        Returns:
            List of CompanyProfile objects
        """
        try:
            return self.company_repository.find_all(limit=limit)
        except Exception as e:
            logger.error(f"Failed to get all profiles: {e}")
            return []
