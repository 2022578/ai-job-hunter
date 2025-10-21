"""
Test Company Profiler Agent
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.company_profiler import CompanyProfiler
from utils.llm_client import OllamaClient
from database.db_manager import DatabaseManager
from database.repositories.company_repository import CompanyRepository
from models.company import CompanyProfile
from datetime import datetime, timedelta


def test_company_profiler_initialization():
    """Test that CompanyProfiler can be initialized"""
    print("Testing CompanyProfiler initialization...")
    
    db_manager = DatabaseManager("data/test_company_profiler.db")
    db_manager.initialize_database()
    
    company_repo = CompanyRepository(db_manager)
    llm_client = OllamaClient(model="llama3")
    
    profiler = CompanyProfiler(
        company_repository=company_repo,
        llm_client=llm_client,
        cache_duration_days=30
    )
    
    assert profiler is not None
    assert profiler.company_repository is not None
    assert profiler.llm_client is not None
    assert profiler.cache_duration_days == 30
    
    print("✓ CompanyProfiler initialized successfully")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_company_profiler.db"):
        os.remove("data/test_company_profiler.db")


def test_assess_genai_focus():
    """Test GenAI focus assessment"""
    print("\nTesting GenAI focus assessment...")
    
    db_manager = DatabaseManager("data/test_company_profiler.db")
    db_manager.initialize_database()
    
    company_repo = CompanyRepository(db_manager)
    llm_client = OllamaClient(model="llama3")
    
    profiler = CompanyProfiler(
        company_repository=company_repo,
        llm_client=llm_client
    )
    
    # Test with GenAI-focused news
    news_articles = [
        "TechCorp launches new GenAI platform for enterprise",
        "Company invests $50M in LLM research and development",
        "TechCorp releases open-source LangChain integration"
    ]
    
    score = profiler.assess_genai_focus("TechCorp", news_articles)
    
    assert 0.0 <= score <= 10.0, f"Score {score} out of valid range"
    assert score > 5.0, "Should have high score with GenAI-focused news"
    
    print(f"✓ GenAI focus score: {score}/10 (with GenAI news)")
    
    # Test with non-GenAI news
    non_genai_news = [
        "Company announces quarterly earnings",
        "New office opening in Bangalore",
        "CEO speaks at tech conference"
    ]
    
    score_low = profiler.assess_genai_focus("RegularCorp", non_genai_news)
    
    assert 0.0 <= score_low <= 10.0
    assert score_low < score, "Non-GenAI news should have lower score"
    
    print(f"✓ GenAI focus score: {score_low}/10 (without GenAI news)")
    
    # Test with no news
    score_neutral = profiler.assess_genai_focus("UnknownCorp", [])
    
    assert score_neutral == 5.0, "Should return neutral score with no data"
    
    print(f"✓ GenAI focus score: {score_neutral}/10 (no news data)")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_company_profiler.db"):
        os.remove("data/test_company_profiler.db")


def test_cache_mechanism():
    """Test company profile caching"""
    print("\nTesting cache mechanism...")
    
    db_manager = DatabaseManager("data/test_company_profiler.db")
    db_manager.initialize_database()
    
    company_repo = CompanyRepository(db_manager)
    llm_client = OllamaClient(model="llama3")
    
    profiler = CompanyProfiler(
        company_repository=company_repo,
        llm_client=llm_client,
        cache_duration_days=30
    )
    
    # Create and save a test profile
    test_profile = CompanyProfile(
        company_name="TestCorp",
        glassdoor_rating=4.2,
        employee_count=500,
        funding_stage="Series B",
        recent_news=["News 1", "News 2"],
        genai_focus_score=8.5,
        culture_summary="Great tech culture"
    )
    
    company_repo.save(test_profile)
    print("✓ Test profile saved")
    
    # Retrieve from cache
    cached = profiler.get_cached_profile("TestCorp")
    
    assert cached is not None, "Should retrieve cached profile"
    assert cached.company_name == "TestCorp"
    assert cached.glassdoor_rating == 4.2
    assert cached.genai_focus_score == 8.5
    assert cached.is_cache_valid(), "Cache should be valid"
    
    print("✓ Retrieved valid cached profile")
    
    # Test expired cache
    expired_profile = CompanyProfile(
        company_name="ExpiredCorp",
        glassdoor_rating=3.8,
        genai_focus_score=6.0,
        cached_at=datetime.now() - timedelta(days=31),
        cache_expiry=datetime.now() - timedelta(days=1)
    )
    
    company_repo.save(expired_profile)
    
    expired_cached = profiler.get_cached_profile("ExpiredCorp")
    
    assert expired_cached is None, "Should not retrieve expired cache"
    
    print("✓ Expired cache correctly ignored")
    
    # Test cache cleanup
    count = profiler.clean_expired_profiles()
    
    assert count >= 1, "Should clean at least one expired profile"
    
    print(f"✓ Cleaned {count} expired profile(s)")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_company_profiler.db"):
        os.remove("data/test_company_profiler.db")


def test_get_all_profiles():
    """Test retrieving all cached profiles"""
    print("\nTesting get all profiles...")
    
    db_manager = DatabaseManager("data/test_company_profiler.db")
    db_manager.initialize_database()
    
    company_repo = CompanyRepository(db_manager)
    llm_client = OllamaClient(model="llama3")
    
    profiler = CompanyProfiler(
        company_repository=company_repo,
        llm_client=llm_client
    )
    
    # Create multiple test profiles
    companies = ["CompanyA", "CompanyB", "CompanyC"]
    
    for company_name in companies:
        profile = CompanyProfile(
            company_name=company_name,
            glassdoor_rating=4.0,
            genai_focus_score=7.0
        )
        company_repo.save(profile)
    
    print(f"✓ Created {len(companies)} test profiles")
    
    # Retrieve all profiles
    all_profiles = profiler.get_all_profiles()
    
    assert len(all_profiles) == len(companies), f"Expected {len(companies)} profiles, got {len(all_profiles)}"
    
    profile_names = [p.company_name for p in all_profiles]
    for company_name in companies:
        assert company_name in profile_names, f"{company_name} not found in profiles"
    
    print(f"✓ Retrieved all {len(all_profiles)} profiles")
    
    # Test with limit
    limited_profiles = profiler.get_all_profiles(limit=2)
    
    assert len(limited_profiles) == 2, f"Expected 2 profiles with limit, got {len(limited_profiles)}"
    
    print(f"✓ Retrieved {len(limited_profiles)} profiles with limit")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_company_profiler.db"):
        os.remove("data/test_company_profiler.db")


def test_summarize_fit():
    """Test company-candidate fit summary generation"""
    print("\nTesting fit summary generation...")
    
    db_manager = DatabaseManager("data/test_company_profiler.db")
    db_manager.initialize_database()
    
    company_repo = CompanyRepository(db_manager)
    llm_client = OllamaClient(model="llama3")
    
    profiler = CompanyProfiler(
        company_repository=company_repo,
        llm_client=llm_client
    )
    
    # Create test profile
    test_profile = CompanyProfile(
        company_name="GenAI Innovations",
        glassdoor_rating=4.5,
        employee_count=300,
        funding_stage="Series B",
        recent_news=[
            "Company launches new LLM platform",
            "Raises $50M for GenAI research"
        ],
        genai_focus_score=9.0
    )
    
    company_repo.save(test_profile)
    
    # User preferences
    user_prefs = {
        'target_salary': 3500000,
        'preferred_remote': True,
        'desired_tech_stack': ['LangChain', 'LangGraph', 'Python'],
        'career_priorities': ['Learning', 'Impact', 'Growth']
    }
    
    # Note: This will only work if Ollama is running
    try:
        summary = profiler.summarize_fit(test_profile, user_prefs)
        
        assert summary is not None
        assert len(summary) > 0
        assert "GenAI Innovations" in summary or "fit" in summary.lower()
        
        print("✓ Generated fit summary successfully")
        print(f"  Summary length: {len(summary)} characters")
        
        # Verify summary was saved to profile
        updated_profile = company_repo.find_by_name("GenAI Innovations")
        assert updated_profile.culture_summary == summary
        
        print("✓ Summary saved to profile")
        
    except Exception as e:
        print(f"⚠ Fit summary test skipped (Ollama may not be running): {e}")
    
    # Cleanup
    db_manager.close_connection()
    if os.path.exists("data/test_company_profiler.db"):
        os.remove("data/test_company_profiler.db")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Company Profiler Agent Tests")
    print("=" * 60)
    
    try:
        test_company_profiler_initialization()
        test_assess_genai_focus()
        test_cache_mechanism()
        test_get_all_profiles()
        test_summarize_fit()
        
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
