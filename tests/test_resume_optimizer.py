"""
Test Resume Optimizer Agent
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only what we need to avoid selenium dependency
import importlib.util

# Load resume_optimizer module directly
spec = importlib.util.spec_from_file_location(
    "resume_optimizer",
    os.path.join(os.path.dirname(__file__), '..', 'agents', 'resume_optimizer.py')
)
resume_optimizer_module = importlib.util.module_from_spec(spec)

# Load dependencies
from utils.llm_client import OllamaClient
from database.db_manager import DatabaseManager
from models.job import JobListing
from datetime import datetime

# Execute the module
spec.loader.exec_module(resume_optimizer_module)

# Get classes from module
ResumeOptimizer = resume_optimizer_module.ResumeOptimizer
ResumeAnalysis = resume_optimizer_module.ResumeAnalysis
OptimizedResume = resume_optimizer_module.OptimizedResume


def test_resume_optimizer_initialization():
    """Test that ResumeOptimizer can be initialized"""
    print("Testing ResumeOptimizer initialization...")
    
    llm_client = OllamaClient(model="llama3")
    db_manager = DatabaseManager("data/test_resume_optimizer.db")
    
    optimizer = ResumeOptimizer(llm_client, db_manager)
    
    assert optimizer is not None
    assert optimizer.llm_client is not None
    assert optimizer.db_manager is not None
    
    print("✓ ResumeOptimizer initialized successfully")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_resume_optimizer.db"):
        os.remove("data/test_resume_optimizer.db")


def test_extract_ats_keywords():
    """Test ATS keyword extraction"""
    print("\nTesting ATS keyword extraction...")
    
    llm_client = OllamaClient(model="llama3")
    db_manager = DatabaseManager("data/test_resume_optimizer.db")
    
    optimizer = ResumeOptimizer(llm_client, db_manager)
    
    job_description = """
    We are looking for a Senior LLM Engineer with experience in:
    - LangChain and LangGraph frameworks
    - Prompt engineering and optimization
    - RAG (Retrieval Augmented Generation) systems
    - Python and FastAPI
    - Vector databases (Pinecone, Weaviate)
    - Fine-tuning large language models
    """
    
    # Note: This will only work if Ollama is running
    try:
        keywords = optimizer.extract_ats_keywords(job_description)
        print(f"✓ Extracted {len(keywords)} keywords")
        if keywords:
            print(f"  Sample keywords: {keywords[:5]}")
    except Exception as e:
        print(f"⚠ Keyword extraction test skipped (Ollama may not be running): {e}")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_resume_optimizer.db"):
        os.remove("data/test_resume_optimizer.db")


def test_resume_version_storage():
    """Test storing and retrieving resume versions"""
    print("\nTesting resume version storage...")
    
    llm_client = OllamaClient(model="llama3")
    db_manager = DatabaseManager("data/test_resume_optimizer.db")
    db_manager.initialize_database()
    
    optimizer = ResumeOptimizer(llm_client, db_manager)
    
    # Create test user
    user_id = "test-user-123"
    resume_text = "Test resume content for version 1"
    
    # Store first version
    success = optimizer._store_resume_version(
        user_id=user_id,
        resume_text=resume_text,
        notes="Initial version"
    )
    
    assert success, "Failed to store resume version"
    print("✓ Resume version stored successfully")
    
    # Retrieve versions
    versions = optimizer.get_resume_versions(user_id)
    
    assert len(versions) > 0, "No versions retrieved"
    assert versions[0].user_id == user_id
    assert versions[0].resume_text == resume_text
    assert versions[0].version_number == 1
    
    print(f"✓ Retrieved {len(versions)} version(s)")
    print(f"  Version {versions[0].version_number}: {versions[0].optimization_notes}")
    
    # Store second version
    resume_text_v2 = "Test resume content for version 2"
    success = optimizer._store_resume_version(
        user_id=user_id,
        resume_text=resume_text_v2,
        job_id="job-123",
        notes="Optimized for specific job"
    )
    
    assert success, "Failed to store second version"
    
    # Retrieve all versions
    versions = optimizer.get_resume_versions(user_id)
    
    assert len(versions) == 2, f"Expected 2 versions, got {len(versions)}"
    assert versions[0].version_number == 2, "Latest version should be first"
    assert versions[1].version_number == 1
    
    print(f"✓ Stored and retrieved multiple versions correctly")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_resume_optimizer.db"):
        os.remove("data/test_resume_optimizer.db")


def test_data_structures():
    """Test that data structures are properly defined"""
    print("\nTesting data structures...")
    
    # Test ResumeAnalysis
    analysis = ResumeAnalysis(
        overall_score=7.5,
        strengths=["Good technical skills", "Clear experience"],
        weaknesses=["Missing keywords"],
        missing_keywords=["LangChain", "RAG"],
        present_keywords=["Python", "ML"],
        keyword_density_score=6.0
    )
    
    assert analysis.overall_score == 7.5
    assert len(analysis.strengths) == 2
    assert len(analysis.missing_keywords) == 2
    
    print("✓ ResumeAnalysis structure validated")
    
    # Test OptimizedResume
    optimized = OptimizedResume(
        job_id="job-123",
        analysis=analysis,
        ats_keywords=["Python", "LangChain", "RAG"]
    )
    
    assert optimized.job_id == "job-123"
    assert optimized.analysis.overall_score == 7.5
    assert len(optimized.ats_keywords) == 3
    
    print("✓ OptimizedResume structure validated")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Resume Optimizer Agent Tests")
    print("=" * 60)
    
    try:
        test_resume_optimizer_initialization()
        test_data_structures()
        test_resume_version_storage()
        test_extract_ats_keywords()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
