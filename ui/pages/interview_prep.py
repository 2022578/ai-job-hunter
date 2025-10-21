"""
Interview Prep Page - Question generation, mock interviews, and custom Q&A management
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from agents.interview_prep_agent import InterviewPrepAgent, Question
from models.question import CustomQuestion
from models.job import JobListing
from database.repositories.job_repository import JobRepository
from database.repositories.question_repository import QuestionRepository
from utils.llm_client import OllamaClient

logger = logging.getLogger(__name__)


def init_interview_prep_state():
    """Initialize session state for interview prep page"""
    if 'interview_questions' not in st.session_state:
        st.session_state.interview_questions = []
    if 'mock_interview_active' not in st.session_state:
        st.session_state.mock_interview_active = False
    if 'mock_interview_index' not in st.session_state:
        st.session_state.mock_interview_index = 0
    if 'mock_interview_answers' not in st.session_state:
        st.session_state.mock_interview_answers = []
    if 'mock_interview_feedback' not in st.session_state:
        st.session_state.mock_interview_feedback = []
    if 'selected_custom_question' not in st.session_state:
        st.session_state.selected_custom_question = None


def get_interview_prep_agent() -> InterviewPrepAgent:
    """Get or create interview prep agent instance"""
    if 'interview_prep_agent' not in st.session_state:
        llm_client = OllamaClient(
            model=st.session_state.config.get('llm', {}).get('model', 'llama3')
        )
        question_repo = QuestionRepository(st.session_state.db_manager)
        st.session_state.interview_prep_agent = InterviewPrepAgent(llm_client, question_repo)
    
    return st.session_state.interview_prep_agent


def render_question_generation():
    """Render interview question generation interface"""
    st.subheader("🎯 Generate Interview Questions")
    
    # Job selection
    job_repo = JobRepository(st.session_state.db_manager)
    all_jobs = job_repo.find_all()
    
    if not all_jobs:
        st.warning("No jobs found. Please search for jobs first.")
        return
    
    # Create job selection dropdown
    job_options = {f"{job.title} at {job.company}": job for job in all_jobs}
    selected_job_name = st.selectbox(
        "Select Job",
        options=list(job_options.keys()),
        key="question_gen_job_select"
    )
    
    selected_job = job_options[selected_job_name]
    
    # Question type selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        question_type = st.selectbox(
            "Question Type",
            options=["Technical", "Behavioral", "Both"],
            key="question_type_select"
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty Level",
            options=["Easy", "Medium", "Hard"],
            key="difficulty_select"
        )
    
    with col3:
        count = st.number_input(
            "Number of Questions",
            min_value=1,
            max_value=20,
            value=10,
            key="question_count"
        )
    
    # Generate button
    if st.button("Generate Questions", type="primary", use_container_width=True):
        with st.spinner("Generating interview questions..."):
            try:
                agent = get_interview_prep_agent()
                
                # Map UI values to agent values
                type_map = {"Technical": "technical", "Behavioral": "behavioral", "Both": "technical"}
                difficulty_map = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}
                
                questions = agent.generate_questions(
                    job=selected_job,
                    question_type=type_map[question_type],
                    difficulty=difficulty_map[difficulty],
                    count=count
                )
                
                # If "Both" selected, generate behavioral questions too
                if question_type == "Both":
                    behavioral_questions = agent.generate_questions(
                        job=selected_job,
                        question_type="behavioral",
                        difficulty=difficulty_map[difficulty],
                        count=count // 2
                    )
                    questions.extend(behavioral_questions)
                
                st.session_state.interview_questions = questions
                st.success(f"Generated {len(questions)} questions!")
                
            except Exception as e:
                logger.error(f"Failed to generate questions: {e}")
                st.error(f"Failed to generate questions: {str(e)}")
    
    # Display generated questions
    if st.session_state.interview_questions:
        st.markdown("---")
        st.subheader("📝 Generated Questions")
        
        for i, question in enumerate(st.session_state.interview_questions, 1):
            with st.expander(f"Q{i}: {question.text[:80]}...", expanded=False):
                st.write(f"**Question:** {question.text}")
                st.write(f"**Category:** {question.category}")
                st.write(f"**Difficulty:** {question.difficulty}")
                if question.topic:
                    st.write(f"**Topic:** {question.topic}")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Mock Interview", use_container_width=True):
                st.session_state.mock_interview_active = True
                st.session_state.mock_interview_index = 0
                st.session_state.mock_interview_answers = []
                st.session_state.mock_interview_feedback = []
                st.rerun()
        
        with col2:
            if st.button("Clear Questions", use_container_width=True):
                st.session_state.interview_questions = []
                st.rerun()


def render_mock_interview():
    """Render mock interview interface"""
    st.subheader("🎤 Mock Interview")
    
    # Check if we have questions to interview with
    if not st.session_state.interview_questions:
        st.info("Please generate questions first in the 'Generate Questions' tab.")
        return
    
    # Check if mock interview is active
    if not st.session_state.mock_interview_active:
        st.write("Ready to start your mock interview?")
        st.write(f"You have {len(st.session_state.interview_questions)} questions prepared.")
        
        if st.button("Start Mock Interview", type="primary", use_container_width=True):
            st.session_state.mock_interview_active = True
            st.session_state.mock_interview_index = 0
            st.session_state.mock_interview_answers = []
            st.session_state.mock_interview_feedback = []
            st.rerun()
        return
    
    # Mock interview in progress
    current_index = st.session_state.mock_interview_index
    total_questions = len(st.session_state.interview_questions)
    
    # Check if interview is complete
    if current_index >= total_questions:
        render_interview_summary()
        return
    
    # Display current question
    current_question = st.session_state.interview_questions[current_index]
    
    # Progress indicator
    st.progress((current_index) / total_questions)
    st.write(f"**Question {current_index + 1} of {total_questions}**")
    
    # Question details
    st.markdown(f"### {current_question.text}")
    st.write(f"**Category:** {current_question.category} | **Difficulty:** {current_question.difficulty}")
    
    # Timer display (visual only, not enforced)
    col1, col2 = st.columns([3, 1])
    with col2:
        st.info("⏱️ Suggested: 5 min")
    
    # Answer input
    answer_key = f"answer_{current_index}"
    user_answer = st.text_area(
        "Your Answer",
        height=200,
        key=answer_key,
        placeholder="Type your answer here..."
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_index == 0)):
            st.session_state.mock_interview_index -= 1
            st.rerun()
    
    with col2:
        if st.button("❌ End Interview"):
            st.session_state.mock_interview_active = False
            st.session_state.mock_interview_index = 0
            st.rerun()
    
    with col3:
        if st.button("Next ➡️", type="primary"):
            if user_answer.strip():
                # Save answer
                if current_index < len(st.session_state.mock_interview_answers):
                    st.session_state.mock_interview_answers[current_index] = user_answer
                else:
                    st.session_state.mock_interview_answers.append(user_answer)
                
                # Move to next question
                st.session_state.mock_interview_index += 1
                st.rerun()
            else:
                st.warning("Please provide an answer before proceeding.")
    
    # Show previous answers if available
    if current_index > 0 and st.session_state.mock_interview_answers:
        with st.expander("📝 View Previous Answers"):
            for i, ans in enumerate(st.session_state.mock_interview_answers[:current_index]):
                st.write(f"**Q{i+1}:** {st.session_state.interview_questions[i].text[:60]}...")
                st.write(f"**Your Answer:** {ans[:200]}...")
                st.markdown("---")


def render_interview_summary():
    """Render interview performance summary"""
    st.subheader("🎉 Interview Complete!")
    st.write("Great job! Let's evaluate your performance.")
    
    # Evaluate all answers button
    if not st.session_state.mock_interview_feedback:
        if st.button("📊 Get Feedback", type="primary", use_container_width=True):
            with st.spinner("Evaluating your answers..."):
                try:
                    agent = get_interview_prep_agent()
                    
                    # Evaluate each answer
                    for i, (question, answer) in enumerate(zip(
                        st.session_state.interview_questions,
                        st.session_state.mock_interview_answers
                    )):
                        feedback = agent.evaluate_answer(
                            question=question.text,
                            user_answer=answer,
                            question_category=question.category
                        )
                        st.session_state.mock_interview_feedback.append(feedback)
                    
                    st.success("Evaluation complete!")
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate answers: {e}")
                    st.error(f"Failed to evaluate answers: {str(e)}")
    
    # Display feedback
    if st.session_state.mock_interview_feedback:
        # Overall statistics
        avg_rating = sum(f.rating for f in st.session_state.mock_interview_feedback) / len(st.session_state.mock_interview_feedback)
        
        st.markdown("---")
        st.subheader("📈 Overall Performance")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Rating", f"{avg_rating:.1f}/10")
        with col2:
            st.metric("Questions Answered", len(st.session_state.mock_interview_answers))
        with col3:
            performance = "Excellent" if avg_rating >= 8 else "Good" if avg_rating >= 6 else "Needs Improvement"
            st.metric("Performance", performance)
        
        st.markdown("---")
        
        # Detailed feedback for each question
        st.subheader("📝 Detailed Feedback")
        
        for i, (question, answer, feedback) in enumerate(zip(
            st.session_state.interview_questions,
            st.session_state.mock_interview_answers,
            st.session_state.mock_interview_feedback
        ), 1):
            with st.expander(f"Q{i}: {question.text[:60]}... (Rating: {feedback.rating}/10)", expanded=False):
                st.write(f"**Question:** {question.text}")
                st.write(f"**Category:** {question.category} | **Difficulty:** {question.difficulty}")
                
                st.markdown("---")
                st.write("**Your Answer:**")
                st.write(answer)
                
                st.markdown("---")
                st.write(f"**Rating:** {feedback.rating}/10")
                
                if feedback.strengths:
                    st.write("**✅ Strengths:**")
                    for strength in feedback.strengths:
                        st.write(f"- {strength}")
                
                if feedback.improvements:
                    st.write("**🔧 Areas for Improvement:**")
                    for improvement in feedback.improvements:
                        st.write(f"- {improvement}")
                
                if feedback.suggestions:
                    st.write("**💡 Suggestions:**")
                    for suggestion in feedback.suggestions:
                        st.write(f"- {suggestion}")
                
                if feedback.improved_version:
                    st.write("**✨ Improved Version:**")
                    st.info(feedback.improved_version)
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Start New Interview", use_container_width=True):
                st.session_state.mock_interview_active = False
                st.session_state.mock_interview_index = 0
                st.session_state.mock_interview_answers = []
                st.session_state.mock_interview_feedback = []
                st.rerun()
        
        with col2:
            if st.button("📚 Save to Custom Questions", use_container_width=True):
                st.info("Feature to save questions coming soon!")


def render_custom_questions():
    """Render custom question management interface"""
    st.subheader("📚 Custom Question Library")
    
    # Add new question section
    with st.expander("➕ Add New Custom Question", expanded=False):
        with st.form("add_custom_question_form"):
            question_text = st.text_area(
                "Question",
                height=100,
                placeholder="Enter your interview question here..."
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category = st.selectbox(
                    "Category",
                    options=["technical", "behavioral", "system_design", "coding", "general"]
                )
            
            with col2:
                topic = st.text_input(
                    "Topic (Optional)",
                    placeholder="e.g., LangChain, RAG, Fine-tuning"
                )
            
            with col3:
                difficulty = st.selectbox(
                    "Difficulty",
                    options=["easy", "medium", "hard"]
                )
            
            user_answer = st.text_area(
                "Your Answer (Optional)",
                height=150,
                placeholder="Enter your answer to this question..."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button("💾 Save Question", use_container_width=True)
            
            with col2:
                generate_ideal = st.form_submit_button("✨ Save & Generate Ideal Answer", use_container_width=True)
            
            if submit_button or generate_ideal:
                if question_text.strip():
                    try:
                        agent = get_interview_prep_agent()
                        
                        # Generate ideal answer if requested
                        ideal_answer = None
                        if generate_ideal:
                            with st.spinner("Generating ideal answer..."):
                                ideal_answer = agent.generate_ideal_answer(
                                    question=question_text,
                                    question_category=category
                                )
                        
                        # Add custom question
                        custom_question = agent.add_custom_question(
                            user_id=st.session_state.user_id,
                            question_text=question_text,
                            category=category,
                            topic=topic if topic else None,
                            difficulty=difficulty,
                            user_answer=user_answer if user_answer else None
                        )
                        
                        # Update ideal answer if generated
                        if ideal_answer:
                            agent.update_custom_question(
                                question_id=custom_question.id,
                                updates={'ideal_answer': ideal_answer}
                            )
                        
                        st.success("✅ Question saved successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Failed to save custom question: {e}")
                        st.error(f"Failed to save question: {str(e)}")
                else:
                    st.warning("Please enter a question.")
    
    st.markdown("---")
    
    # Filter and search section
    st.subheader("🔍 Search & Filter")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            options=["All"] + ["technical", "behavioral", "system_design", "coding", "general"],
            key="filter_category"
        )
    
    with col2:
        # Get available topics
        agent = get_interview_prep_agent()
        all_questions = agent.get_custom_questions(st.session_state.user_id)
        topics = list(set([q.topic for q in all_questions if q.topic]))
        
        filter_topic = st.selectbox(
            "Filter by Topic",
            options=["All"] + sorted(topics),
            key="filter_topic"
        )
    
    with col3:
        filter_difficulty = st.selectbox(
            "Filter by Difficulty",
            options=["All", "easy", "medium", "hard"],
            key="filter_difficulty"
        )
    
    with col4:
        search_text = st.text_input(
            "Search Questions",
            placeholder="Search...",
            key="search_questions"
        )
    
    # Build filters
    filters = {}
    if filter_category != "All":
        filters['category'] = filter_category
    if filter_topic != "All":
        filters['topic'] = filter_topic
    if filter_difficulty != "All":
        filters['difficulty'] = filter_difficulty
    
    # Get filtered questions
    try:
        custom_questions = agent.get_custom_questions(st.session_state.user_id, filters)
        
        # Apply search filter
        if search_text:
            custom_questions = [
                q for q in custom_questions
                if search_text.lower() in q.question_text.lower()
            ]
        
        st.markdown("---")
        st.write(f"**Found {len(custom_questions)} question(s)**")
        
        if not custom_questions:
            st.info("No custom questions found. Add your first question above!")
        else:
            # Display questions
            for question in custom_questions:
                render_custom_question_card(question, agent)
    
    except Exception as e:
        logger.error(f"Failed to load custom questions: {e}")
        st.error(f"Failed to load questions: {str(e)}")


def render_custom_question_card(question: CustomQuestion, agent: InterviewPrepAgent):
    """Render a single custom question card"""
    with st.expander(f"📝 {question.question_text[:80]}...", expanded=False):
        # Question details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Category:** {question.category}")
        with col2:
            if question.topic:
                st.write(f"**Topic:** {question.topic}")
        with col3:
            if question.difficulty:
                st.write(f"**Difficulty:** {question.difficulty}")
        
        st.markdown("---")
        st.write("**Question:**")
        st.write(question.question_text)
        
        # Display answers side-by-side
        if question.user_answer or question.ideal_answer:
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Your Answer:**")
                if question.user_answer:
                    st.info(question.user_answer)
                else:
                    st.write("_No answer provided_")
            
            with col2:
                st.write("**Ideal Answer:**")
                if question.ideal_answer:
                    st.success(question.ideal_answer)
                else:
                    st.write("_No ideal answer generated_")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Edit", key=f"edit_{question.id}"):
                st.session_state.selected_custom_question = question.id
                st.rerun()
        
        with col2:
            if not question.ideal_answer:
                if st.button("✨ Generate Ideal Answer", key=f"generate_{question.id}"):
                    with st.spinner("Generating ideal answer..."):
                        try:
                            ideal_answer = agent.generate_ideal_answer(
                                question=question.question_text,
                                question_category=question.category
                            )
                            agent.update_custom_question(
                                question_id=question.id,
                                updates={'ideal_answer': ideal_answer}
                            )
                            st.success("Ideal answer generated!")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Failed to generate ideal answer: {e}")
                            st.error(f"Failed to generate ideal answer: {str(e)}")
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{question.id}"):
                try:
                    question_repo = QuestionRepository(st.session_state.db_manager)
                    success = question_repo.delete(question.id)
                    if success:
                        st.success("Question deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete question")
                except Exception as e:
                    logger.error(f"Failed to delete question: {e}")
                    st.error(f"Failed to delete question: {str(e)}")
        
        with col4:
            if st.button("📋 Copy Question", key=f"copy_{question.id}"):
                st.code(question.question_text, language=None)
                st.info("Question text displayed above - copy manually")
        
        # Edit mode
        if st.session_state.selected_custom_question == question.id:
            st.markdown("---")
            st.write("**Edit Question:**")
            
            with st.form(f"edit_form_{question.id}"):
                new_question_text = st.text_area(
                    "Question",
                    value=question.question_text,
                    height=100
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_category = st.selectbox(
                        "Category",
                        options=["technical", "behavioral", "system_design", "coding", "general"],
                        index=["technical", "behavioral", "system_design", "coding", "general"].index(question.category)
                    )
                
                with col2:
                    new_topic = st.text_input(
                        "Topic",
                        value=question.topic if question.topic else ""
                    )
                
                with col3:
                    difficulty_options = ["easy", "medium", "hard"]
                    default_difficulty_index = difficulty_options.index(question.difficulty) if question.difficulty in difficulty_options else 1
                    new_difficulty = st.selectbox(
                        "Difficulty",
                        options=difficulty_options,
                        index=default_difficulty_index
                    )
                
                new_user_answer = st.text_area(
                    "Your Answer",
                    value=question.user_answer if question.user_answer else "",
                    height=150
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    save_button = st.form_submit_button("💾 Save Changes", use_container_width=True)
                
                with col2:
                    cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if save_button:
                    try:
                        updates = {
                            'question_text': new_question_text,
                            'category': new_category,
                            'topic': new_topic if new_topic else None,
                            'difficulty': new_difficulty,
                            'user_answer': new_user_answer if new_user_answer else None
                        }
                        
                        success = agent.update_custom_question(question.id, updates)
                        
                        if success:
                            st.success("Question updated!")
                            st.session_state.selected_custom_question = None
                            st.rerun()
                        else:
                            st.error("Failed to update question")
                    
                    except Exception as e:
                        logger.error(f"Failed to update question: {e}")
                        st.error(f"Failed to update question: {str(e)}")
                
                if cancel_button:
                    st.session_state.selected_custom_question = None
                    st.rerun()


def render_interview_prep():
    """Main interview prep rendering function"""
    st.title("💼 Interview Prep")
    st.markdown("Prepare for your interviews with AI-generated questions and mock interviews")
    st.markdown("---")
    
    # Initialize state
    init_interview_prep_state()
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📝 Generate Questions", "🎤 Mock Interview", "📚 Custom Questions"])
    
    with tab1:
        render_question_generation()
    
    with tab2:
        render_mock_interview()
    
    with tab3:
        render_custom_questions()
