"""
Company Profile Page - Company research and fit analysis
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Optional, List

from agents.company_profiler import CompanyProfiler
from database.repositories.company_repository import CompanyRepository
from database.repositories.job_repository import JobRepository
from database.repositories.user_repository import UserRepository
from utils.llm_client import OllamaClient
from models.company import CompanyProfile

logger = logging.getLogger(__name__)


def get_unique_companies(db_manager) -> List[str]:
    """
    Get list of unique company names from job listings
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        List of unique company names
    """
    try:
        job_repo = JobRepository(db_manager)
        jobs = job_repo.find_all()
        
        # Extract unique company names
        companies = sorted(set(job.company for job in jobs if job.company))
        return companies
    except Exception as e:
        logger.error(f"Failed to get unique companies: {e}")
        return []


def initialize_company_profiler(db_manager) -> CompanyProfiler:
    """
    Initialize company profiler agent
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        CompanyProfiler instance
    """
    try:
        company_repo = CompanyRepository(db_manager)
        
        # Get LLM configuration from session state
        config = st.session_state.get('config', {})
        llm_config = config.get('llm', {})
        model_name = llm_config.get('model', 'llama3')
        
        llm_client = OllamaClient(model_name=model_name)
        
        return CompanyProfiler(
            company_repository=company_repo,
            llm_client=llm_client
        )
    except Exception as e:
        logger.error(f"Failed to initialize company profiler: {e}")
        st.error(f"Failed to initialize company profiler: {str(e)}")
        return None


def get_user_preferences(db_manager, user_id: str) -> dict:
    """
    Get user preferences for fit analysis
    
    Args:
        db_manager: Database manager instance
        user_id: User ID
        
    Returns:
        Dictionary with user preferences
    """
    try:
        user_repo = UserRepository(db_manager)
        user = user_repo.find_by_id(user_id)
        
        if user:
            return {
                'skills': user.skills,
                'experience_years': user.experience_years,
                'target_salary': user.target_salary,
                'preferred_locations': user.preferred_locations,
                'preferred_remote': user.preferred_remote,
                'desired_tech_stack': user.desired_tech_stack
            }
        else:
            return {
                'skills': [],
                'experience_years': 0,
                'target_salary': 0,
                'preferred_locations': [],
                'preferred_remote': False,
                'desired_tech_stack': []
            }
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        return {}


def render_company_input_section(companies: List[str]) -> Optional[str]:
    """
    Render company input section with dropdown and text input
    
    Args:
        companies: List of company names from job listings
        
    Returns:
        Selected company name or None
    """
    st.subheader("🔍 Select or Enter Company")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        input_method = st.radio(
            "Input Method",
            ["Select from job listings", "Enter manually"],
            horizontal=True
        )
    
    company_name = None
    
    if input_method == "Select from job listings":
        if companies:
            company_name = st.selectbox(
                "Select Company",
                options=[""] + companies,
                index=0
            )
        else:
            st.info("No companies found in job listings. Please run a job search first or enter manually.")
    else:
        company_name = st.text_input(
            "Enter Company Name",
            placeholder="e.g., Google, Microsoft, OpenAI"
        )
    
    return company_name if company_name else None


def render_company_info_section(profile: CompanyProfile):
    """
    Render company information section
    
    Args:
        profile: CompanyProfile instance
    """
    st.subheader("🏢 Company Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if profile.glassdoor_rating:
            st.metric(
                "Glassdoor Rating",
                f"{profile.glassdoor_rating:.1f}/5.0",
                delta=None
            )
        else:
            st.metric("Glassdoor Rating", "N/A")
    
    with col2:
        if profile.employee_count:
            st.metric("Employee Count", f"{profile.employee_count:,}")
        else:
            st.metric("Employee Count", "N/A")
    
    with col3:
        if profile.funding_stage:
            st.metric("Funding Stage", profile.funding_stage)
        else:
            st.metric("Funding Stage", "N/A")


def render_genai_focus_section(profile: CompanyProfile):
    """
    Render GenAI focus score section with explanation
    
    Args:
        profile: CompanyProfile instance
    """
    st.subheader("🤖 GenAI Focus Score")
    
    score = profile.genai_focus_score
    
    # Determine color based on score
    if score >= 7:
        color = "green"
        assessment = "High Focus"
    elif score >= 4:
        color = "orange"
        assessment = "Moderate Focus"
    else:
        color = "red"
        assessment = "Low Focus"
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric("Score", f"{score:.1f}/10")
        st.markdown(f"**Assessment:** :{color}[{assessment}]")
    
    with col2:
        st.markdown("**What this means:**")
        if score >= 7:
            st.success(
                "This company shows strong commitment to GenAI and AI technologies. "
                "Recent news and activities indicate active investment in AI initiatives."
            )
        elif score >= 4:
            st.warning(
                "This company has moderate involvement in GenAI. "
                "They may have some AI projects but it's not their primary focus."
            )
        else:
            st.info(
                "Limited information about GenAI focus. "
                "This could mean the company is not heavily invested in AI, or data is unavailable."
            )


def render_recent_news_section(profile: CompanyProfile):
    """
    Render recent news articles section
    
    Args:
        profile: CompanyProfile instance
    """
    st.subheader("📰 Recent News")
    
    if profile.recent_news:
        for i, news_item in enumerate(profile.recent_news, 1):
            with st.container():
                st.markdown(f"**{i}.** {news_item}")
                st.markdown("---")
    else:
        st.info("No recent news articles found for this company.")


def render_fit_analysis_section(profile: CompanyProfile, profiler: CompanyProfiler, user_preferences: dict):
    """
    Render LLM-generated fit analysis section
    
    Args:
        profile: CompanyProfile instance
        profiler: CompanyProfiler instance
        user_preferences: User preferences dictionary
    """
    st.subheader("🎯 Company-Candidate Fit Analysis")
    
    if profile.culture_summary:
        st.markdown(profile.culture_summary)
    else:
        # Generate fit analysis if not available
        if st.button("Generate Fit Analysis", type="primary"):
            with st.spinner("Analyzing company fit using LLM..."):
                try:
                    summary = profiler.summarize_fit(profile, user_preferences)
                    st.markdown(summary)
                    st.success("Fit analysis generated successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Failed to generate fit analysis: {e}")
                    st.error(f"Failed to generate fit analysis: {str(e)}")


def render_cache_info(profile: CompanyProfile):
    """
    Render cache information
    
    Args:
        profile: CompanyProfile instance
    """
    with st.expander("ℹ️ Cache Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Cached At:** {profile.cached_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            st.write(f"**Expires At:** {profile.cache_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if profile.is_cache_valid():
            days_remaining = (profile.cache_expiry - datetime.now()).days
            st.success(f"✅ Cache is valid ({days_remaining} days remaining)")
        else:
            st.warning("⚠️ Cache has expired. Click 'Refresh Profile' to update.")


def render_company_profile():
    """Main company profile rendering function"""
    st.title("🏢 Company Profiler")
    st.markdown("Research companies and assess your fit with potential employers")
    st.markdown("---")
    
    try:
        # Initialize components
        db_manager = st.session_state.db_manager
        user_id = st.session_state.user_id
        
        # Get unique companies from job listings
        companies = get_unique_companies(db_manager)
        
        # Initialize company profiler
        profiler = initialize_company_profiler(db_manager)
        
        if not profiler:
            st.error("Failed to initialize company profiler. Please check your configuration.")
            return
        
        # Render company input section
        company_name = render_company_input_section(companies)
        
        if not company_name:
            st.info("👆 Please select or enter a company name to view its profile")
            return
        
        # Add action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            profile_button = st.button("🔍 View Profile", type="primary", use_container_width=True)
        
        with col2:
            refresh_button = st.button("🔄 Refresh Profile", use_container_width=True)
        
        with col3:
            # Placeholder for future actions
            pass
        
        # Handle profile viewing
        if profile_button or refresh_button:
            force_refresh = refresh_button
            
            with st.spinner(f"{'Refreshing' if force_refresh else 'Loading'} profile for {company_name}..."):
                try:
                    profile = profiler.profile_company(company_name, force_refresh=force_refresh)
                    
                    if profile:
                        # Store in session state
                        st.session_state.current_company_profile = profile
                        st.success(f"Profile loaded successfully for {company_name}!")
                    else:
                        st.error(f"Failed to load profile for {company_name}. Please try again.")
                        return
                        
                except Exception as e:
                    logger.error(f"Failed to profile company: {e}")
                    st.error(f"Failed to profile company: {str(e)}")
                    return
        
        # Display profile if available in session state
        if 'current_company_profile' in st.session_state:
            profile = st.session_state.current_company_profile
            
            # Check if the profile matches the selected company
            if profile.company_name == company_name:
                st.markdown("---")
                
                # Render company information
                render_company_info_section(profile)
                st.markdown("---")
                
                # Render GenAI focus score
                render_genai_focus_section(profile)
                st.markdown("---")
                
                # Render recent news
                render_recent_news_section(profile)
                st.markdown("---")
                
                # Render fit analysis
                user_preferences = get_user_preferences(db_manager, user_id)
                render_fit_analysis_section(profile, profiler, user_preferences)
                st.markdown("---")
                
                # Render cache information
                render_cache_info(profile)
            else:
                st.info(f"Click 'View Profile' to load information for {company_name}")
        
    except Exception as e:
        logger.error(f"Company profile page error: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check the logs for more details.")
