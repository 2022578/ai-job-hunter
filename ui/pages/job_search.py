"""
Job Search Page - Job discovery interface with filtering, sorting, and actions
"""

import streamlit as st
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from database.repositories.job_repository import JobRepository
from database.repositories.application_repository import ApplicationRepository
from database.repositories.company_repository import CompanyRepository
from agents.job_search_agent import JobSearchAgent, SearchCriteria
from agents.match_scorer import MatchScorer
from agents.company_profiler import CompanyProfiler
from agents.cover_letter_generator import CoverLetterGenerator
from models.job import JobListing
from models.application import Application
from models.user import UserProfile
from utils.llm_client import OllamaClient

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables for job search page"""
    if 'job_search_results' not in st.session_state:
        st.session_state.job_search_results = []
    
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    if 'jobs_per_page' not in st.session_state:
        st.session_state.jobs_per_page = 10


def render_search_form():
    """Render manual search form with filters"""
    st.subheader("🔍 Search for Jobs")
    
    with st.form("job_search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input(
                "Keywords",
                value="GenAI, LLM, LangChain",
                help="Comma-separated keywords to search for"
            )
            
            min_salary = st.number_input(
                "Minimum Salary (Lakhs)",
                min_value=0,
                max_value=200,
                value=35,
                step=5,
                help="Minimum salary in lakhs per annum"
            )
        
        with col2:
            location = st.text_input(
                "Location (Optional)",
                value="",
                help="Leave empty for all locations"
            )
            
            max_pages = st.number_input(
                "Max Pages to Scrape",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                help="Number of pages to scrape from job sites"
            )
        
        submitted = st.form_submit_button("🔍 Search Jobs", use_container_width=True)
        
        if submitted:
            perform_job_search(keywords, min_salary, location, max_pages)


def perform_job_search(keywords_str: str, min_salary: int, location: str, max_pages: int):
    """
    Execute job search with given criteria
    
    Args:
        keywords_str: Comma-separated keywords
        min_salary: Minimum salary in lakhs
        location: Location filter
        max_pages: Maximum pages to scrape
    """
    try:
        # Parse keywords
        keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        if not keywords:
            st.error("Please provide at least one keyword")
            return
        
        # Create search criteria
        criteria = SearchCriteria(
            keywords=keywords,
            min_salary_lakhs=min_salary,
            location=location if location else None,
            max_pages=max_pages
        )
        
        # Initialize job search agent
        job_repo = JobRepository(st.session_state.db_manager)
        job_search_agent = JobSearchAgent(job_repo)
        
        # Perform search
        with st.spinner("Searching for jobs... This may take a few minutes."):
            new_jobs = job_search_agent.search(criteria)
        
        if new_jobs:
            st.success(f"✅ Found {len(new_jobs)} new jobs!")
            st.session_state.search_performed = True
            # Reload all jobs to display
            load_all_jobs()
        else:
            st.info("No new jobs found matching your criteria")
            
    except Exception as e:
        logger.error(f"Job search failed: {e}", exc_info=True)
        st.error(f"Job search failed: {str(e)}")


def load_all_jobs():
    """Load all jobs from database"""
    try:
        job_repo = JobRepository(st.session_state.db_manager)
        all_jobs = job_repo.find_all()
        st.session_state.job_search_results = all_jobs
    except Exception as e:
        logger.error(f"Failed to load jobs: {e}")
        st.session_state.job_search_results = []


def render_filter_and_sort():
    """Render filter and sort controls"""
    st.subheader("🎯 Filter & Sort")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_by = st.selectbox(
            "Sort By",
            options=["Match Score", "Salary", "Posted Date", "Company"],
            index=0
        )
    
    with col2:
        remote_filter = st.selectbox(
            "Remote Type",
            options=["All", "Remote", "Hybrid", "Onsite"],
            index=0
        )
    
    with col3:
        min_match_score = st.slider(
            "Min Match Score",
            min_value=0,
            max_value=100,
            value=0,
            step=10
        )
    
    return sort_by, remote_filter, min_match_score


def filter_and_sort_jobs(
    jobs: List[JobListing],
    sort_by: str,
    remote_filter: str,
    min_match_score: int
) -> List[JobListing]:
    """
    Filter and sort jobs based on criteria
    
    Args:
        jobs: List of jobs to filter and sort
        sort_by: Sort criterion
        remote_filter: Remote type filter
        min_match_score: Minimum match score filter
        
    Returns:
        Filtered and sorted list of jobs
    """
    # Filter by remote type
    if remote_filter != "All":
        jobs = [job for job in jobs if job.remote_type.lower() == remote_filter.lower()]
    
    # Filter by match score
    jobs = [job for job in jobs if job.match_score is None or job.match_score >= min_match_score]
    
    # Sort jobs
    if sort_by == "Match Score":
        jobs = sorted(jobs, key=lambda x: x.match_score if x.match_score else 0, reverse=True)
    elif sort_by == "Salary":
        jobs = sorted(jobs, key=lambda x: x.salary_max if x.salary_max else x.salary_min if x.salary_min else 0, reverse=True)
    elif sort_by == "Posted Date":
        jobs = sorted(jobs, key=lambda x: x.posted_date if x.posted_date else datetime.min, reverse=True)
    elif sort_by == "Company":
        jobs = sorted(jobs, key=lambda x: x.company)
    
    return jobs


def render_job_card(job: JobListing, app_repo: ApplicationRepository):
    """
    Render a job listing card
    
    Args:
        job: JobListing to render
        app_repo: Application repository for checking application status
    """
    with st.container():
        # Check if already applied
        user_apps = app_repo.find_by_user(st.session_state.user_id)
        applied_job_ids = {app.job_id for app in user_apps}
        is_applied = job.id in applied_job_ids
        
        # Card header with title and company
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {job.title}")
            st.markdown(f"**{job.company}** • {job.location}")
        
        with col2:
            # Match score badge
            if job.match_score is not None:
                score_color = "green" if job.match_score >= 80 else "orange" if job.match_score >= 60 else "red"
                st.markdown(f"<div style='text-align: right;'><span style='background-color: {score_color}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;'>{job.match_score:.0f}%</span></div>", unsafe_allow_html=True)
            
            if is_applied:
                st.markdown("<div style='text-align: right; color: green;'>✓ Applied</div>", unsafe_allow_html=True)
        
        # Job details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            salary_text = "Not Disclosed"
            if job.salary_min and job.salary_max:
                salary_text = f"₹{job.salary_min}-{job.salary_max}L"
            elif job.salary_min:
                salary_text = f"₹{job.salary_min}L+"
            st.markdown(f"💰 **Salary:** {salary_text}")
        
        with col2:
            remote_icon = "🏠" if job.remote_type == "remote" else "🏢" if job.remote_type == "onsite" else "🔄"
            st.markdown(f"{remote_icon} **Type:** {job.remote_type.capitalize()}")
        
        with col3:
            posted_text = "Unknown"
            if job.posted_date:
                days_ago = (datetime.now() - job.posted_date).days
                if days_ago == 0:
                    posted_text = "Today"
                elif days_ago == 1:
                    posted_text = "Yesterday"
                else:
                    posted_text = f"{days_ago} days ago"
            st.markdown(f"📅 **Posted:** {posted_text}")
        
        # Skills
        if job.required_skills:
            skills_display = ", ".join(job.required_skills[:5])
            if len(job.required_skills) > 5:
                skills_display += f" +{len(job.required_skills) - 5} more"
            st.markdown(f"🔧 **Skills:** {skills_display}")
        
        # Description preview
        description_preview = job.description[:200] + "..." if len(job.description) > 200 else job.description
        st.markdown(f"📄 {description_preview}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ View Details", key=f"view_{job.id}", use_container_width=True):
                st.session_state.selected_job_id = job.id
                st.rerun()
        
        with col2:
            if not is_applied:
                if st.button("💾 Save", key=f"save_{job.id}", use_container_width=True):
                    save_job(job.id, app_repo)
            else:
                st.button("✓ Saved", key=f"saved_{job.id}", use_container_width=True, disabled=True)
        
        with col3:
            if st.button("📝 Apply", key=f"apply_{job.id}", use_container_width=True):
                mark_as_applied(job.id, app_repo)
        
        with col4:
            if st.button("🏢 Company", key=f"company_{job.id}", use_container_width=True):
                view_company_profile(job.company)
        
        st.markdown("---")


def render_job_listings(jobs: List[JobListing]):
    """
    Render paginated job listings
    
    Args:
        jobs: List of jobs to display
    """
    if not jobs:
        st.info("No jobs found. Try adjusting your filters or run a new search.")
        return
    
    # Pagination
    total_jobs = len(jobs)
    total_pages = (total_jobs + st.session_state.jobs_per_page - 1) // st.session_state.jobs_per_page
    
    # Page controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.current_page <= 1):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col2:
        st.markdown(f"<div style='text-align: center;'>Page {st.session_state.current_page} of {total_pages} ({total_jobs} jobs)</div>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ➡️", disabled=st.session_state.current_page >= total_pages):
            st.session_state.current_page += 1
            st.rerun()
    
    st.markdown("---")
    
    # Calculate pagination
    start_idx = (st.session_state.current_page - 1) * st.session_state.jobs_per_page
    end_idx = min(start_idx + st.session_state.jobs_per_page, total_jobs)
    
    # Display jobs for current page
    app_repo = ApplicationRepository(st.session_state.db_manager)
    
    for job in jobs[start_idx:end_idx]:
        render_job_card(job, app_repo)


def render_job_detail_view(job_id: str):
    """
    Render detailed view of a single job
    
    Args:
        job_id: ID of job to display
    """
    try:
        job_repo = JobRepository(st.session_state.db_manager)
        job = job_repo.find_by_id(job_id)
        
        if not job:
            st.error("Job not found")
            return
        
        # Back button
        if st.button("⬅️ Back to Listings"):
            st.session_state.selected_job_id = None
            st.rerun()
        
        st.markdown("---")
        
        # Job header
        st.title(job.title)
        st.subheader(f"at {job.company}")
        
        # Key details
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            salary_text = "Not Disclosed"
            if job.salary_min and job.salary_max:
                salary_text = f"₹{job.salary_min}-{job.salary_max}L"
            elif job.salary_min:
                salary_text = f"₹{job.salary_min}L+"
            st.metric("Salary", salary_text)
        
        with col2:
            st.metric("Location", job.location if job.location else "Not specified")
        
        with col3:
            st.metric("Remote Type", job.remote_type.capitalize())
        
        with col4:
            if job.match_score is not None:
                st.metric("Match Score", f"{job.match_score:.0f}%")
            else:
                st.metric("Match Score", "N/A")
        
        st.markdown("---")
        
        # Full description
        st.subheader("📄 Job Description")
        st.markdown(job.description)
        
        st.markdown("---")
        
        # Required skills
        if job.required_skills:
            st.subheader("🔧 Required Skills")
            # Display skills as tags
            skills_html = " ".join([f"<span style='background-color: #e0e0e0; padding: 5px 10px; margin: 5px; border-radius: 5px; display: inline-block;'>{skill}</span>" for skill in job.required_skills])
            st.markdown(skills_html, unsafe_allow_html=True)
            st.markdown("---")
        
        # Company profile section
        st.subheader("🏢 Company Profile")
        render_company_profile_section(job.company)
        
        st.markdown("---")
        
        # Action buttons
        st.subheader("⚡ Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        app_repo = ApplicationRepository(st.session_state.db_manager)
        
        with col1:
            if st.button("💾 Save Job", use_container_width=True):
                save_job(job.id, app_repo)
        
        with col2:
            if st.button("📝 Mark as Applied", use_container_width=True):
                mark_as_applied(job.id, app_repo)
        
        with col3:
            if st.button("✉️ Generate Cover Letter", use_container_width=True):
                generate_cover_letter_for_job(job)
        
        with col4:
            if st.button("🔗 Open Job Link", use_container_width=True):
                st.markdown(f"[Open in new tab]({job.source_url})")
        
    except Exception as e:
        logger.error(f"Failed to render job detail: {e}", exc_info=True)
        st.error(f"Failed to load job details: {str(e)}")


def render_company_profile_section(company_name: str):
    """
    Render company profile section
    
    Args:
        company_name: Name of the company
    """
    try:
        company_repo = CompanyRepository(st.session_state.db_manager)
        
        # Check if profile exists in cache
        cached_profile = company_repo.get_cached(company_name)
        
        if cached_profile:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if cached_profile.glassdoor_rating:
                    st.metric("Glassdoor Rating", f"{cached_profile.glassdoor_rating:.1f}/5.0")
                else:
                    st.metric("Glassdoor Rating", "N/A")
            
            with col2:
                if cached_profile.employee_count:
                    st.metric("Employees", f"{cached_profile.employee_count:,}")
                else:
                    st.metric("Employees", "N/A")
            
            with col3:
                st.metric("GenAI Focus", f"{cached_profile.genai_focus_score:.1f}/10")
            
            if cached_profile.culture_summary:
                st.markdown("**Company Summary:**")
                st.info(cached_profile.culture_summary)
            
            if cached_profile.recent_news:
                with st.expander("📰 Recent News"):
                    for news in cached_profile.recent_news[:5]:
                        st.markdown(f"• {news}")
        else:
            st.info(f"No profile available for {company_name}. Click 'Profile Company' to generate one.")
            
            if st.button("🔍 Profile Company", key=f"profile_{company_name}"):
                profile_company(company_name)
                
    except Exception as e:
        logger.error(f"Failed to render company profile: {e}")
        st.warning("Unable to load company profile")


def save_job(job_id: str, app_repo: ApplicationRepository):
    """
    Save job for later
    
    Args:
        job_id: ID of job to save
        app_repo: Application repository
    """
    try:
        application = Application(
            job_id=job_id,
            user_id=st.session_state.user_id,
            status="saved"
        )
        
        if app_repo.save(application):
            st.success("✅ Job saved!")
            st.rerun()
        else:
            st.error("Failed to save job")
            
    except Exception as e:
        logger.error(f"Failed to save job: {e}")
        st.error(f"Failed to save job: {str(e)}")


def mark_as_applied(job_id: str, app_repo: ApplicationRepository):
    """
    Mark job as applied
    
    Args:
        job_id: ID of job to mark as applied
        app_repo: Application repository
    """
    try:
        application = Application(
            job_id=job_id,
            user_id=st.session_state.user_id,
            status="applied",
            applied_date=datetime.now()
        )
        
        if app_repo.save(application):
            st.success("✅ Marked as applied!")
            st.rerun()
        else:
            st.error("Failed to mark as applied")
            
    except Exception as e:
        logger.error(f"Failed to mark as applied: {e}")
        st.error(f"Failed to mark as applied: {str(e)}")


def generate_cover_letter_for_job(job: JobListing):
    """
    Generate cover letter for a job
    
    Args:
        job: JobListing to generate cover letter for
    """
    st.info("Cover letter generation coming soon! This will be implemented in task 20.")


def view_company_profile(company_name: str):
    """
    View detailed company profile
    
    Args:
        company_name: Name of company to profile
    """
    st.info(f"Detailed company profile for {company_name} coming soon! This will be implemented in task 22.")


def profile_company(company_name: str):
    """
    Profile a company
    
    Args:
        company_name: Name of company to profile
    """
    try:
        with st.spinner(f"Profiling {company_name}... This may take a minute."):
            company_repo = CompanyRepository(st.session_state.db_manager)
            llm_client = OllamaClient()
            
            profiler = CompanyProfiler(
                company_repository=company_repo,
                llm_client=llm_client
            )
            
            profile = profiler.profile_company(company_name)
            
            if profile:
                st.success(f"✅ Successfully profiled {company_name}!")
                st.rerun()
            else:
                st.error("Failed to profile company")
                
    except Exception as e:
        logger.error(f"Failed to profile company: {e}")
        st.error(f"Failed to profile company: {str(e)}")


def render_job_search():
    """Main job search page rendering function"""
    st.title("🔍 Job Search")
    st.markdown("Search for GenAI and LLM jobs, filter by your preferences, and take action!")
    st.markdown("---")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Load jobs if not already loaded
        if not st.session_state.job_search_results:
            load_all_jobs()
        
        # Check if viewing job detail
        if st.session_state.selected_job_id:
            render_job_detail_view(st.session_state.selected_job_id)
            return
        
        # Render search form
        render_search_form()
        
        st.markdown("---")
        
        # Show job count
        total_jobs = len(st.session_state.job_search_results)
        st.markdown(f"### 📊 {total_jobs} Jobs Available")
        
        if total_jobs > 0:
            # Render filter and sort controls
            sort_by, remote_filter, min_match_score = render_filter_and_sort()
            
            st.markdown("---")
            
            # Filter and sort jobs
            filtered_jobs = filter_and_sort_jobs(
                st.session_state.job_search_results,
                sort_by,
                remote_filter,
                min_match_score
            )
            
            # Render job listings
            render_job_listings(filtered_jobs)
        else:
            st.info("No jobs in database. Use the search form above to find jobs!")
        
    except Exception as e:
        logger.error(f"Job search page error: {e}", exc_info=True)
        st.error(f"Failed to load job search page: {str(e)}")
