"""
GenAI Job Assistant - Main Streamlit Application
Entry point for the Streamlit UI with navigation and session state management
"""

import sys
import streamlit as st
import yaml
from pathlib import Path
from datetime import datetime

# Increase recursion limit significantly to handle complex object graphs
# This is needed for Streamlit's internal operations and database queries
sys.setrecursionlimit(10000)

from utils.logger import AgentLogger, LoggerConfig, get_logger, handle_error

# Logger will be initialized in main()
logger = None

# Load configuration with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_config():
    """Load configuration from config.yaml"""
    try:
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {}
    except Exception:
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
        st.session_state.user_id = 'default_user'
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    if 'db_manager' not in st.session_state:
        from database.db_manager import DatabaseManager
        db_path = st.session_state.config.get('database', {}).get('path', 'data/job_assistant.db')
        st.session_state.db_manager = DatabaseManager(db_path)
    
    # Initialize stats cache
    if 'sidebar_stats' not in st.session_state:
        st.session_state.sidebar_stats = None
    if 'stats_last_update' not in st.session_state:
        st.session_state.stats_last_update = datetime.now()

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
        
        # Quick stats in sidebar - cached for performance
        st.subheader("Quick Stats")
        
        # Check if database is initialized
        if 'db_manager' not in st.session_state:
            st.metric("Total Jobs", "—")
            st.metric("Applications", "—")
            st.metric("Interviews", "—")
            return
        
        # Use cached stats to avoid slow queries on every render
        if 'sidebar_stats' not in st.session_state or \
           'stats_last_update' not in st.session_state or \
           (datetime.now() - st.session_state.stats_last_update).seconds > 30:
            try:
                from database.repositories.job_repository import JobRepository
                from database.repositories.application_repository import ApplicationRepository
                
                job_repo = JobRepository(st.session_state.db_manager)
                app_repo = ApplicationRepository(st.session_state.db_manager)
                
                # Cache the stats
                st.session_state.sidebar_stats = {
                    'total_jobs': len(job_repo.find_all()),
                    'app_stats': app_repo.get_statistics(st.session_state.user_id)
                }
                st.session_state.stats_last_update = datetime.now()
            except Exception:
                st.session_state.sidebar_stats = {
                    'total_jobs': 0,
                    'app_stats': {'total': 0, 'by_status': {}}
                }
        
        # Display cached stats
        stats = st.session_state.get('sidebar_stats', {})
        st.metric("Total Jobs", stats.get('total_jobs', 0))
        st.metric("Applications", stats.get('app_stats', {}).get('total', 0))
        st.metric("Interviews", stats.get('app_stats', {}).get('by_status', {}).get('interview', 0))

# Page routing with optimized lazy loading
@st.cache_resource
def get_page_renderer(page_name):
    """Cache page renderers to avoid repeated imports"""
    if page_name == "Dashboard":
        from ui.pages.dashboard import render_dashboard
        return render_dashboard
    elif page_name == "Job Search":
        from ui.pages.job_search import render_job_search
        return render_job_search
    elif page_name == "Applications":
        from ui.pages.applications import render_applications
        return render_applications
    elif page_name == "Resume Optimizer":
        from ui.pages.resume_optimizer import render_resume_optimizer
        return render_resume_optimizer
    elif page_name == "Cover Letter":
        from ui.pages.cover_letter import render_cover_letter
        return render_cover_letter
    elif page_name == "Interview Prep":
        from ui.pages.interview_prep import render_interview_prep
        return render_interview_prep
    elif page_name == "Company Profile":
        from ui.pages.company_profile import render_company_profile
        return render_company_profile
    elif page_name == "Settings":
        from ui.pages.settings import render_settings
        return render_settings
    return None

def route_to_page():
    """Route to the selected page"""
    current_page = st.session_state.current_page
    renderer = get_page_renderer(current_page)
    
    if renderer:
        renderer()
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
