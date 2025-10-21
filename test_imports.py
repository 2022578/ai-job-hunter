"""
Test script to isolate import issues
"""
import sys
sys.setrecursionlimit(1000)

print("Testing imports...")

try:
    print("1. Importing streamlit...")
    import streamlit as st
    print("   ✓ streamlit imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("2. Importing yaml...")
    import yaml
    print("   ✓ yaml imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("3. Importing logger...")
    from utils.logger import AgentLogger, LoggerConfig
    print("   ✓ logger imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("4. Importing DatabaseManager...")
    from database.db_manager import DatabaseManager
    print("   ✓ DatabaseManager imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("5. Importing repositories...")
    from database.repositories.job_repository import JobRepository
    from database.repositories.application_repository import ApplicationRepository
    print("   ✓ repositories imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("6. Importing UI pages...")
    from ui.pages.dashboard import render_dashboard
    print("   ✓ dashboard imported")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {str(e)[:100]}")

print("\nAll imports completed!")
