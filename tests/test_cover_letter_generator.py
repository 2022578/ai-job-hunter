"""
Tests for Cover Letter Generator Agent
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.cover_letter_generator import CoverLetterGenerator, CoverLetter
from utils.llm_client import OllamaClient
from database.db_manager import DatabaseManager
from models.job import JobListing


@pytest.fixture
def db_manager():
    """Create test database manager"""
    db_path = "data/test_cover_letter.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    db.initialize_database()
    
    yield db
    
    # Cleanup
    db.close_connection()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def llm_client():
    """Create LLM client"""
    return OllamaClient(model="llama3", timeout=60)


@pytest.fixture
def generator(llm_client, db_manager):
    """Create cover letter generator"""
    return CoverLetterGenerator(llm_client, db_manager)


@pytest.fixture
def sample_job():
    """Create sample job listing"""
    return JobListing(
        id="test-job-1",
        title="Senior LLM Engineer",
        company="TechCorp AI",
        description="""We are seeking a Senior LLM Engineer to join our GenAI team.
        
        Requirements:
        - 5+ years of experience in ML/AI
        - Strong experience with LLMs, LangChain, and prompt engineering
        - Experience building RAG systems
        - Python expertise
        - Experience with autonomous agents
        
        Responsibilities:
        - Design and implement LLM-powered applications
        - Build and optimize RAG pipelines
        - Develop autonomous agent systems
        - Collaborate with cross-functional teams""",
        source="naukri",
        source_url="https://example.com/job1",
        salary_min=35,
        salary_max=50,
        location="Bangalore",
        remote_type="hybrid",
        required_skills=["Python", "LLM", "LangChain", "RAG"]
    )


@pytest.fixture
def sample_resume():
    """Sample resume summary"""
    return """Senior Software Engineer with 6 years of experience in AI/ML.
    
    Key Experience:
    - Built production LLM applications using LangChain and OpenAI
    - Developed RAG systems for enterprise knowledge management
    - Implemented autonomous agent frameworks for workflow automation
    - Led team of 4 engineers on GenAI projects
    
    Technical Skills: Python, LangChain, LangGraph, PyTorch, Vector Databases, Prompt Engineering"""


def test_generator_initialization(generator):
    """Test generator initializes correctly"""
    assert generator is not None
    assert generator.llm_client is not None
    assert generator.db_manager is not None
    assert generator.CACHE_DURATION_DAYS == 7
    assert "professional" in generator.VALID_TONES


def test_generate_cover_letter(generator, sample_job, sample_resume):
    """Test basic cover letter generation"""
    letter = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id="test-user-1",
        tone="professional"
    )
    
    assert letter is not None
    assert len(letter) > 100
    assert isinstance(letter, str)
    # Check that it's not an error message
    assert not letter.startswith("Failed to generate")


def test_generate_with_different_tones(generator, sample_job, sample_resume):
    """Test generation with different tones"""
    tones = ["professional", "enthusiastic", "technical"]
    
    for tone in tones:
        letter = generator.generate(
            job=sample_job,
            resume_summary=sample_resume,
            user_id=f"test-user-{tone}",
            tone=tone
        )
        
        assert letter is not None
        assert len(letter) > 100


def test_generate_with_projects(generator, sample_job, sample_resume):
    """Test generation with relevant projects"""
    projects = [
        "Built RAG system for customer support with 95% accuracy",
        "Developed multi-agent system for automated code review"
    ]
    
    letter = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id="test-user-projects",
        relevant_projects=projects,
        tone="technical"
    )
    
    assert letter is not None
    assert len(letter) > 100


def test_caching_mechanism(generator, sample_job, sample_resume):
    """Test that letters are cached correctly"""
    user_id = "test-user-cache"
    
    # Generate first letter
    letter1 = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id=user_id,
        tone="professional"
    )
    
    # Generate second letter (should use cache)
    letter2 = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id=user_id,
        tone="professional"
    )
    
    # Should be identical due to caching
    assert letter1 == letter2


def test_regenerate_with_tone(generator, sample_job, sample_resume, db_manager):
    """Test regenerating with different tone"""
    user_id = "test-user-regen"
    
    # First, save the job to database
    conn = db_manager.get_connection()
    job_dict = sample_job.to_db_dict()
    conn.execute("""
        INSERT INTO jobs (
            id, title, company, description, source, source_url,
            salary_min, salary_max, location, remote_type, required_skills
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_dict['id'], job_dict['title'], job_dict['company'],
        job_dict['description'], job_dict['source'], job_dict['source_url'],
        job_dict['salary_min'], job_dict['salary_max'], job_dict['location'],
        job_dict['remote_type'], job_dict['required_skills']
    ))
    conn.commit()
    
    # Generate initial letter
    letter1 = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id=user_id,
        tone="professional"
    )
    
    # Regenerate with different tone
    letter2 = generator.regenerate_with_tone(
        job_id=sample_job.id,
        resume_summary=sample_resume,
        tone="enthusiastic",
        user_id=user_id
    )
    
    assert letter1 != letter2
    assert len(letter2) > 100


def test_save_letter(generator):
    """Test saving cover letter"""
    success = generator.save_letter(
        job_id="test-job-save",
        user_id="test-user-save",
        content="This is a test cover letter.",
        tone="professional"
    )
    
    assert success is True


def test_get_letter_by_job(generator, sample_job, sample_resume):
    """Test retrieving letter by job"""
    user_id = "test-user-retrieve"
    
    # Generate and cache letter
    original_letter = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id=user_id,
        tone="professional"
    )
    
    # Retrieve it
    retrieved_letter = generator.get_letter_by_job(
        job_id=sample_job.id,
        user_id=user_id,
        tone="professional"
    )
    
    assert retrieved_letter == original_letter


def test_invalid_tone_defaults_to_professional(generator, sample_job, sample_resume):
    """Test that invalid tone defaults to professional"""
    letter = generator.generate(
        job=sample_job,
        resume_summary=sample_resume,
        user_id="test-user-invalid-tone",
        tone="invalid_tone"
    )
    
    # Should still generate successfully with default tone
    assert letter is not None
    assert len(letter) > 100


def test_cover_letter_dataclass():
    """Test CoverLetter dataclass"""
    letter = CoverLetter(
        job_id="job-1",
        user_id="user-1",
        content="Test content",
        tone="professional"
    )
    
    assert letter.id is not None
    assert letter.job_id == "job-1"
    assert letter.user_id == "user-1"
    assert letter.content == "Test content"
    assert letter.tone == "professional"
    assert isinstance(letter.generated_at, datetime)
    assert isinstance(letter.expires_at, datetime)
    assert letter.expires_at > letter.generated_at


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
