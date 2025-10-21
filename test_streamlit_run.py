"""
Test Streamlit app initialization without actually running the server
"""
import sys
sys.setrecursionlimit(5000)

print("Testing Streamlit app initialization...")

try:
    # Import app module
    import app
    print("✓ App module imported")
    
    # Try to initialize the logger
    from utils.logger import AgentLogger, LoggerConfig
    AgentLogger.initialize(
        log_dir='logs',
        log_file='test_job_assistant.log',
        level=LoggerConfig.INFO,
        console_output=False
    )
    print("✓ Logger initialized")
    
    # Try to initialize database
    from database.db_manager import DatabaseManager
    db_manager = DatabaseManager('data/job_assistant.db')
    print("✓ Database manager created")
    
    # Try to load config
    config = app.load_config()
    print(f"✓ Config loaded: {len(config)} keys")
    
    print("\n✅ All initialization tests passed!")
    
except RecursionError as e:
    print(f"\n❌ RecursionError occurred: {e}")
    import traceback
    print("\nPartial traceback (last 10 frames):")
    tb_lines = traceback.format_exc().split('\n')
    for line in tb_lines[-20:]:
        print(line)
        
except Exception as e:
    print(f"\n❌ Error occurred: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
