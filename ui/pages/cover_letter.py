"""
Cover Letter Generator Page - Generate personalized cover letters for job applications
"""

import streamlit as st
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from agents.cover_letter_generator import CoverLetterGenerator
from database.repositories.job_repository import JobRepository
from database.repositories.user_repository import UserRepository
from utils.llm_client import OllamaClient
from models.job import JobListing

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize session state variables for cover letter page"""
    if 'selected_job_for_letter' not in st.session_state:
        st.session_state.selected_job_for_letter = None
    
    if 'generated_letter' not in st.session_state:
        st.session_state.generated_letter = ""
    
    if 'selected_tone' not in st.session_state:
        st.session_state.selected_tone = "professional"
    
    if 'letter_edited' not in st.session_state:
        st.session_state.letter_edited = False


def render_job_selection(job_repo: JobRepository):
    """
    Render job selection dropdown
    
    Args:
        job_repo: Job repository instance
    """
    st.subheader("🎯 Select Job")
    
    try:
        # Get all jobs
        jobs = job_repo.find_all()
        
        if not jobs:
            st.warning("No jobs found. Please search for jobs first.")
            st.session_state.selected_job_for_letter = None
            return
        
        # Sort by match score if available
        jobs_sorted = sorted(
            jobs,
            key=lambda x: x.match_score if x.match_score else 0,
            reverse=True
        )
        
        # Create job options
        job_options = ["Select a job..."] + [
            f"{job.title} at {job.company} (Match: {job.match_score:.0f}%)" if job.match_score
            else f"{job.title} at {job.company}"
            for job in jobs_sorted
        ]
        
        selected_option = st.selectbox(
            "Choose the job you want to generate a cover letter for",
            options=job_options,
            help="Select a job to generate a personalized cover letter"
        )
        
        if selected_option == "Select a job...":
            st.session_state.selected_job_for_letter = None
        else:
            # Find the selected job
            selected_index = job_options.index(selected_option) - 1
            st.session_state.selected_job_for_letter = jobs_sorted[selected_index]
            
            # Show job details
            job = jobs_sorted[selected_index]
            with st.expander("📋 Job Details", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Company:** {job.company}")
                    st.markdown(f"**Location:** {job.location}")
                    st.markdown(f"**Remote:** {job.remote_type}")
                
                with col2:
                    if job.salary_min and job.salary_max:
                        st.markdown(f"**Salary:** ₹{job.salary_min}L - ₹{job.salary_max}L")
                    if job.match_score:
                        st.markdown(f"**Match Score:** {job.match_score:.1f}%")
                
                if job.required_skills:
                    st.markdown(f"**Required Skills:** {', '.join(job.required_skills[:10])}")
                
                if job.description:
                    st.markdown("**Description:**")
                    st.text_area(
                        "Job Description",
                        value=job.description[:500] + "..." if len(job.description) > 500 else job.description,
                        height=150,
                        disabled=True,
                        label_visibility="collapsed"
                    )
    
    except Exception as e:
        logger.error(f"Failed to render job selection: {e}")
        st.error("Failed to load jobs")


def render_tone_selection():
    """Render tone selection options"""
    st.subheader("🎨 Select Tone")
    
    tone_descriptions = {
        "professional": "📝 Professional - Formal and business-appropriate",
        "enthusiastic": "🌟 Enthusiastic - Energetic and passionate",
        "technical": "🔧 Technical - Focused on technical skills and expertise"
    }
    
    selected_tone = st.radio(
        "Choose the tone for your cover letter",
        options=list(tone_descriptions.keys()),
        format_func=lambda x: tone_descriptions[x],
        index=list(tone_descriptions.keys()).index(st.session_state.selected_tone),
        help="Select the tone that best matches the company culture and role"
    )
    
    st.session_state.selected_tone = selected_tone


def get_user_resume_summary(user_repo: UserRepository) -> str:
    """
    Get user resume summary
    
    Args:
        user_repo: User repository instance
        
    Returns:
        Resume summary text
    """
    try:
        user = user_repo.find_by_id(st.session_state.user_id)
        
        if user and user.resume_text:
            return user.resume_text
        
        # Fallback: create a basic summary from user profile
        if user:
            summary = f"Professional with {user.experience_years} years of experience.\n"
            if user.skills:
                summary += f"Skills: {', '.join(user.skills)}\n"
            return summary
        
        return "Experienced professional in GenAI and LLM technologies."
    
    except Exception as e:
        logger.error(f"Failed to get user resume: {e}")
        return "Experienced professional in GenAI and LLM technologies."


def render_generate_button(generator: CoverLetterGenerator, user_repo: UserRepository):
    """
    Render generate button and handle generation
    
    Args:
        generator: CoverLetterGenerator instance
        user_repo: User repository instance
    """
    col1, col2 = st.columns(2)
    
    with col1:
        generate_button = st.button(
            "✨ Generate Cover Letter",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.selected_job_for_letter is None
        )
    
    with col2:
        regenerate_button = st.button(
            "🔄 Regenerate",
            use_container_width=True,
            disabled=not st.session_state.generated_letter
        )
    
    # Handle generate button
    if generate_button:
        if not st.session_state.selected_job_for_letter:
            st.error("Please select a job first")
            return
        
        with st.spinner(f"Generating {st.session_state.selected_tone} cover letter..."):
            try:
                job = st.session_state.selected_job_for_letter
                resume_summary = get_user_resume_summary(user_repo)
                
                # Get user projects if available
                user = user_repo.find_by_id(st.session_state.user_id)
                relevant_projects = None
                if user and hasattr(user, 'projects') and user.projects:
                    relevant_projects = [p.name for p in user.projects[:3]]
                
                letter = generator.generate(
                    job=job,
                    resume_summary=resume_summary,
                    user_id=st.session_state.user_id,
                    relevant_projects=relevant_projects,
                    tone=st.session_state.selected_tone
                )
                
                st.session_state.generated_letter = letter
                st.session_state.letter_edited = False
                st.success("✅ Cover letter generated successfully!")
                st.rerun()
            
            except Exception as e:
                logger.error(f"Cover letter generation failed: {e}")
                st.error(f"Generation failed: {str(e)}")
    
    # Handle regenerate button
    if regenerate_button:
        if not st.session_state.selected_job_for_letter:
            st.error("Please select a job first")
            return
        
        with st.spinner(f"Regenerating with {st.session_state.selected_tone} tone..."):
            try:
                job = st.session_state.selected_job_for_letter
                resume_summary = get_user_resume_summary(user_repo)
                
                # Get user projects if available
                user = user_repo.find_by_id(st.session_state.user_id)
                relevant_projects = None
                if user and hasattr(user, 'projects') and user.projects:
                    relevant_projects = [p.name for p in user.projects[:3]]
                
                letter = generator.regenerate_with_tone(
                    job_id=job.id,
                    resume_summary=resume_summary,
                    tone=st.session_state.selected_tone,
                    user_id=st.session_state.user_id,
                    relevant_projects=relevant_projects
                )
                
                st.session_state.generated_letter = letter
                st.session_state.letter_edited = False
                st.success("✅ Cover letter regenerated successfully!")
                st.rerun()
            
            except Exception as e:
                logger.error(f"Cover letter regeneration failed: {e}")
                st.error(f"Regeneration failed: {str(e)}")


def render_cover_letter_display(generator: CoverLetterGenerator):
    """
    Render generated cover letter with editing capability
    
    Args:
        generator: CoverLetterGenerator instance
    """
    if not st.session_state.generated_letter:
        st.info("👆 Select a job and tone, then click 'Generate Cover Letter' to get started!")
        return
    
    st.markdown("---")
    st.subheader("📄 Your Cover Letter")
    
    # Character count
    char_count = len(st.session_state.generated_letter)
    word_count = len(st.session_state.generated_letter.split())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Characters", char_count)
    with col2:
        st.metric("Words", word_count)
    with col3:
        # Estimate reading time (average 200 words per minute)
        reading_time = max(1, word_count // 200)
        st.metric("Reading Time", f"{reading_time} min")
    
    # Editable text area
    edited_letter = st.text_area(
        "Cover Letter Content",
        value=st.session_state.generated_letter,
        height=400,
        help="You can edit the cover letter directly in this text area",
        label_visibility="collapsed"
    )
    
    # Track if letter was edited
    if edited_letter != st.session_state.generated_letter:
        st.session_state.generated_letter = edited_letter
        st.session_state.letter_edited = True
    
    # Show edit indicator
    if st.session_state.letter_edited:
        st.info("✏️ Letter has been edited")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            # Display in a code block for easy copying
            st.code(st.session_state.generated_letter, language=None)
            st.success("✅ Ready to copy! Select the text above and copy it.")
    
    with col2:
        if st.button("💾 Save", use_container_width=True):
            save_cover_letter(generator)
    
    with col3:
        # Download as text file
        download_filename = f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.download_button(
            label="📥 Download",
            data=st.session_state.generated_letter,
            file_name=download_filename,
            mime="text/plain",
            use_container_width=True
        )
    
    with col4:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.generated_letter = ""
            st.session_state.letter_edited = False
            st.rerun()


def save_cover_letter(generator: CoverLetterGenerator):
    """
    Save cover letter to database
    
    Args:
        generator: CoverLetterGenerator instance
    """
    try:
        if not st.session_state.selected_job_for_letter:
            st.error("No job selected")
            return
        
        if not st.session_state.generated_letter:
            st.error("No cover letter to save")
            return
        
        success = generator.save_letter(
            job_id=st.session_state.selected_job_for_letter.id,
            user_id=st.session_state.user_id,
            content=st.session_state.generated_letter,
            tone=st.session_state.selected_tone
        )
        
        if success:
            st.success("✅ Cover letter saved successfully!")
        else:
            st.error("Failed to save cover letter")
    
    except Exception as e:
        logger.error(f"Failed to save cover letter: {e}")
        st.error(f"Failed to save: {str(e)}")


def render_formatting_preview():
    """Render formatting preview section"""
    if not st.session_state.generated_letter:
        return
    
    with st.expander("👁️ Formatting Preview", expanded=False):
        st.markdown("**Preview how your cover letter will look:**")
        st.markdown("---")
        
        # Display with basic formatting
        lines = st.session_state.generated_letter.split('\n')
        for line in lines:
            if line.strip():
                st.markdown(line)
            else:
                st.markdown("")


def render_saved_letters(generator: CoverLetterGenerator):
    """
    Render saved cover letters section
    
    Args:
        generator: CoverLetterGenerator instance
    """
    with st.expander("📚 Saved Cover Letters", expanded=False):
        try:
            saved_letters = generator.get_all_letters(
                user_id=st.session_state.user_id,
                include_expired=False
            )
            
            if not saved_letters:
                st.info("No saved cover letters yet")
                return
            
            st.markdown(f"**{len(saved_letters)} saved letters**")
            
            for letter in saved_letters:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    generated_date = datetime.fromisoformat(letter['generated_at'])
                    st.markdown(f"**Job ID:** {letter['job_id'][:8]}... • **Tone:** {letter['tone']} • **Date:** {generated_date.strftime('%Y-%m-%d')}")
                
                with col2:
                    if st.button("📖 Load", key=f"load_{letter['id']}", use_container_width=True):
                        st.session_state.generated_letter = letter['content']
                        st.session_state.selected_tone = letter['tone']
                        st.session_state.letter_edited = False
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{letter['id']}", use_container_width=True):
                        if generator.delete_letter(letter['id']):
                            st.success("Deleted!")
                            st.rerun()
                
                st.markdown("---")
        
        except Exception as e:
            logger.error(f"Failed to load saved letters: {e}")
            st.error("Failed to load saved letters")


def render_cover_letter():
    """Main cover letter page rendering function"""
    st.title("✉️ Cover Letter Generator")
    st.markdown("Generate personalized, professional cover letters tailored to specific job postings!")
    st.markdown("---")
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Initialize components
        llm_client = OllamaClient(
            model=st.session_state.config.get('llm', {}).get('model', 'llama3'),
            base_url=st.session_state.config.get('llm', {}).get('base_url', 'http://localhost:11434')
        )
        generator = CoverLetterGenerator(llm_client, st.session_state.db_manager)
        job_repo = JobRepository(st.session_state.db_manager)
        user_repo = UserRepository(st.session_state.db_manager)
        
        # Job selection section
        render_job_selection(job_repo)
        
        st.markdown("---")
        
        # Tone selection section
        render_tone_selection()
        
        st.markdown("---")
        
        # Generate button
        render_generate_button(generator, user_repo)
        
        # Display generated cover letter
        render_cover_letter_display(generator)
        
        # Formatting preview
        render_formatting_preview()
        
        st.markdown("---")
        
        # Saved letters
        render_saved_letters(generator)
        
    except Exception as e:
        logger.error(f"Cover letter page error: {e}", exc_info=True)
        st.error(f"Failed to load cover letter page: {str(e)}")

