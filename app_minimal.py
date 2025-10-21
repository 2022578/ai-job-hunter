"""
Minimal Streamlit App for Testing
"""
import sys
sys.setrecursionlimit(5000)

import streamlit as st

st.set_page_config(
    page_title='GenAI Job Assistant - Test',
    page_icon='🤖',
    layout='wide'
)

st.title("🤖 GenAI Job Assistant - Minimal Test")
st.write("If you can see this, the basic Streamlit app works!")

try:
    from utils.logger import AgentLogger, LoggerConfig
    AgentLogger.initialize(
        log_dir='logs',
        log_file='job_assistant.log',
        level=LoggerConfig.INFO,
        console_output=False
    )
    st.success("✓ Logger initialized successfully")
except Exception as e:
    st.error(f"✗ Logger initialization failed: {e}")

try:
    from database.db_manager import DatabaseManager
    db_manager = DatabaseManager('data/job_assistant.db')
    st.success("✓ Database manager created successfully")
except Exception as e:
    st.error(f"✗ Database manager creation failed: {e}")

try:
    from database.repositories.job_repository import JobRepository
    job_repo = JobRepository(db_manager)
    jobs = job_repo.find_all()
    st.success(f"✓ Job repository works - found {len(jobs)} jobs")
except Exception as e:
    st.error(f"✗ Job repository failed: {e}")

st.info("If all checks passed, your full app should work. Try running: streamlit run app.py")
