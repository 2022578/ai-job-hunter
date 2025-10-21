"""
Tests for Interview Prep Agent
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from agents.interview_prep_agent import (
    InterviewPrepAgent,
    Question,
    InterviewSession,
    Feedback
)
from models.job import JobListing
from models.question import CustomQuestion
from utils.llm_client import LLMResponse


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client"""
    client = Mock()
    return client


@pytest.fixture
def mock_question_repo():
    """Create mock question repository"""
    repo = Mock()
    return repo


@pytest.fixture
def interview_agent(mock_llm_client, mock_question_repo):
    """Create InterviewPrepAgent instance"""
    return InterviewPrepAgent(mock_llm_client, mock_question_repo)


@pytest.fixture
def sample_job():
    """Create sample job listing"""
    return JobListing(
        title="Senior LLM Engineer",
        company="TechCorp",
        description="Looking for an experienced LLM engineer with expertise in LangChain, RAG systems, and autonomous agents.",
        source="naukri",
        source_url="https://example.com/job/123",
        salary_min=35,
        salary_max=50,
        location="Bangalore",
        remote_type="hybrid",
        required_skills=["Python", "LangChain", "LLM", "RAG"]
    )


def test_generate_questions_success(interview_agent, mock_llm_client, sample_job):
    """Test successful question generation"""
    # Mock LLM response
    mock_response = LLMResponse(
        text="""**Q1: What is RAG and how does it work?**
Category: RAG Systems
Difficulty: medium

**Q2: Explain the difference between few-shot and zero-shot learning.**
Category: LLM Fundamentals
Difficulty: easy

**Q3: How would you implement a multi-agent system using LangChain?**
Category: LangChain
Difficulty: hard""",
        model="llama3",
        tokens_used=500
    )
    mock_llm_client.generate_with_retry.return_value = mock_response
    
    # Generate questions
    questions = interview_agent.generate_questions(
        job=sample_job,
        question_type="technical",
        difficulty="medium",
        count=3
    )
    
    # Verify
    assert len(questions) == 3
    assert questions[0].text == "What is RAG and how does it work?"
    assert questions[0].category == "RAG Systems"
    assert questions[0].difficulty == "medium"
    assert questions[1].text == "Explain the difference between few-shot and zero-shot learning."
    assert questions[2].text == "How would you implement a multi-agent system using LangChain?"


def test_generate_questions_invalid_type(interview_agent, sample_job):
    """Test question generation with invalid type"""
    with pytest.raises(ValueError, match="Invalid question_type"):
        interview_agent.generate_questions(
            job=sample_job,
            question_type="invalid",
            difficulty="medium",
            count=5
        )


def test_generate_questions_invalid_difficulty(interview_agent, sample_job):
    """Test question generation with invalid difficulty"""
    with pytest.raises(ValueError, match="Invalid difficulty"):
        interview_agent.generate_questions(
            job=sample_job,
            question_type="technical",
            difficulty="super_hard",
            count=5
        )


def test_generate_questions_invalid_count(interview_agent, sample_job):
    """Test question generation with invalid count"""
    with pytest.raises(ValueError, match="Count must be between"):
        interview_agent.generate_questions(
            job=sample_job,
            question_type="technical",
            difficulty="medium",
            count=100
        )


def test_evaluate_answer_success(interview_agent, mock_llm_client):
    """Test successful answer evaluation"""
    # Mock LLM response
    mock_response = LLMResponse(
        text="""**OVERALL ASSESSMENT:** Good answer with relevant details
**RATING:** 8/10

**STRENGTHS:**
- Clear explanation of RAG components
- Mentioned vector databases
- Provided practical example

**AREAS FOR IMPROVEMENT:**
- Could discuss chunking strategies
- Missing information about embedding models

**SUGGESTIONS:**
- Add details about chunk size optimization
- Mention specific vector database options

**IMPROVED VERSION:**
RAG combines retrieval with generation. Documents are chunked, embedded using models like sentence-transformers, and stored in vector databases like Pinecone. When queried, relevant chunks are retrieved and provided as context to the LLM.""",
        model="llama3",
        tokens_used=300
    )
    mock_llm_client.generate_with_retry.return_value = mock_response
    
    # Evaluate answer
    feedback = interview_agent.evaluate_answer(
        question="What is RAG?",
        user_answer="RAG is a system that retrieves relevant information and uses it to generate responses.",
        question_category="technical"
    )
    
    # Verify
    assert feedback.rating == 8.0
    assert len(feedback.strengths) == 3
    assert "Clear explanation" in feedback.strengths[0]
    assert len(feedback.improvements) == 2
    assert len(feedback.suggestions) == 2
    assert "RAG combines retrieval" in feedback.improved_version


def test_conduct_mock_interview(interview_agent, mock_llm_client):
    """Test mock interview session"""
    # Create questions
    questions = [
        Question(text="What is LangChain?", category="technical", difficulty="easy"),
        Question(text="Explain RAG systems", category="technical", difficulty="medium")
    ]
    
    user_answers = [
        "LangChain is a framework for building LLM applications.",
        "RAG systems retrieve relevant information to augment LLM responses."
    ]
    
    # Mock LLM responses for evaluation
    mock_response = LLMResponse(
        text="""**RATING:** 7/10
**STRENGTHS:**
- Good basic understanding
**AREAS FOR IMPROVEMENT:**
- Add more details
**SUGGESTIONS:**
- Provide examples
**IMPROVED VERSION:**
Better answer here.""",
        model="llama3",
        tokens_used=200
    )
    mock_llm_client.generate_with_retry.return_value = mock_response
    
    # Conduct interview
    session = interview_agent.conduct_mock_interview(questions, user_answers)
    
    # Verify
    assert len(session.questions) == 2
    assert len(session.answers) == 2
    assert len(session.feedback) == 2
    assert session.started_at is not None
    assert session.completed_at is not None


def test_conduct_mock_interview_mismatch(interview_agent):
    """Test mock interview with mismatched questions and answers"""
    questions = [
        Question(text="What is LangChain?", category="technical", difficulty="easy")
    ]
    user_answers = ["Answer 1", "Answer 2"]
    
    with pytest.raises(ValueError, match="count mismatch"):
        interview_agent.conduct_mock_interview(questions, user_answers)


def test_add_custom_question_success(interview_agent, mock_question_repo):
    """Test adding custom question"""
    mock_question_repo.save.return_value = True
    
    question = interview_agent.add_custom_question(
        user_id="user123",
        question_text="What is prompt engineering?",
        category="technical",
        topic="LLM",
        difficulty="easy"
    )
    
    assert question.user_id == "user123"
    assert question.question_text == "What is prompt engineering?"
    assert question.category == "technical"
    assert question.topic == "LLM"
    assert question.difficulty == "easy"
    mock_question_repo.save.assert_called_once()


def test_add_custom_question_validation_error(interview_agent):
    """Test adding custom question with validation error"""
    with pytest.raises(ValueError):
        interview_agent.add_custom_question(
            user_id="user123",
            question_text="",
            category="technical"
        )


def test_generate_ideal_answer(interview_agent, mock_llm_client):
    """Test ideal answer generation"""
    mock_response = LLMResponse(
        text="RAG (Retrieval-Augmented Generation) is a technique that combines information retrieval with LLM generation. It works by first retrieving relevant documents from a knowledge base, then using those documents as context for the LLM to generate accurate, grounded responses.",
        model="llama3",
        tokens_used=150
    )
    mock_llm_client.generate_with_retry.return_value = mock_response
    
    ideal_answer = interview_agent.generate_ideal_answer(
        question="What is RAG?",
        question_category="technical"
    )
    
    assert "RAG" in ideal_answer
    assert "retrieval" in ideal_answer.lower()
    assert len(ideal_answer) > 50


def test_get_custom_questions(interview_agent, mock_question_repo):
    """Test retrieving custom questions"""
    mock_questions = [
        CustomQuestion(
            user_id="user123",
            question_text="Question 1",
            category="technical"
        ),
        CustomQuestion(
            user_id="user123",
            question_text="Question 2",
            category="behavioral"
        )
    ]
    mock_question_repo.find_by_user.return_value = mock_questions
    
    questions = interview_agent.get_custom_questions(
        user_id="user123",
        filters={"category": "technical"}
    )
    
    assert len(questions) == 2
    mock_question_repo.find_by_user.assert_called_once_with("user123", {"category": "technical"})


def test_update_custom_question(interview_agent, mock_question_repo):
    """Test updating custom question"""
    existing_question = CustomQuestion(
        id="q123",
        user_id="user123",
        question_text="Old question",
        category="technical"
    )
    mock_question_repo.find_by_id.return_value = existing_question
    mock_question_repo.update.return_value = True
    
    success = interview_agent.update_custom_question(
        question_id="q123",
        updates={"question_text": "Updated question", "difficulty": "hard"}
    )
    
    assert success
    mock_question_repo.find_by_id.assert_called_once_with("q123")
    mock_question_repo.update.assert_called_once()


def test_update_custom_question_not_found(interview_agent, mock_question_repo):
    """Test updating non-existent question"""
    mock_question_repo.find_by_id.return_value = None
    
    success = interview_agent.update_custom_question(
        question_id="nonexistent",
        updates={"question_text": "Updated"}
    )
    
    assert not success


def test_link_question_to_job(interview_agent, mock_question_repo):
    """Test linking question to job"""
    existing_question = CustomQuestion(
        id="q123",
        user_id="user123",
        question_text="Question",
        category="technical"
    )
    mock_question_repo.find_by_id.return_value = existing_question
    mock_question_repo.update.return_value = True
    
    success = interview_agent.link_question_to_job(
        question_id="q123",
        job_id="job456"
    )
    
    assert success
    mock_question_repo.update.assert_called_once()


def test_get_questions_for_job(interview_agent, mock_question_repo):
    """Test retrieving questions for specific job"""
    mock_questions = [
        CustomQuestion(
            user_id="user123",
            question_text="Question 1",
            category="technical",
            topic="job:job456"
        ),
        CustomQuestion(
            user_id="user123",
            question_text="Question 2",
            category="technical",
            topic="LLM"
        )
    ]
    mock_question_repo.find_by_user.return_value = mock_questions
    
    job_questions = interview_agent.get_questions_for_job(
        user_id="user123",
        job_id="job456"
    )
    
    assert len(job_questions) == 1
    assert "job:job456" in job_questions[0].topic
