# Logging and Error Handling System

## Overview

The GenAI Job Assistant includes a comprehensive logging and error handling system that provides:

- **Rotating file handler** for automatic log file management
- **Context-aware logging** for agent executions
- **User-friendly error messages** for UI display
- **Recovery action recommendations** for different error types
- **Structured error handling** with categorization

## Components

### 1. AgentLogger

Centralized logger with rotating file handler support.

**Features:**
- Automatic log file rotation (10 MB max size, 5 backup files)
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Console and file output
- Context logging for agent executions

**Usage:**

```python
from utils.logger import AgentLogger, get_logger

# Initialize logging system (done once at app startup)
AgentLogger.initialize(
    log_dir='logs',
    log_file='job_assistant.log',
    level=LoggerConfig.INFO,
    console_output=True
)

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Processing started")
logger.error("An error occurred", exc_info=True)
```

### 2. Agent Execution Logging

Special logging for agent workflows with context.

**Usage:**

```python
from utils.logger import log_agent_start, log_agent_complete, log_agent_error

# Log agent start
log_agent_start('JobSearchAgent', 'search_jobs', {
    'keywords': ['GenAI', 'LLM'],
    'salary_min': 35
})

# Log agent completion
log_agent_complete('JobSearchAgent', 'search_jobs', {
    'jobs_found': 10,
    'duration': '5.2s'
})

# Log agent error
try:
    # Agent logic here
    pass
except Exception as e:
    log_agent_error('JobSearchAgent', 'search_jobs', e, {
        'context': 'additional info'
    })
```

### 3. ErrorHandler

Provides user-friendly error messages and categorization.

**Error Categories:**
- `scraping`: Web scraping errors (network, CAPTCHA, rate limits)
- `llm`: LLM-related errors (model unavailable, timeout, invalid output)
- `database`: Database errors (connection, corruption, constraints)
- `authentication`: Auth errors (invalid credentials, session expired)
- `notification`: Notification errors (email failed, WhatsApp failed)
- `general`: General errors (file not found, permission denied)

**Usage:**

```python
from utils.logger import handle_error, handle_critical_error

try:
    # Your code here
    scrape_jobs()
except Exception as e:
    error_info = handle_error(
        error=e,
        category='scraping',
        error_type='network_timeout',
        context={'url': 'https://example.com'},
        logger_name=__name__
    )
    
    # error_info contains:
    # - user_message: User-friendly message
    # - technical_message: Technical details
    # - category: Error category
    # - error_type: Specific error type
    # - context: Additional context
    # - stack_trace: Full stack trace
```

### 4. RecoveryAction

Recommends recovery actions for different error types.

**Recovery Actions:**
- `RETRY`: Retry the operation
- `SKIP`: Skip and continue
- `FALLBACK`: Use alternative method
- `ABORT`: Stop operation
- `NOTIFY_USER`: Require user action

**Usage:**

```python
from utils.logger import RecoveryAction

action = RecoveryAction.get_recovery_action('scraping', 'network_timeout')
# Returns: 'retry'

if action == RecoveryAction.RETRY:
    # Implement retry logic
    pass
elif action == RecoveryAction.NOTIFY_USER:
    # Show message to user
    pass
```

### 5. UI Helpers

Streamlit-specific helpers for displaying errors in the UI.

**Usage:**

```python
from utils.ui_helpers import display_error, display_success, display_agent_status

# Display error with user-friendly message
try:
    # Your code
    pass
except Exception as e:
    error_info = handle_error(e, 'llm', 'model_unavailable')
    display_error(error_info, show_technical_details=True)

# Display success message
display_success("Resume optimized successfully!")

# Display agent status
display_agent_status('JobSearchAgent', 'completed', {'jobs_found': 10})
```

## Error Message Examples

### Scraping Errors

| Error Type | User Message |
|------------|--------------|
| `network_timeout` | Unable to connect to job website. Please check your internet connection. |
| `captcha_detected` | CAPTCHA detected. Please complete the CAPTCHA manually and try again. |
| `rate_limit` | Too many requests. Please wait a few minutes before trying again. |
| `login_failed` | Login failed. Please check your credentials in Settings. |

### LLM Errors

| Error Type | User Message |
|------------|--------------|
| `model_unavailable` | AI model is not available. Please ensure Ollama is running. |
| `generation_timeout` | AI generation took too long. Please try again. |
| `invalid_output` | AI generated invalid response. Please try again. |
| `context_too_long` | Input is too long. Please provide shorter content. |

### Database Errors

| Error Type | User Message |
|------------|--------------|
| `connection_failed` | Database connection failed. Please restart the application. |
| `constraint_violation` | Data already exists. Please check for duplicates. |
| `corruption` | Database corruption detected. Attempting to restore from backup. |

## Configuration

### Log Levels

```python
from utils.logger import LoggerConfig

# Available log levels
LoggerConfig.DEBUG    # Detailed debugging information
LoggerConfig.INFO     # General informational messages
LoggerConfig.WARNING  # Warning messages
LoggerConfig.ERROR    # Error messages
LoggerConfig.CRITICAL # Critical errors
```

### Log File Settings

```python
AgentLogger.initialize(
    log_dir='logs',                    # Log directory
    log_file='job_assistant.log',      # Log file name
    level=LoggerConfig.INFO,           # Minimum log level
    max_bytes=10 * 1024 * 1024,       # Max file size (10 MB)
    backup_count=5,                    # Number of backup files
    console_output=True                # Also log to console
)
```

## Best Practices

### 1. Initialize Once

Initialize the logging system once at application startup (in `app.py`):

```python
from utils.logger import AgentLogger, LoggerConfig

AgentLogger.initialize(
    log_dir='logs',
    log_file='job_assistant.log',
    level=LoggerConfig.INFO
)
```

### 2. Use Module-Level Loggers

Create a logger for each module:

```python
from utils.logger import get_logger

logger = get_logger(__name__)
```

### 3. Log Agent Workflows

Use agent-specific logging for workflows:

```python
from utils.logger import log_agent_start, log_agent_complete, log_agent_error

log_agent_start('AgentName', 'action_name', {'param': 'value'})
# ... agent logic ...
log_agent_complete('AgentName', 'action_name', {'result': 'success'})
```

### 4. Handle Errors Gracefully

Always provide context when handling errors:

```python
from utils.logger import handle_error

try:
    # Your code
    pass
except Exception as e:
    error_info = handle_error(
        e,
        category='appropriate_category',
        error_type='specific_error_type',
        context={'relevant': 'context'},
        logger_name=__name__
    )
    # Display error to user or take recovery action
```

### 5. Use UI Helpers in Streamlit

Display errors in a user-friendly way:

```python
from utils.ui_helpers import display_error

try:
    # Your code
    pass
except Exception as e:
    error_info = handle_error(e, 'category', 'error_type')
    display_error(error_info)
```

## Log File Location

Logs are stored in: `logs/job_assistant.log`

Backup files: `logs/job_assistant.log.1`, `logs/job_assistant.log.2`, etc.

## Testing

Run the validation script to test the logging system:

```bash
python tests/validate_logger.py
```

Run unit tests:

```bash
pytest tests/test_logger.py -v
```

## Troubleshooting

### Log File Not Created

Ensure the `logs` directory exists or the application has permission to create it.

### Log File Too Large

Adjust the `max_bytes` parameter when initializing:

```python
AgentLogger.initialize(
    max_bytes=5 * 1024 * 1024,  # 5 MB instead of 10 MB
    backup_count=3               # Keep fewer backups
)
```

### Missing Log Entries

Check the log level - DEBUG messages won't appear if level is set to INFO:

```python
AgentLogger.initialize(level=LoggerConfig.DEBUG)
```

## Integration with Existing Code

The logging system is already integrated into:

- `app.py`: Main application error handling
- All agent modules: Agent execution logging
- UI pages: Error display in Streamlit

To add logging to new modules:

```python
from utils.logger import get_logger, handle_error

logger = get_logger(__name__)

def my_function():
    try:
        logger.info("Starting operation")
        # Your code
        logger.info("Operation completed")
    except Exception as e:
        error_info = handle_error(e, 'category', 'error_type')
        logger.error(f"Operation failed: {e}")
        raise
```

## Requirements

The logging system satisfies **Requirement 11.5**:
- ✅ Rotating file handler for log management
- ✅ Multiple log levels (DEBUG, INFO, ERROR)
- ✅ Context logging for agent executions
- ✅ Error notification system for critical failures
- ✅ User-friendly error messages in UI
