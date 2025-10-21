"""
Background Scheduler Service Runner
Runs the task scheduler independently of the Streamlit UI.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scheduler import TaskScheduler, create_scheduler_service
from agents.orchestrator import LangGraphOrchestrator
from agents.job_search_agent import JobSearchAgent, SearchCriteria
from agents.match_scorer import MatchScorer
from agents.resume_optimizer import ResumeOptimizer
from agents.cover_letter_generator import CoverLetterGenerator
from agents.interview_prep_agent import InterviewPrepAgent
from agents.company_profiler import CompanyProfiler
from agents.job_tracker import JobTracker
from utils.notification_manager import UnifiedNotificationService
from utils.llm_client import OllamaClient
from database.db_manager import DatabaseManager
from database.repositories.job_repository import JobRepository
from database.repositories.user_repository import UserRepository
from database.repositories.company_repository import CompanyRepository
from database.repositories.application_repository import ApplicationRepository
from database.repositories.question_repository import QuestionRepository
from models.user import UserProfile
import yaml


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def initialize_agents(config):
    """Initialize all agents and dependencies."""
    try:
        logger.info("Initializing agents and dependencies...")
        
        # Initialize database
        db_path = config.get('database', {}).get('path', 'data/job_assistant.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        # Initialize repositories
        job_repository = JobRepository(db_manager)
        user_repository = UserRepository(db_manager)
        company_repository = CompanyRepository(db_manager)
        application_repository = ApplicationRepository(db_manager)
        question_repository = QuestionRepository(db_manager)
        
        # Initialize LLM client
        llm_config = config.get('llm', {})
        llm_client = OllamaClient(
            model_name=llm_config.get('model_name', 'llama3'),
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 2000)
        )
        
        # Initialize agents
        job_search_agent = JobSearchAgent(job_repository=job_repository)
        
        match_scorer = MatchScorer(
            job_repository=job_repository,
            scoring_weights=config.get('scoring', {})
        )
        
        resume_optimizer = ResumeOptimizer(
            llm_client=llm_client,
            user_repository=user_repository
        )
        
        cover_letter_generator = CoverLetterGenerator(
            llm_client=llm_client,
            application_repository=application_repository
        )
        
        interview_prep_agent = InterviewPrepAgent(
            llm_client=llm_client,
            question_repository=question_repository
        )
        
        company_profiler = CompanyProfiler(
            llm_client=llm_client,
            company_repository=company_repository,
            cache_duration_days=config.get('company_profiling', {}).get('cache_duration_days', 30)
        )
        
        job_tracker = JobTracker(
            application_repository=application_repository,
            job_repository=job_repository
        )
        
        # Initialize notification service
        notification_service = UnifiedNotificationService(
            user_repository=user_repository,
            config=config.get('notifications', {})
        )
        
        # Initialize orchestrator
        orchestrator = LangGraphOrchestrator(
            job_search_agent=job_search_agent,
            match_scorer=match_scorer,
            resume_optimizer=resume_optimizer,
            cover_letter_generator=cover_letter_generator,
            interview_prep_agent=interview_prep_agent,
            company_profiler=company_profiler,
            job_tracker=job_tracker,
            notification_service=notification_service
        )
        
        logger.info("All agents initialized successfully")
        
        return orchestrator, user_repository
        
    except Exception as e:
        logger.error(f"Error initializing agents: {e}")
        raise


def get_user_profile(user_repository: UserRepository, config):
    """Get or create user profile."""
    try:
        # Try to get existing user
        users = user_repository.find_all()
        
        if users:
            user_profile = users[0]
            logger.info(f"Using existing user profile: {user_profile.name}")
        else:
            # Create default user from config
            user_config = config.get('user', {})
            user_profile = UserProfile(
                name=user_config.get('name', 'Default User'),
                email=user_config.get('email', 'user@example.com'),
                skills=user_config.get('skills', []),
                experience_years=user_config.get('experience_years', 0),
                target_salary=user_config.get('target_salary', 3500000),
                preferred_locations=config.get('job_search', {}).get('preferred_locations', []),
                preferred_remote=config.get('job_search', {}).get('remote_preference', True),
                desired_tech_stack=user_config.get('desired_tech_stack', [])
            )
            
            # Save user profile
            user_repository.save(user_profile)
            logger.info(f"Created new user profile: {user_profile.name}")
        
        return user_profile
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise


def get_search_criteria(config):
    """Get search criteria from config."""
    job_search_config = config.get('job_search', {})
    
    return SearchCriteria(
        keywords=job_search_config.get('keywords', ['GenAI', 'LLM']),
        min_salary_lakhs=job_search_config.get('min_salary', 3500000) // 100000,
        location=None,  # Will search all locations
        experience=None,
        max_pages=5
    )


def main():
    """Main entry point for scheduler service."""
    try:
        logger.info("=" * 60)
        logger.info("Starting GenAI Job Assistant Scheduler Service")
        logger.info("=" * 60)
        
        # Load configuration
        config = load_config()
        
        # Initialize agents
        orchestrator, user_repository = initialize_agents(config)
        
        # Get user profile
        user_profile = get_user_profile(user_repository, config)
        
        # Get search criteria
        search_criteria = get_search_criteria(config)
        
        # Create and configure scheduler
        scheduler = create_scheduler_service(
            orchestrator=orchestrator,
            search_criteria=search_criteria,
            user_profile=user_profile,
            user_id=user_profile.id,
            config_path="config/config.yaml"
        )
        
        # Set up signal handlers for graceful shutdown
        scheduler.setup_signal_handlers()
        
        # Start scheduler
        scheduler.start()
        
        logger.info("Scheduler service is running. Press Ctrl+C to stop.")
        logger.info("=" * 60)
        
        # Keep the service running
        try:
            while scheduler.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
    except Exception as e:
        logger.error(f"Fatal error in scheduler service: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Scheduler service stopped")


if __name__ == "__main__":
    main()
