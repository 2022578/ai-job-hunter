"""
Tests for LangGraph Orchestrator
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from agents.orchestrator import LangGraphOrchestrator
from agents.job_search_agent import SearchCriteria
from models.user import UserProfile
from models.job import JobListing
from models.match_score import MatchScore


@pytest.fixture
def mock_agents():
    """Create mock agents for testing"""
    return {
        'job_search_agent': Mock(),
        'match_scorer': Mock(),
        'resume_optimizer': Mock(),
        'cover_letter_generator': Mock(),
        'interview_prep_agent': Mock(),
        'company_profiler': Mock(),
        'job_tracker': Mock(),
        'notification_service': Mock()
    }


@pytest.fixture
def orchestrator(mock_agents):
    """Create orchestrator with mock agents"""
    return LangGraphOrchestrator(
        job_search_agent=mock_agents['job_search_agent'],
        match_scorer=mock_agents['match_scorer'],
        resume_optimizer=mock_agents['resume_optimizer'],
        cover_letter_generator=mock_agents['cover_letter_generator'],
        interview_prep_agent=mock_agents['interview_prep_agent'],
        company_profiler=mock_agents['company_profiler'],
        job_tracker=mock_agents['job_tracker'],
        notification_service=mock_agents['notification_service']
    )


@pytest.fixture
def sample_job():
    """Create sample job listing"""
    return JobListing(
        id="test-job-1",
        title="Senior GenAI Engineer",
        company="Test Company",
        description="Work on LLM applications",
        source="naukri",
        source_url="https://example.com/job1",
        salary_min=35,
        salary_max=50,
        location="Bangalore",
        remote_type="hybrid",
        required_skills=["Python", "LangChain", "LLM"],
        posted_date=datetime.now(),
        created_at=datetime.now()
    )


@pytest.fixture
def sample_user_profile():
    """Create sample user profile"""
    return UserProfile(
        id="test-user-1",
        name="Test User",
        email="test@example.com",
        skills=["Python", "LangChain", "GenAI"],
        experience_years=5,
        target_salary=40,
        preferred_locations=["Bangalore"],
        preferred_remote=True,
        desired_tech_stack=["LangChain", "LangGraph"]
    )


def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes correctly"""
    assert orchestrator is not None
    assert orchestrator.job_search_agent is not None
    assert orchestrator.match_scorer is not None
    assert orchestrator.resume_optimizer is not None
    assert orchestrator.cover_letter_generator is not None
    assert orchestrator.interview_prep_agent is not None
    assert orchestrator.company_profiler is not None


def test_daily_search_workflow_success(orchestrator, mock_agents, sample_job, sample_user_profile):
    """Test successful daily search workflow execution"""
    # Setup mocks
    mock_agents['job_search_agent'].search.return_value = [sample_job]
    
    mock_score = MatchScore(
        job_id=sample_job.id,
        total_score=85.0,
        skills_match=90.0,
        salary_match=80.0,
        tech_stack_match=85.0,
        remote_flexibility=100.0,
        company_profile_score=70.0
    )
    mock_agents['match_scorer'].rank_jobs.return_value = [(sample_job, mock_score)]
    mock_agents['match_scorer'].update_job_scores.return_value = 1
    
    mock_agents['notification_service'].send_daily_digest.return_value = {
        'email': True,
        'whatsapp': False
    }
    
    # Execute workflow
    search_criteria = SearchCriteria(
        keywords=["GenAI", "LLM"],
        min_salary_lakhs=35
    )
    
    results = orchestrator.execute_daily_search(
        search_criteria=search_criteria,
        user_profile=sample_user_profile,
        user_id="test-user-1"
    )
    
    # Verify results
    assert results['success'] is True
    assert results['jobs_found'] == 1
    assert results['jobs_scored'] == 1
    assert results['notification_sent'] is True
    assert results['error'] is None
    
    # Verify agent calls
    mock_agents['job_search_agent'].search.assert_called_once()
    mock_agents['match_scorer'].rank_jobs.assert_called_once()
    mock_agents['notification_service'].send_daily_digest.assert_called_once()


def test_daily_search_workflow_no_jobs(orchestrator, mock_agents, sample_user_profile):
    """Test daily search workflow when no jobs found"""
    # Setup mocks
    mock_agents['job_search_agent'].search.return_value = []
    mock_agents['match_scorer'].rank_jobs.return_value = []
    
    # Execute workflow
    search_criteria = SearchCriteria(
        keywords=["GenAI"],
        min_salary_lakhs=35
    )
    
    results = orchestrator.execute_daily_search(
        search_criteria=search_criteria,
        user_profile=sample_user_profile,
        user_id="test-user-1"
    )
    
    # Verify results
    assert results['success'] is True
    assert results['jobs_found'] == 0
    assert results['jobs_scored'] == 0


def test_optimize_resume_workflow_success(orchestrator, mock_agents, sample_job):
    """Test successful resume optimization workflow"""
    # Setup mocks
    mock_agents['match_scorer'].job_repository = Mock()
    mock_agents['match_scorer'].job_repository.find_by_id.return_value = sample_job
    
    mock_optimization = Mock()
    mock_optimization.analysis = Mock()
    mock_optimization.analysis.overall_score = 8.5
    mock_agents['resume_optimizer'].optimize_for_job.return_value = mock_optimization
    
    # Execute workflow
    results = orchestrator.optimize_resume(
        user_id="test-user-1",
        resume_text="Sample resume content",
        job_id=sample_job.id
    )
    
    # Verify results
    assert results['success'] is True
    assert results['optimization_result'] is not None
    assert results['error'] is None
    
    # Verify agent calls
    mock_agents['resume_optimizer'].optimize_for_job.assert_called_once()


def test_generate_cover_letter_workflow_success(orchestrator, mock_agents, sample_job):
    """Test successful cover letter generation workflow"""
    # Setup mocks
    mock_agents['match_scorer'].job_repository = Mock()
    mock_agents['match_scorer'].job_repository.find_by_id.return_value = sample_job
    
    mock_cover_letter = "Dear Hiring Manager,\n\nI am excited to apply..."
    mock_agents['cover_letter_generator'].generate.return_value = mock_cover_letter
    
    # Execute workflow
    results = orchestrator.generate_cover_letter(
        user_id="test-user-1",
        job_id=sample_job.id,
        resume_summary="Experienced GenAI engineer",
        tone="professional"
    )
    
    # Verify results
    assert results['success'] is True
    assert results['cover_letter'] is not None
    assert len(results['cover_letter']) > 0
    assert results['error'] is None
    
    # Verify agent calls
    mock_agents['cover_letter_generator'].generate.assert_called_once()


def test_prepare_interview_workflow_success(orchestrator, mock_agents, sample_job):
    """Test successful interview preparation workflow"""
    # Setup mocks
    mock_agents['match_scorer'].job_repository = Mock()
    mock_agents['match_scorer'].job_repository.find_by_id.return_value = sample_job
    
    mock_questions = [
        Mock(text="What is LangChain?", category="technical", difficulty="medium"),
        Mock(text="Explain RAG", category="technical", difficulty="medium")
    ]
    mock_agents['interview_prep_agent'].generate_questions.return_value = mock_questions
    
    # Execute workflow
    results = orchestrator.prepare_interview(
        user_id="test-user-1",
        job_id=sample_job.id,
        question_type="technical",
        difficulty="medium"
    )
    
    # Verify results
    assert results['success'] is True
    assert results['questions'] is not None
    assert len(results['questions']) == 2
    assert results['error'] is None
    
    # Verify agent calls
    mock_agents['interview_prep_agent'].generate_questions.assert_called_once()


def test_profile_company_workflow_success(orchestrator, mock_agents):
    """Test successful company profiling workflow"""
    # Setup mocks
    mock_profile = Mock()
    mock_profile.company_name = "Test Company"
    mock_profile.glassdoor_rating = 4.2
    mock_profile.genai_focus_score = 8.5
    
    mock_agents['company_profiler'].profile_company.return_value = mock_profile
    mock_agents['company_profiler'].summarize_fit.return_value = "Great fit for GenAI roles"
    
    # Execute workflow
    user_preferences = {
        'preferred_remote': True,
        'target_salary': 40
    }
    
    results = orchestrator.profile_company(
        company_name="Test Company",
        user_preferences=user_preferences,
        use_cache=True
    )
    
    # Verify results
    assert results['success'] is True
    assert results['profile'] is not None
    assert results['fit_summary'] is not None
    assert results['error'] is None
    
    # Verify agent calls
    mock_agents['company_profiler'].profile_company.assert_called_once()
    mock_agents['company_profiler'].summarize_fit.assert_called_once()


def test_workflow_error_handling(orchestrator, mock_agents, sample_user_profile):
    """Test workflow error handling"""
    # Setup mock to raise exception
    mock_agents['job_search_agent'].search.side_effect = Exception("Network error")
    
    # Execute workflow
    search_criteria = SearchCriteria(
        keywords=["GenAI"],
        min_salary_lakhs=35
    )
    
    results = orchestrator.execute_daily_search(
        search_criteria=search_criteria,
        user_profile=sample_user_profile,
        user_id="test-user-1"
    )
    
    # Verify error handling
    assert results['success'] is False
    assert results['error'] is not None
    assert "Network error" in results['error']


def test_handle_workflow_error(orchestrator):
    """Test error recovery handler"""
    error = Exception("Connection timeout")
    
    error_info = orchestrator.handle_workflow_error("daily_search", error)
    
    assert error_info['workflow'] == "daily_search"
    assert error_info['error'] == "Connection timeout"
    assert error_info['error_type'] == "Exception"
    assert error_info['recovery_strategy'] == "retry_with_backoff"
    assert 'timestamp' in error_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
