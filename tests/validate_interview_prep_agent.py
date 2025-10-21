"""
Validation script for Interview Prep Agent implementation
Tests core functionality without requiring full dependencies
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from unittest.mock import Mock

from agents.interview_prep_agent import (
    InterviewPrepAgent,
    Question,
    InterviewSession,
    Feedback
)
from models.job import JobListing
from models.question import CustomQuestion
from utils.llm_client import LLMResponse


def test_question_dataclass():
    """Test Question dataclass"""
    q = Question(
        text="What is LangChain?",
        category="technical",
        difficulty="medium",
        topic="LangChain"
    )
    assert q.text == "What is LangChain?"
    assert q.category == "technical"
    assert q.difficulty == "medium"
    assert q.topic == "LangChain"
    print("✓ Question dataclass works")


def test_feedback_dataclass():
    """Test Feedback dataclass"""
    f = Feedback(
        rating=8.5,
        strengths=["Good explanation", "Clear examples"],
        improvements=["Add more details"],
        suggestions=["Include code samples"],
        improved_version="Better answer here"
    )
    assert f.rating == 8.5
    assert len(f.strengths) == 2
    assert len(f.improvements) == 1
    print("✓ Feedback dataclass works")


def test_interview_session_dataclass():
    """Test InterviewSession dataclass"""
    questions = [
        Question(text="Q1", category="technical", difficulty="easy"),
        Question(text="Q2", category="behavioral", difficulty="medium")
    ]
    session = InterviewSession(
        questions=questions,
        answers=["A1", "A2"],
        feedback=["F1", "F2"],
        started_at=datetime.now()
    )
    assert len(session.questions) == 2
    assert len(session.answers) == 2
    assert session.started_at is not None
    print("✓ InterviewSession dataclass works")


def test_agent_initialization():
    """Test agent initialization"""
    mock_llm = Mock()
    mock_repo = Mock()
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    assert agent.llm_client == mock_llm
    assert agent.question_repo == mock_repo
    print("✓ Agent initialization works")


def test_parse_questions_from_response():
    """Test question parsing from LLM response"""
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    response = LLMResponse(
        text="""**Q1: What is RAG?**
Category: RAG Systems
Difficulty: medium

**Q2: Explain LangChain**
Category: LangChain
Difficulty: easy

Q3: How do you fine-tune an LLM?
Category: Fine-tuning
Difficulty: hard""",
        model="llama3",
        tokens_used=200
    )
    
    questions = agent._parse_questions_from_response(response, "technical", "medium")
    
    assert len(questions) == 3
    assert questions[0].text == "What is RAG?"
    assert questions[0].category == "RAG Systems"
    assert questions[1].text == "Explain LangChain"
    assert questions[2].text == "How do you fine-tune an LLM?"
    print("✓ Question parsing works")


def test_parse_feedback_from_response():
    """Test feedback parsing from LLM response"""
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    response = LLMResponse(
        text="""**OVERALL ASSESSMENT:** Good answer
**RATING:** 7.5/10

**STRENGTHS:**
- Clear explanation
- Good examples
- Technical accuracy

**AREAS FOR IMPROVEMENT:**
- Could add more depth
- Missing edge cases

**SUGGESTIONS:**
- Include code samples
- Discuss trade-offs

**IMPROVED VERSION:**
Here is a better version of the answer with more details.""",
        model="llama3",
        tokens_used=300
    )
    
    feedback = agent._parse_feedback_from_response(response)
    
    assert feedback.rating == 7.5
    assert len(feedback.strengths) >= 2
    assert len(feedback.improvements) >= 1
    assert len(feedback.suggestions) >= 1
    assert "better version" in feedback.improved_version.lower()
    print("✓ Feedback parsing works")


def test_format_feedback():
    """Test feedback formatting"""
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    feedback = Feedback(
        rating=8.0,
        strengths=["Good structure", "Clear examples"],
        improvements=["Add more details"],
        suggestions=["Include metrics"],
        improved_version="Enhanced answer"
    )
    
    formatted = agent._format_feedback(feedback)
    
    assert "Rating: 8.0/10" in formatted
    assert "Strengths:" in formatted
    assert "Good structure" in formatted
    assert "Areas for Improvement:" in formatted
    assert "Suggestions:" in formatted
    assert "Improved Version:" in formatted
    print("✓ Feedback formatting works")


def test_generate_questions_validation():
    """Test question generation validation"""
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    job = JobListing(
        title="LLM Engineer",
        company="TechCorp",
        description="Build LLM applications",
        source="naukri",
        source_url="https://example.com/job"
    )
    
    # Test invalid question type
    try:
        agent.generate_questions(job, question_type="invalid", difficulty="medium", count=5)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid question_type" in str(e)
        print("✓ Question type validation works")
    
    # Test invalid difficulty
    try:
        agent.generate_questions(job, question_type="technical", difficulty="super_hard", count=5)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Invalid difficulty" in str(e)
        print("✓ Difficulty validation works")
    
    # Test invalid count
    try:
        agent.generate_questions(job, question_type="technical", difficulty="medium", count=100)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Count must be between" in str(e)
        print("✓ Count validation works")


def test_conduct_mock_interview_validation():
    """Test mock interview validation"""
    mock_llm = Mock()
    mock_repo = Mock()
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    questions = [
        Question(text="Q1", category="technical", difficulty="easy")
    ]
    answers = ["A1", "A2"]  # Mismatch
    
    try:
        agent.conduct_mock_interview(questions, answers)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "count mismatch" in str(e)
        print("✓ Mock interview validation works")


def test_add_custom_question():
    """Test adding custom question"""
    mock_llm = Mock()
    mock_repo = Mock()
    mock_repo.save.return_value = True
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    
    question = agent.add_custom_question(
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
    assert mock_repo.save.called
    print("✓ Add custom question works")


def test_get_custom_questions():
    """Test retrieving custom questions"""
    mock_llm = Mock()
    mock_repo = Mock()
    
    mock_questions = [
        CustomQuestion(
            user_id="user123",
            question_text="Q1",
            category="technical"
        ),
        CustomQuestion(
            user_id="user123",
            question_text="Q2",
            category="behavioral"
        )
    ]
    mock_repo.find_by_user.return_value = mock_questions
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    questions = agent.get_custom_questions("user123", {"category": "technical"})
    
    assert len(questions) == 2
    assert mock_repo.find_by_user.called
    print("✓ Get custom questions works")


def test_update_custom_question():
    """Test updating custom question"""
    mock_llm = Mock()
    mock_repo = Mock()
    
    existing_question = CustomQuestion(
        id="q123",
        user_id="user123",
        question_text="Old question",
        category="technical"
    )
    mock_repo.find_by_id.return_value = existing_question
    mock_repo.update.return_value = True
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    success = agent.update_custom_question(
        question_id="q123",
        updates={"question_text": "Updated question"}
    )
    
    assert success
    assert mock_repo.find_by_id.called
    assert mock_repo.update.called
    print("✓ Update custom question works")


def test_link_question_to_job():
    """Test linking question to job"""
    mock_llm = Mock()
    mock_repo = Mock()
    
    existing_question = CustomQuestion(
        id="q123",
        user_id="user123",
        question_text="Question",
        category="technical"
    )
    mock_repo.find_by_id.return_value = existing_question
    mock_repo.update.return_value = True
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    success = agent.link_question_to_job("q123", "job456")
    
    assert success
    assert mock_repo.update.called
    print("✓ Link question to job works")


def test_get_questions_for_job():
    """Test retrieving questions for job"""
    mock_llm = Mock()
    mock_repo = Mock()
    
    mock_questions = [
        CustomQuestion(
            user_id="user123",
            question_text="Q1",
            category="technical",
            topic="job:job456"
        ),
        CustomQuestion(
            user_id="user123",
            question_text="Q2",
            category="technical",
            topic="LLM"
        )
    ]
    mock_repo.find_by_user.return_value = mock_questions
    
    agent = InterviewPrepAgent(mock_llm, mock_repo)
    job_questions = agent.get_questions_for_job("user123", "job456")
    
    assert len(job_questions) == 1
    assert "job:job456" in job_questions[0].topic
    print("✓ Get questions for job works")


def main():
    """Run all validation tests"""
    print("\n=== Validating Interview Prep Agent Implementation ===\n")
    
    tests = [
        test_question_dataclass,
        test_feedback_dataclass,
        test_interview_session_dataclass,
        test_agent_initialization,
        test_parse_questions_from_response,
        test_parse_feedback_from_response,
        test_format_feedback,
        test_generate_questions_validation,
        test_conduct_mock_interview_validation,
        test_add_custom_question,
        test_get_custom_questions,
        test_update_custom_question,
        test_link_question_to_job,
        test_get_questions_for_job
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
