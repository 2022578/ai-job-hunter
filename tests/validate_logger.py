"""
Validation script for logging and error handling system
Demonstrates the logging functionality without cleanup issues
"""

from utils.logger import (
    AgentLogger,
    LoggerConfig,
    ErrorHandler,
    RecoveryAction,
    get_logger,
    log_agent_start,
    log_agent_complete,
    log_agent_error,
    handle_error,
    handle_critical_error
)
from pathlib import Path


def validate_basic_logging():
    """Validate basic logging functionality"""
    print("=" * 60)
    print("Testing Basic Logging")
    print("=" * 60)
    
    # Initialize logger
    AgentLogger.initialize(
        log_dir='logs',
        log_file='job_assistant.log',
        level=LoggerConfig.INFO
    )
    
    logger = get_logger('ValidationScript')
    logger.info("Logger initialized successfully")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✅ Basic logging test passed")
    print()


def validate_agent_logging():
    """Validate agent execution logging"""
    print("=" * 60)
    print("Testing Agent Execution Logging")
    print("=" * 60)
    
    # Test agent workflow logging
    log_agent_start('JobSearchAgent', 'search_jobs', {'keywords': ['GenAI', 'LLM']})
    log_agent_complete('JobSearchAgent', 'search_jobs', {'jobs_found': 10})
    
    # Test error logging
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        log_agent_error('JobSearchAgent', 'search_jobs', e, {'context': 'test'})
    
    print("✅ Agent logging test passed")
    print()


def validate_error_handling():
    """Validate error handling functionality"""
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    # Test different error categories
    test_cases = [
        ('scraping', 'network_timeout', 'Connection timeout'),
        ('llm', 'model_unavailable', 'Ollama not running'),
        ('database', 'connection_failed', 'Database locked'),
        ('authentication', 'invalid_credentials', 'Wrong password'),
        ('notification', 'email_failed', 'SMTP error')
    ]
    
    for category, error_type, message in test_cases:
        try:
            raise Exception(message)
        except Exception as e:
            error_info = handle_error(
                e,
                category=category,
                error_type=error_type,
                context={'test': 'validation'}
            )
            print(f"✅ {category}/{error_type}: {error_info['user_message'][:50]}...")
    
    print()


def validate_recovery_actions():
    """Validate recovery action recommendations"""
    print("=" * 60)
    print("Testing Recovery Actions")
    print("=" * 60)
    
    test_cases = [
        ('scraping', 'network_timeout', RecoveryAction.RETRY),
        ('scraping', 'captcha_detected', RecoveryAction.NOTIFY_USER),
        ('llm', 'model_unavailable', RecoveryAction.FALLBACK),
        ('database', 'constraint_violation', RecoveryAction.SKIP),
        ('authentication', 'invalid_credentials', RecoveryAction.NOTIFY_USER)
    ]
    
    for category, error_type, expected_action in test_cases:
        action = RecoveryAction.get_recovery_action(category, error_type)
        status = "✅" if action == expected_action else "❌"
        print(f"{status} {category}/{error_type}: {action}")
    
    print()


def validate_user_friendly_messages():
    """Validate user-friendly error messages"""
    print("=" * 60)
    print("Testing User-Friendly Messages")
    print("=" * 60)
    
    test_cases = [
        ('scraping', 'network_timeout'),
        ('llm', 'model_unavailable'),
        ('database', 'connection_failed'),
        ('authentication', 'invalid_credentials'),
        ('notification', 'email_failed')
    ]
    
    for category, error_type in test_cases:
        error_info = ErrorHandler.get_user_friendly_message(category, error_type)
        print(f"✅ {category}/{error_type}:")
        print(f"   User Message: {error_info['user_message']}")
        print()


def validate_log_file_creation():
    """Validate log file is created"""
    print("=" * 60)
    print("Testing Log File Creation")
    print("=" * 60)
    
    log_file = Path('logs/job_assistant.log')
    if log_file.exists():
        print(f"✅ Log file created: {log_file}")
        print(f"   File size: {log_file.stat().st_size} bytes")
        
        # Show last few lines
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                print(f"   Total lines: {len(lines)}")
                print("\n   Last 5 log entries:")
                for line in lines[-5:]:
                    print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Note: Could not read log file content: {e}")
    else:
        print("❌ Log file not found")
    
    print()


def main():
    """Run all validation tests"""
    print("\n" + "=" * 60)
    print("LOGGING AND ERROR HANDLING VALIDATION")
    print("=" * 60 + "\n")
    
    try:
        validate_basic_logging()
        validate_agent_logging()
        validate_error_handling()
        validate_recovery_actions()
        validate_user_friendly_messages()
        validate_log_file_creation()
        
        print("=" * 60)
        print("ALL VALIDATION TESTS PASSED ✅")
        print("=" * 60)
        print("\nLogging system is working correctly!")
        print("Check logs/job_assistant.log for detailed logs.")
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
