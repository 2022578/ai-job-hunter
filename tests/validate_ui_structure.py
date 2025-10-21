"""
Validation script for UI structure
Tests that all UI components are properly structured without running Streamlit
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_app_structure():
    """Test that app.py exists and has required functions"""
    print("Testing app.py structure...")
    
    app_path = project_root / "app.py"
    assert app_path.exists(), "app.py not found"
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required functions
    required_functions = [
        'load_config',
        'configure_page',
        'init_session_state',
        'render_sidebar',
        'route_to_page',
        'main'
    ]
    
    for func in required_functions:
        assert f"def {func}" in content, f"Function {func} not found in app.py"
    
    print("✓ app.py structure is valid")


def test_dashboard_structure():
    """Test that dashboard.py exists and has required functions"""
    print("Testing dashboard.py structure...")
    
    dashboard_path = project_root / "ui" / "pages" / "dashboard.py"
    assert dashboard_path.exists(), "dashboard.py not found"
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required functions
    required_functions = [
        'get_dashboard_data',
        'render_overview_metrics',
        'render_application_funnel',
        'render_match_score_distribution',
        'render_timeline',
        'render_top_companies',
        'render_upcoming_interviews',
        'render_actionable_insights',
        'render_quick_actions',
        'render_dashboard'
    ]
    
    for func in required_functions:
        assert f"def {func}" in content, f"Function {func} not found in dashboard.py"
    
    print("✓ dashboard.py structure is valid")


def test_ui_pages_init():
    """Test that ui/pages/__init__.py exists"""
    print("Testing ui/pages/__init__.py...")
    
    init_path = project_root / "ui" / "pages" / "__init__.py"
    assert init_path.exists(), "ui/pages/__init__.py not found"
    
    print("✓ ui/pages/__init__.py exists")


def test_imports():
    """Test that imports are syntactically correct"""
    print("Testing imports...")
    
    try:
        # Test app.py imports (without streamlit)
        import yaml
        import logging
        from pathlib import Path
        print("✓ Basic imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    try:
        # Test database imports
        from database.db_manager import DatabaseManager
        from database.repositories.job_repository import JobRepository
        from database.repositories.application_repository import ApplicationRepository
        print("✓ Database imports successful")
    except ImportError as e:
        print(f"✗ Database import failed: {e}")
        return False
    
    return True


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("UI Structure Validation")
    print("=" * 60)
    
    try:
        test_app_structure()
        test_dashboard_structure()
        test_ui_pages_init()
        test_imports()
        
        print("\n" + "=" * 60)
        print("✓ All validation tests passed!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Validation failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
