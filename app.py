"""
GenAI Job Assistant - Main Streamlit Application
Entry point for the Streamlit UI with navigation and session state management
"""

import sys
import streamlit as st
import yaml
from pathlib import Path

# Increase recursion limit significantly to handle complex object graphs
# This is needed for Streamlit's internal operations and database queries
sys.setrecursionlimit(10000)

from utils.logger import AgentLogger, LoggerConfig, get_logger, handle_error

# Logger will be initialized in main()
logger = None

# Load configuration
def load_config():
    """Load configuration from config.yaml"""
    try:
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            if logger:
                logger.warning("Config file not found, using defaults")
            return {}
    except Exception as e:
        error_info = handle_error(
            e,
            category='general',
            error_type='file_not_found',
            context={'file': 'config.yaml'},
            logger_name=__name__
        )
        if logger:
            logger.error(f"Failed to load config: {e}")
        return {}

# Page configuration
def configure_page():
    """Configure Streamlit page settings"""
    config = load_config()
    ui_config = config.get('ui', {})
    
    st.set_page_config(
        page_title=ui_config.get('page_title', 'GenAI Job Assistant'),
        page_icon=ui_config.get('page_icon', '🤖'),
        layout=ui_config.get('layout', 'wide'),
        initial_sidebar_state='expanded'
    )

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
    
    if 'user_id' not in st.session_state:
        # For now, use a default user ID. In production, this would come from authentication
        st.session_state.user_id = 'default_user'
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    if 'db_manager' not in st.session_state:
        # Initialize database manager
        from database.db_manager import DatabaseManager
        db_path = st.session_state.config.get('database', {}).get('path', 'data/job_assistant.db')
        st.session_state.db_manager = DatabaseManager(db_path)

# Navigation sidebar
def render_sidebar():
    """Render navigation sidebar"""
    with st.sidebar:
        st.title("🤖 GenAI Job Assistant")
        st.markdown("---")
        
        # Navigation menu
        pages = {
            "Dashboard": "📊",
            "Job Search": "🔍",
            "Applications": "📝",
            "Resume Optimizer": "📝",
            "Cover Letter": "✉️",
            "Interview Prep": "💼",
            "Company Profile": "🏢",
            "Settings": "⚙️"
        }
        
        st.subheader("Navigation")
        for page_name, icon in pages.items():
            if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats in sidebar
        st.subheader("Quick Stats")
        
        # Check if database is initialized
        if 'db_manager' not in st.session_state:
            st.metric("Total Jobs", "—")
            st.metric("Applications", "—")
            st.metric("Interviews", "—")
            return
        
        try:
            from database.repositories.job_repository import JobRepository
            from database.repositories.application_repository import ApplicationRepository
            
            job_repo = JobRepository(st.session_state.db_manager)
            app_repo = ApplicationRepository(st.session_state.db_manager)
            
            # Use simpler queries to avoid recursion
            total_jobs = len(job_repo.find_all())
            stats = app_repo.get_statistics(st.session_state.user_id)
            
            st.metric("Total Jobs", total_jobs)
            st.metric("Applications", stats.get('total', 0))
            st.metric("Interviews", stats.get('by_status', {}).get('interview', 0))
        except RecursionError:
            # Handle recursion error specifically
            st.metric("Total Jobs", "Error")
            st.metric("Applications", "Error")
            st.metric("Interviews", "Error")
            st.caption("⚠️ Database query error")
        except Exception:
            # Simplified error handling for other errors
            st.metric("Total Jobs", "—")
            st.metric("Applications", "—")
            st.metric("Interviews", "—")

# Page routing
def route_to_page():
    """Route to the selected page"""
    current_page = st.session_state.current_page
    
    if current_page == "Dashboard":
        from ui.pages.dashboard import render_dashboard
        render_dashboard()
    elif current_page == "Job Search":
        from ui.pages.job_search import render_job_search
        render_job_search()
    elif current_page == "Applications":
        from ui.pages.applications import render_applications
        render_applications()
    elif current_page == "Resume Optimizer":
        from ui.pages.resume_optimizer import render_resume_optimizer
        render_resume_optimizer()
    elif current_page == "Cover Letter":
        from ui.pages.cover_letter import render_cover_letter
        render_cover_letter()
    elif current_page == "Interview Prep":
        from ui.pages.interview_prep import render_interview_prep
        render_interview_prep()
    elif current_page == "Company Profile":
        from ui.pages.company_profile import render_company_profile
        render_company_profile()
    elif current_page == "Settings":
        from ui.pages.settings import render_settings
        render_settings()
    else:
        st.error(f"Unknown page: {current_page}")

# Main application
def main():
    """Main application entry point"""
    global logger
    
    # Initialize logging system (only once)
    if logger is None:
        AgentLogger.initialize(
            log_dir='logs',
            log_file='job_assistant.log',
            level=LoggerConfig.INFO,
            console_output=True
        )
        logger = get_logger(__name__)
    
    try:
        # Configure page
        configure_page()
        
        # Initialize session state
        init_session_state()
        
        # Render sidebar navigation
        render_sidebar()
        
        # Route to selected page
        route_to_page()
        
    except RecursionError as e:
        # Handle recursion errors specially to avoid infinite loops
        st.error("⚠️ Application encountered a recursion error. Please refresh the page.")
        st.error("If the problem persists, check your database and model configurations.")
        if logger:
            logger.critical(f"RecursionError in main: {str(e)[:200]}")
    except Exception as e:
        # Simplified error handling to avoid recursion in error handlers
        st.error(f"⚠️ An error occurred: {str(e)[:200]}")
        if logger:
            logger.error(f"Application error: {str(e)[:200]}")

if __name__ == "__main__":
    main()
