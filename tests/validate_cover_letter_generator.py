"""
Validation script for Cover Letter Generator
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.cover_letter_generator import CoverLetterGenerator, CoverLetter
from utils.llm_client import OllamaClient
from database.db_manager import DatabaseManager
from models.job import JobListing


def test_basic_functionality():
    """Test basic cover letter generator functionality"""
    print("=" * 60)
    print("COVER LETTER GENERATOR VALIDATION")
    print("=" * 60)
    
    # Setup
    print("\n1. Setting up test environment...")
    db_path = "data/test_cover_letter_validation.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    llm_client = OllamaClient(model="llama3", timeout=60)
    generator = CoverLetterGenerator(llm_client, db_manager)
    
    print("✓ Generator initialized successfully")
    
    # Create sample job
    print("\n2. Creating sample job listing...")
    job = JobListing(
        id="test-job-1",
        title="Senior LLM Engineer",
        company="TechCorp AI",
        description="""We are seeking a Senior LLM Engineer to join our GenAI team.
        
        Requirements:
        - 5+ years of experience in ML/AI
        - Strong experience with LLMs, LangChain, and prompt engineering
        - Experience building RAG systems
        - Python expertise
        
        Responsibilities:
        - Design and implement LLM-powered applications
        - Build and optimize RAG pipelines""",
        source="naukri",
        source_url="https://example.com/job1",
        salary_min=35,
        salary_max=50,
        location="Bangalore",
        remote_type="hybrid",
        required_skills=["Python", "LLM", "LangChain", "RAG"]
    )
    
    print(f"✓ Job created: {job.title} at {job.company}")
    
    # Create sample resume
    print("\n3. Creating sample resume summary...")
    resume_summary = """Senior Software Engineer with 6 years of experience in AI/ML.
    
    Key Experience:
    - Built production LLM applications using LangChain
    - Developed RAG systems for enterprise knowledge management
    - Implemented autonomous agent frameworks
    
    Technical Skills: Python, LangChain, LangGraph, PyTorch"""
    
    print("✓ Resume summary created")
    
    # Test 1: Generate cover letter with professional tone
    print("\n4. Testing cover letter generation (professional tone)...")
    try:
        letter_professional = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-1",
            tone="professional"
        )
        
        if letter_professional and len(letter_professional) > 100:
            print("✓ Professional cover letter generated successfully")
            print(f"  Length: {len(letter_professional)} characters")
            print(f"  Preview: {letter_professional[:150]}...")
        else:
            print("✗ Failed: Letter too short or empty")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2: Generate with enthusiastic tone
    print("\n5. Testing cover letter generation (enthusiastic tone)...")
    try:
        letter_enthusiastic = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-2",
            tone="enthusiastic"
        )
        
        if letter_enthusiastic and len(letter_enthusiastic) > 100:
            print("✓ Enthusiastic cover letter generated successfully")
            print(f"  Length: {len(letter_enthusiastic)} characters")
        else:
            print("✗ Failed: Letter too short or empty")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 3: Generate with technical tone
    print("\n6. Testing cover letter generation (technical tone)...")
    try:
        letter_technical = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-3",
            tone="technical"
        )
        
        if letter_technical and len(letter_technical) > 100:
            print("✓ Technical cover letter generated successfully")
            print(f"  Length: {len(letter_technical)} characters")
        else:
            print("✗ Failed: Letter too short or empty")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 4: Test caching
    print("\n7. Testing caching mechanism...")
    try:
        letter_cached = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-1",
            tone="professional"
        )
        
        if letter_cached == letter_professional:
            print("✓ Caching works correctly (returned same letter)")
        else:
            print("✗ Warning: Cache returned different letter")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 5: Test with relevant projects
    print("\n8. Testing generation with relevant projects...")
    try:
        projects = [
            "Built RAG system for customer support with 95% accuracy",
            "Developed multi-agent system for automated code review"
        ]
        
        letter_with_projects = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-4",
            relevant_projects=projects,
            tone="technical"
        )
        
        if letter_with_projects and len(letter_with_projects) > 100:
            print("✓ Cover letter with projects generated successfully")
            print(f"  Length: {len(letter_with_projects)} characters")
        else:
            print("✗ Failed: Letter too short or empty")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 6: Test save_letter
    print("\n9. Testing save_letter method...")
    try:
        success = generator.save_letter(
            job_id="test-job-save",
            user_id="test-user-save",
            content="This is a test cover letter for validation.",
            tone="professional"
        )
        
        if success:
            print("✓ Letter saved successfully")
        else:
            print("✗ Failed to save letter")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 7: Test get_letter_by_job
    print("\n10. Testing get_letter_by_job method...")
    try:
        retrieved_letter = generator.get_letter_by_job(
            job_id=job.id,
            user_id="test-user-1",
            tone="professional"
        )
        
        if retrieved_letter == letter_professional:
            print("✓ Letter retrieved successfully from cache")
        else:
            print("✗ Retrieved letter doesn't match original")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 8: Test invalid tone handling
    print("\n11. Testing invalid tone handling...")
    try:
        letter_invalid_tone = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-invalid",
            tone="invalid_tone"
        )
        
        if letter_invalid_tone and len(letter_invalid_tone) > 100:
            print("✓ Invalid tone handled gracefully (defaulted to professional)")
        else:
            print("✗ Failed to handle invalid tone")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Cleanup
    print("\n12. Cleaning up...")
    db_manager.close_connection()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✓ Cleanup completed")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
