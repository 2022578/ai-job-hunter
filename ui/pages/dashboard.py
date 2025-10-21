"""
Dashboard Page - Overview metrics and actionable insights
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from database.repositories.job_repository import JobRepository
from database.repositories.application_repository import ApplicationRepository

logger = logging.getLogger(__name__)


def get_dashboard_data(user_id: str, db_manager) -> Dict[str, Any]:
    """
    Fetch all data needed for dashboard
    
    Args:
        user_id: User ID to fetch data for
        db_manager: Database manager instance
        
    Returns:
        Dictionary containing dashboard data
    """
    try:
        job_repo = JobRepository(db_manager)
        app_repo = ApplicationRepository(db_manager)
        
        # Get all jobs
        all_jobs = job_repo.find_all()
        
        # Get application statistics
        app_stats = app_repo.get_statistics(user_id)
        
        # Get recent jobs (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_jobs = [job for job in all_jobs if job.created_at >= recent_cutoff]
        
        # Get applications by status
        applications = app_repo.find_by_user(user_id)
        
        # Get upcoming interviews
        upcoming_interviews = [
            app for app in applications 
            if app.interview_date and app.interview_date >= datetime.now()
        ]
        upcoming_interviews.sort(key=lambda x: x.interview_date)
        
        # Calculate match score distribution
        jobs_with_scores = [job for job in all_jobs if job.match_score is not None]
        
        return {
            'total_jobs': len(all_jobs),
            'recent_jobs': len(recent_jobs),
            'app_stats': app_stats,
            'applications': applications,
            'upcoming_interviews': upcoming_interviews,
            'jobs_with_scores': jobs_with_scores,
            'all_jobs': all_jobs
        }
    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        return {
            'total_jobs': 0,
            'recent_jobs': 0,
            'app_stats': {'total': 0, 'by_status': {}, 'interview_rate': 0, 'offer_rate': 0},
            'applications': [],
            'upcoming_interviews': [],
            'jobs_with_scores': [],
            'all_jobs': []
        }


def render_overview_metrics(data: Dict[str, Any]):
    """Render overview metrics cards"""
    st.subheader("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Jobs Found",
            value=data['total_jobs'],
            delta=f"+{data['recent_jobs']} this week" if data['recent_jobs'] > 0 else None
        )
    
    with col2:
        st.metric(
            label="Applications Submitted",
            value=data['app_stats']['total']
        )
    
    with col3:
        interviews_count = data['app_stats']['by_status'].get('interview', 0)
        st.metric(
            label="Interviews Scheduled",
            value=interviews_count
        )
    
    with col4:
        avg_score = 0
        if data['jobs_with_scores']:
            avg_score = sum(job.match_score for job in data['jobs_with_scores']) / len(data['jobs_with_scores'])
        st.metric(
            label="Avg Match Score",
            value=f"{avg_score:.1f}%"
        )


def render_application_funnel(data: Dict[str, Any]):
    """Render application funnel visualization"""
    st.subheader("📈 Application Funnel")
    
    by_status = data['app_stats']['by_status']
    
    # Create funnel data
    funnel_data = {
        'Stage': ['Saved', 'Applied', 'Interview', 'Offered'],
        'Count': [
            by_status.get('saved', 0),
            by_status.get('applied', 0),
            by_status.get('interview', 0),
            by_status.get('offered', 0)
        ]
    }
    
    df = pd.DataFrame(funnel_data)
    
    if df['Count'].sum() > 0:
        st.bar_chart(df.set_index('Stage'))
        
        # Show conversion rates
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Interview Rate", f"{data['app_stats']['interview_rate']}%")
        with col2:
            st.metric("Offer Rate", f"{data['app_stats']['offer_rate']}%")
    else:
        st.info("No application data yet. Start applying to jobs to see your funnel!")


def render_match_score_distribution(data: Dict[str, Any]):
    """Render match score distribution chart"""
    st.subheader("🎯 Match Score Distribution")
    
    if not data['jobs_with_scores']:
        st.info("No jobs with match scores yet. Run the match scorer to see distribution!")
        return
    
    # Create score buckets
    score_buckets = {
        '90-100': 0,
        '80-89': 0,
        '70-79': 0,
        '60-69': 0,
        'Below 60': 0
    }
    
    for job in data['jobs_with_scores']:
        score = job.match_score
        if score >= 90:
            score_buckets['90-100'] += 1
        elif score >= 80:
            score_buckets['80-89'] += 1
        elif score >= 70:
            score_buckets['70-79'] += 1
        elif score >= 60:
            score_buckets['60-69'] += 1
        else:
            score_buckets['Below 60'] += 1
    
    df = pd.DataFrame({
        'Score Range': list(score_buckets.keys()),
        'Count': list(score_buckets.values())
    })
    
    st.bar_chart(df.set_index('Score Range'))


def render_timeline(data: Dict[str, Any]):
    """Render application timeline"""
    st.subheader("📅 Application Timeline")
    
    applications = data['applications']
    
    if not applications:
        st.info("No applications yet. Start applying to jobs to see your timeline!")
        return
    
    # Group applications by date
    timeline_data = {}
    for app in applications:
        date_key = app.created_at.date()
        if date_key not in timeline_data:
            timeline_data[date_key] = 0
        timeline_data[date_key] += 1
    
    # Sort by date
    sorted_dates = sorted(timeline_data.keys())
    
    df = pd.DataFrame({
        'Date': sorted_dates,
        'Applications': [timeline_data[date] for date in sorted_dates]
    })
    
    st.line_chart(df.set_index('Date'))


def render_top_companies(data: Dict[str, Any]):
    """Render top companies by job count"""
    st.subheader("🏢 Top Companies")
    
    if not data['all_jobs']:
        st.info("No jobs found yet. Run a job search to see top companies!")
        return
    
    # Count jobs by company
    company_counts = {}
    for job in data['all_jobs']:
        company = job.company
        if company not in company_counts:
            company_counts[company] = 0
        company_counts[company] += 1
    
    # Sort and get top 10
    sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if sorted_companies:
        df = pd.DataFrame(sorted_companies, columns=['Company', 'Job Count'])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No company data available")


def render_upcoming_interviews(data: Dict[str, Any]):
    """Render upcoming interviews section"""
    st.subheader("📆 Upcoming Interviews")
    
    upcoming = data['upcoming_interviews']
    
    if not upcoming:
        st.info("No upcoming interviews scheduled")
        return
    
    for app in upcoming[:5]:  # Show max 5
        try:
            # Get job details
            job_repo = JobRepository(st.session_state.db_manager)
            job = job_repo.find_by_id(app.job_id)
            
            if job:
                days_until = (app.interview_date - datetime.now()).days
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{job.title}** at {job.company}")
                    with col2:
                        st.write(f"📅 {app.interview_date.strftime('%b %d, %Y %I:%M %p')}")
                    with col3:
                        if days_until == 0:
                            st.write("🔴 Today!")
                        elif days_until == 1:
                            st.write("🟡 Tomorrow")
                        else:
                            st.write(f"🟢 In {days_until} days")
                    st.markdown("---")
        except Exception as e:
            logger.error(f"Failed to render interview: {e}")


def render_actionable_insights(data: Dict[str, Any]):
    """Render daily actionable insights and next steps"""
    st.subheader("💡 Actionable Insights")
    
    insights = []
    
    # Check for high-scoring jobs without applications
    high_score_jobs = [
        job for job in data['jobs_with_scores'] 
        if job.match_score >= 80
    ]
    
    applied_job_ids = {app.job_id for app in data['applications']}
    unapplied_high_score = [
        job for job in high_score_jobs 
        if job.id not in applied_job_ids
    ]
    
    if unapplied_high_score:
        insights.append(f"🎯 You have {len(unapplied_high_score)} high-scoring jobs (80+) that you haven't applied to yet!")
    
    # Check for upcoming interviews
    interviews_this_week = [
        app for app in data['upcoming_interviews']
        if (app.interview_date - datetime.now()).days <= 7
    ]
    
    if interviews_this_week:
        insights.append(f"📆 You have {len(interviews_this_week)} interview(s) this week. Time to prepare!")
    
    # Check for stale applications
    stale_apps = [
        app for app in data['applications']
        if app.status == 'applied' and (datetime.now() - app.created_at).days > 14
    ]
    
    if stale_apps:
        insights.append(f"⏰ You have {len(stale_apps)} applications pending for over 2 weeks. Consider following up!")
    
    # Check for recent jobs
    if data['recent_jobs'] > 0:
        insights.append(f"🆕 {data['recent_jobs']} new jobs found this week. Check them out!")
    
    # Display insights
    if insights:
        for insight in insights:
            st.info(insight)
    else:
        st.success("✅ You're all caught up! Keep up the great work.")


def render_quick_actions():
    """Render quick action buttons"""
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Jobs", use_container_width=True):
            st.session_state.current_page = "Job Search"
            st.rerun()
    
    with col2:
        if st.button("📝 Optimize Resume", use_container_width=True):
            st.info("Resume optimizer coming soon!")
    
    with col3:
        if st.button("💼 Prepare Interview", use_container_width=True):
            st.session_state.current_page = "Interview Prep"
            st.rerun()


def render_dashboard():
    """Main dashboard rendering function"""
    st.title("📊 Dashboard")
    st.markdown("Welcome to your GenAI Job Assistant dashboard!")
    st.markdown("---")
    
    try:
        # Fetch dashboard data
        user_id = st.session_state.user_id
        db_manager = st.session_state.db_manager
        
        with st.spinner("Loading dashboard data..."):
            data = get_dashboard_data(user_id, db_manager)
        
        # Render overview metrics
        render_overview_metrics(data)
        st.markdown("---")
        
        # Render actionable insights
        render_actionable_insights(data)
        st.markdown("---")
        
        # Render quick actions
        render_quick_actions()
        st.markdown("---")
        
        # Two column layout for charts
        col1, col2 = st.columns(2)
        
        with col1:
            render_application_funnel(data)
            st.markdown("---")
            render_timeline(data)
        
        with col2:
            render_match_score_distribution(data)
            st.markdown("---")
            render_top_companies(data)
        
        st.markdown("---")
        
        # Upcoming interviews
        render_upcoming_interviews(data)
        
    except Exception as e:
        logger.error(f"Dashboard rendering error: {e}", exc_info=True)
        st.error(f"Failed to load dashboard: {str(e)}")
        st.error("Please check that the database is initialized and accessible.")
