"""
Resume Optimizer Page - Resume analysis and optimization interface
"""

import streamlit as st
import logging
from typing import Optional
from pathlib import Path
import io
from datetime import datetime

from agents.resume_optimizer import ResumeOptimizer, ResumeAnalysis, OptimizedResume
from database.repositories.job_repository import JobRepository
from utils.llm_client import OllamaClient
from models.job import JobListing

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables for resume optimizer page"""
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = ""
    
    if 'selected_job_for_optimization' not in st.session_state:
        st.session_state.selected_job_for_optimization = None
    
    if 'optimization_result' not in st.session_state:
        st.session_state.optimization_result = None
    
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None


def read_resume_file(uploaded_file) -> Optional[str]:
    """
    Read resume content from uploaded file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Resume text content or None if failed
    """
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == '.txt':
            # Read plain text
            return uploaded_file.read().decode('utf-8')
        
        elif file_extension == '.pdf':
            # Read PDF
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                st.error("PyPDF2 not installed. Please install it to read PDF files: pip install PyPDF2")
                return None
        
        elif file_extension in ['.docx', '.doc']:
            # Read DOCX
            try:
                import docx
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                st.error("python-docx not installed. Please install it to read DOCX files: pip install python-docx")
                return None
        
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
    
    except Exception as e:
        logger.error(f"Failed to read resume file: {e}")
        st.error(f"Failed to read file: {str(e)}")
        return None


def render_resume_input():
    """Render resume input section with file upload and text area"""
    st.subheader("📄 Your Resume")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=['pdf', 'docx', 'txt'],
        help="Upload your resume in PDF, DOCX, or TXT format"
    )
    
    if uploaded_file is not None:
        with st.spinner("Reading resume..."):
            resume_text = read_resume_file(uploaded_file)
            if resume_text:
                st.session_state.resume_text = resume_text
                st.success(f"✅ Resume loaded: {uploaded_file.name}")
    
    # Manual text input
    st.markdown("**Or paste your resume text:**")
    resume_text_input = st.text_area(
        "Resume Text",
        value=st.session_state.resume_text,
        height=300,
        placeholder="Paste your resume content here...",
        label_visibility="collapsed"
    )
    
    if resume_text_input != st.session_state.resume_text:
        st.session_state.resume_text = resume_text_input


def render_job_selection(job_repo: JobRepository):
    """
    Render job selection dropdown for targeted optimization
    
    Args:
        job_repo: Job repository instance
    """
    st.subheader("🎯 Target Job (Optional)")
    
    try:
        # Get all jobs
        jobs = job_repo.find_all()
        
        if not jobs:
            st.info("No jobs found. Search for jobs first to enable targeted optimization.")
            st.session_state.selected_job_for_optimization = None
            return
        
        # Create job options
        job_options = ["None - General Analysis"] + [
            f"{job.title} at {job.company}" for job in jobs
        ]
        
        selected_option = st.selectbox(
            "Select a job to optimize for",
            options=job_options,
            help="Select a specific job to get targeted optimization suggestions"
        )
        
        if selected_option == "None - General Analysis":
            st.session_state.selected_job_for_optimization = None
        else:
            # Find the selected job
            selected_index = job_options.index(selected_option) - 1
            st.session_state.selected_job_for_optimization = jobs[selected_index]
            
            # Show job details
            job = jobs[selected_index]
            with st.expander("📋 Job Details"):
                st.markdown(f"**Company:** {job.company}")
                st.markdown(f"**Location:** {job.location}")
                if job.salary_min and job.salary_max:
                    st.markdown(f"**Salary:** ₹{job.salary_min}L - ₹{job.salary_max}L")
                st.markdown(f"**Remote:** {job.remote_type}")
                
                if job.required_skills:
                    st.markdown(f"**Required Skills:** {', '.join(job.required_skills)}")
    
    except Exception as e:
        logger.error(f"Failed to render job selection: {e}")
        st.error("Failed to load jobs")


def render_analysis_button(optimizer: ResumeOptimizer):
    """
    Render analyze button and handle analysis
    
    Args:
        optimizer: ResumeOptimizer instance
    """
    col1, col2 = st.columns(2)
    
    with col1:
        analyze_button = st.button(
            "🔍 Analyze Resume",
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if st.session_state.selected_job_for_optimization:
            optimize_button = st.button(
                "🎯 Optimize for Job",
                use_container_width=True,
                type="primary"
            )
        else:
            optimize_button = False
    
    # Handle analyze button
    if analyze_button:
        if not st.session_state.resume_text or not st.session_state.resume_text.strip():
            st.error("Please provide your resume text first")
            return
        
        with st.spinner("Analyzing your resume..."):
            try:
                analysis = optimizer.analyze_resume(
                    st.session_state.resume_text,
                    job_description=None
                )
                st.session_state.analysis_result = analysis
                st.session_state.optimization_result = None
                st.success("✅ Analysis complete!")
                st.rerun()
            except Exception as e:
                logger.error(f"Resume analysis failed: {e}")
                st.error(f"Analysis failed: {str(e)}")
    
    # Handle optimize button
    if optimize_button:
        if not st.session_state.resume_text or not st.session_state.resume_text.strip():
            st.error("Please provide your resume text first")
            return
        
        if not st.session_state.selected_job_for_optimization:
            st.error("Please select a job to optimize for")
            return
        
        with st.spinner("Optimizing your resume for the selected job..."):
            try:
                optimized = optimizer.optimize_for_job(
                    st.session_state.resume_text,
                    st.session_state.selected_job_for_optimization,
                    user_id=st.session_state.user_id
                )
                st.session_state.optimization_result = optimized
                st.session_state.analysis_result = optimized.analysis
                st.success("✅ Optimization complete!")
                st.rerun()
            except Exception as e:
                logger.error(f"Resume optimization failed: {e}")
                st.error(f"Optimization failed: {str(e)}")


def render_analysis_results(analysis: ResumeAnalysis):
    """
    Render analysis results
    
    Args:
        analysis: ResumeAnalysis instance
    """
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    # Overall score
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        score_color = "green" if analysis.overall_score >= 7 else "orange" if analysis.overall_score >= 5 else "red"
        st.markdown(
            f"<div style='text-align: center; padding: 20px; background-color: {score_color}; color: white; border-radius: 10px;'>"
            f"<h1>{analysis.overall_score:.1f}/10</h1>"
            f"<p>Overall Resume Strength</p>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Keyword analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Present Keywords")
        if analysis.present_keywords:
            for keyword in analysis.present_keywords[:10]:
                st.markdown(f"- {keyword}")
            if len(analysis.present_keywords) > 10:
                with st.expander(f"Show {len(analysis.present_keywords) - 10} more..."):
                    for keyword in analysis.present_keywords[10:]:
                        st.markdown(f"- {keyword}")
        else:
            st.info("No keywords identified")
    
    with col2:
        st.markdown("### ❌ Missing Keywords")
        if analysis.missing_keywords:
            for keyword in analysis.missing_keywords[:10]:
                st.markdown(f"- {keyword}")
            if len(analysis.missing_keywords) > 10:
                with st.expander(f"Show {len(analysis.missing_keywords) - 10} more..."):
                    for keyword in analysis.missing_keywords[10:]:
                        st.markdown(f"- {keyword}")
        else:
            st.success("No critical keywords missing!")
    
    # Keyword density score
    if analysis.keyword_density_score > 0:
        st.markdown(f"**Keyword Density Score:** {analysis.keyword_density_score:.1f}/10")
        st.progress(analysis.keyword_density_score / 10)
    
    st.markdown("---")
    
    # Strengths and weaknesses
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💪 Strengths")
        if analysis.strengths:
            for strength in analysis.strengths:
                st.markdown(f"- {strength}")
        else:
            st.info("No specific strengths identified")
    
    with col2:
        st.markdown("### 🔧 Areas for Improvement")
        if analysis.weaknesses:
            for weakness in analysis.weaknesses:
                st.markdown(f"- {weakness}")
        else:
            st.success("No major weaknesses identified!")
    
    # Recommendations
    if analysis.recommendations:
        st.markdown("---")
        st.markdown("### 💡 Recommendations")
        for i, rec in enumerate(analysis.recommendations, 1):
            st.markdown(f"{i}. {rec}")


def render_optimization_results(optimized: OptimizedResume):
    """
    Render optimization results with before/after comparisons
    
    Args:
        optimized: OptimizedResume instance
    """
    st.markdown("---")
    st.subheader("🎯 Optimization Results")
    
    # ATS Keywords
    if optimized.ats_keywords:
        st.markdown("### 🔑 ATS Keywords to Include")
        
        # Display in columns
        num_cols = 3
        cols = st.columns(num_cols)
        for i, keyword in enumerate(optimized.ats_keywords):
            with cols[i % num_cols]:
                st.markdown(f"- {keyword}")
    
    # GenAI Highlights
    if optimized.genai_highlights:
        st.markdown("---")
        st.markdown("### 🤖 GenAI Experience Highlights")
        for i, highlight in enumerate(optimized.genai_highlights, 1):
            st.markdown(f"{i}. {highlight}")
    
    # Before/After Improvements
    if optimized.improvements:
        st.markdown("---")
        st.markdown("### ✏️ Suggested Improvements")
        
        for i, improvement in enumerate(optimized.improvements, 1):
            with st.expander(f"**{i}. {improvement.section_name}**", expanded=(i == 1)):
                st.markdown(f"**Reason:** {improvement.reason}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Before:**")
                    st.text_area(
                        "Before",
                        value=improvement.before,
                        height=150,
                        key=f"before_{i}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown("**After:**")
                    st.text_area(
                        "After",
                        value=improvement.after,
                        height=150,
                        key=f"after_{i}",
                        label_visibility="collapsed"
                    )
                
                # Copy button for optimized version
                if st.button(f"📋 Copy Optimized Version", key=f"copy_{i}", use_container_width=True):
                    st.code(improvement.after, language=None)
                    st.success("✅ Text ready to copy!")


def render_resume_optimizer():
    """Main resume optimizer page rendering function"""
    st.title("📝 Resume Optimizer")
    st.markdown("Analyze and optimize your resume for GenAI/LLM roles with AI-powered suggestions!")
    st.markdown("---")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Initialize components
        llm_client = OllamaClient(
            model=st.session_state.config.get('llm', {}).get('model', 'llama3'),
            base_url=st.session_state.config.get('llm', {}).get('base_url', 'http://localhost:11434')
        )
        optimizer = ResumeOptimizer(llm_client, st.session_state.db_manager)
        job_repo = JobRepository(st.session_state.db_manager)
        
        # Resume input section
        render_resume_input()
        
        st.markdown("---")
        
        # Job selection section
        render_job_selection(job_repo)
        
        st.markdown("---")
        
        # Analysis button
        render_analysis_button(optimizer)
        
        # Display results if available
        if st.session_state.optimization_result:
            render_optimization_results(st.session_state.optimization_result)
        elif st.session_state.analysis_result:
            render_analysis_results(st.session_state.analysis_result)
        
    except Exception as e:
        logger.error(f"Resume optimizer page error: {e}", exc_info=True)
        st.error(f"Failed to load resume optimizer page: {str(e)}")

