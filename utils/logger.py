"""
Logging and Error Handling Utilities
Provides centralized logging with rotating file handler and error notification system
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback


class LoggerConfig:
    """Configuration for logging system"""
    
    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    # Default settings
    DEFAULT_LOG_DIR = "logs"
    DEFAULT_LOG_FILE = "job_assistant.log"
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class AgentLogger:
    """
    Enhanced logger with context support for agent executions
    Provides rotating file handler and structured logging
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def initialize(
        cls,
        log_dir: str = LoggerConfig.DEFAULT_LOG_DIR,
        log_file: str = LoggerConfig.DEFAULT_LOG_FILE,
        level: int = LoggerConfig.INFO,
        max_bytes: int = LoggerConfig.DEFAULT_MAX_BYTES,
        backup_count: int = LoggerConfig.DEFAULT_BACKUP_COUNT,
        console_output: bool = True
    ):
        """
        Initialize the logging system with rotating file handler
        
        Args:
            log_dir: Directory for log files
            log_file: Name of the log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to also output to console
        """
        if cls._initialized:
            return
        
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            LoggerConfig.DEFAULT_FORMAT,
            datefmt=LoggerConfig.DEFAULT_DATE_FORMAT
        )
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(file_handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name
        
        Args:
            name: Name of the logger (typically module name)
            
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]
    
    @classmethod
    def log_agent_execution(
        cls,
        agent_name: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """
        Log agent execution with context
        
        Args:
            agent_name: Name of the agent
            action: Action being performed
            status: Status (started, completed, failed)
            details: Additional context details
            error: Exception if action failed
        """
        logger = cls.get_logger(agent_name)
        
        context = {
            'agent': agent_name,
            'action': action,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            context.update(details)
        
        message = f"Agent: {agent_name} | Action: {action} | Status: {status}"
        
        if details:
            detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
            message += f" | {detail_str}"
        
        if status == 'started':
            logger.info(message)
        elif status == 'completed':
            logger.info(message)
        elif status == 'failed':
            if error:
                logger.error(f"{message} | Error: {str(error)}", exc_info=True)
            else:
                logger.error(message)
        else:
            logger.warning(f"{message} | Unknown status")


class ErrorHandler:
    """
    Centralized error handling with user-friendly messages
    """
    
    # Error categories and user-friendly messages
    ERROR_MESSAGES = {
        'scraping': {
            'network_timeout': 'Unable to connect to job website. Please check your internet connection.',
            'captcha_detected': 'CAPTCHA detected. Please complete the CAPTCHA manually and try again.',
            'rate_limit': 'Too many requests. Please wait a few minutes before trying again.',
            'page_structure_changed': 'Job website structure has changed. Please contact support.',
            'login_failed': 'Login failed. Please check your credentials in Settings.',
            'default': 'Failed to fetch job listings. Please try again later.'
        },
        'llm': {
            'model_unavailable': 'AI model is not available. Please ensure Ollama is running.',
            'generation_timeout': 'AI generation took too long. Please try again.',
            'invalid_output': 'AI generated invalid response. Please try again.',
            'context_too_long': 'Input is too long. Please provide shorter content.',
            'default': 'AI processing failed. Please try again.'
        },
        'database': {
            'connection_failed': 'Database connection failed. Please restart the application.',
            'constraint_violation': 'Data already exists. Please check for duplicates.',
            'corruption': 'Database corruption detected. Attempting to restore from backup.',
            'default': 'Database error occurred. Please try again.'
        },
        'authentication': {
            'invalid_credentials': 'Invalid credentials. Please update your credentials in Settings.',
            'session_expired': 'Session expired. Please log in again.',
            'encryption_failed': 'Failed to encrypt credentials. Please contact support.',
            'default': 'Authentication error. Please check your credentials.'
        },
        'notification': {
            'email_failed': 'Failed to send email notification. Please check SMTP settings.',
            'whatsapp_failed': 'Failed to send WhatsApp notification. Please check Twilio settings.',
            'invalid_config': 'Notification settings are invalid. Please update in Settings.',
            'default': 'Failed to send notification. Please check your settings.'
        },
        'general': {
            'file_not_found': 'Required file not found. Please check the file path.',
            'permission_denied': 'Permission denied. Please check file permissions.',
            'invalid_input': 'Invalid input provided. Please check your input and try again.',
            'default': 'An unexpected error occurred. Please try again.'
        }
    }
    
    @classmethod
    def get_user_friendly_message(
        cls,
        category: str,
        error_type: str,
        technical_details: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get user-friendly error message
        
        Args:
            category: Error category (scraping, llm, database, etc.)
            error_type: Specific error type
            technical_details: Technical error details for logging
            
        Returns:
            Dictionary with user_message and technical_message
        """
        category_messages = cls.ERROR_MESSAGES.get(category, cls.ERROR_MESSAGES['general'])
        user_message = category_messages.get(error_type, category_messages['default'])
        
        return {
            'user_message': user_message,
            'technical_message': technical_details or 'No technical details available',
            'category': category,
            'error_type': error_type
        }
    
    @classmethod
    def handle_error(
        cls,
        error: Exception,
        category: str,
        error_type: str,
        context: Optional[Dict[str, Any]] = None,
        logger_name: Optional[str] = None,
        notify_user: bool = True
    ) -> Dict[str, str]:
        """
        Handle error with logging and user notification
        
        Args:
            error: The exception that occurred
            category: Error category
            error_type: Specific error type
            context: Additional context information
            logger_name: Name of logger to use
            notify_user: Whether to prepare user notification
            
        Returns:
            Dictionary with error information
        """
        logger = AgentLogger.get_logger(logger_name or 'ErrorHandler')
        
        # Get user-friendly message
        error_info = cls.get_user_friendly_message(
            category,
            error_type,
            str(error)
        )
        
        # Add context
        if context:
            error_info['context'] = context
        
        # Log the error
        log_message = f"Error [{category}/{error_type}]: {str(error)}"
        if context:
            context_str = " | ".join([f"{k}: {v}" for k, v in context.items()])
            log_message += f" | Context: {context_str}"
        
        logger.error(log_message, exc_info=True)
        
        # Add stack trace for debugging
        error_info['stack_trace'] = traceback.format_exc()
        
        return error_info
    
    @classmethod
    def handle_critical_error(
        cls,
        error: Exception,
        category: str,
        error_type: str,
        context: Optional[Dict[str, Any]] = None,
        logger_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Handle critical error that requires immediate attention
        
        Args:
            error: The exception that occurred
            category: Error category
            error_type: Specific error type
            context: Additional context information
            logger_name: Name of logger to use
            
        Returns:
            Dictionary with error information
        """
        logger = AgentLogger.get_logger(logger_name or 'ErrorHandler')
        
        # Get error info
        error_info = cls.handle_error(
            error,
            category,
            error_type,
            context,
            logger_name,
            notify_user=True
        )
        
        # Log as critical
        logger.critical(
            f"CRITICAL ERROR [{category}/{error_type}]: {str(error)}",
            exc_info=True
        )
        
        # In production, this would trigger notifications to admins
        # For now, we just mark it as critical
        error_info['severity'] = 'critical'
        
        return error_info


class RecoveryAction:
    """
    Defines recovery actions for different error types
    """
    
    RETRY = 'retry'
    SKIP = 'skip'
    FALLBACK = 'fallback'
    ABORT = 'abort'
    NOTIFY_USER = 'notify_user'
    
    @classmethod
    def get_recovery_action(cls, category: str, error_type: str) -> str:
        """
        Get recommended recovery action for error
        
        Args:
            category: Error category
            error_type: Specific error type
            
        Returns:
            Recovery action string
        """
        recovery_map = {
            'scraping': {
                'network_timeout': cls.RETRY,
                'captcha_detected': cls.NOTIFY_USER,
                'rate_limit': cls.RETRY,
                'page_structure_changed': cls.ABORT,
                'login_failed': cls.NOTIFY_USER,
                'default': cls.RETRY
            },
            'llm': {
                'model_unavailable': cls.FALLBACK,
                'generation_timeout': cls.RETRY,
                'invalid_output': cls.RETRY,
                'context_too_long': cls.SKIP,
                'default': cls.RETRY
            },
            'database': {
                'connection_failed': cls.RETRY,
                'constraint_violation': cls.SKIP,
                'corruption': cls.FALLBACK,
                'default': cls.RETRY
            },
            'authentication': {
                'invalid_credentials': cls.NOTIFY_USER,
                'session_expired': cls.RETRY,
                'encryption_failed': cls.ABORT,
                'default': cls.NOTIFY_USER
            },
            'notification': {
                'email_failed': cls.SKIP,
                'whatsapp_failed': cls.SKIP,
                'invalid_config': cls.NOTIFY_USER,
                'default': cls.SKIP
            }
        }
        
        category_actions = recovery_map.get(category, {})
        return category_actions.get(error_type, cls.RETRY)


# Convenience functions for common logging operations
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return AgentLogger.get_logger(name)


def log_agent_start(agent_name: str, action: str, details: Optional[Dict[str, Any]] = None):
    """Log agent action start"""
    AgentLogger.log_agent_execution(agent_name, action, 'started', details)


def log_agent_complete(agent_name: str, action: str, details: Optional[Dict[str, Any]] = None):
    """Log agent action completion"""
    AgentLogger.log_agent_execution(agent_name, action, 'completed', details)


def log_agent_error(agent_name: str, action: str, error: Exception, details: Optional[Dict[str, Any]] = None):
    """Log agent action failure"""
    AgentLogger.log_agent_execution(agent_name, action, 'failed', details, error)


def handle_error(
    error: Exception,
    category: str,
    error_type: str,
    context: Optional[Dict[str, Any]] = None,
    logger_name: Optional[str] = None
) -> Dict[str, str]:
    """Handle error with logging"""
    return ErrorHandler.handle_error(error, category, error_type, context, logger_name)


def handle_critical_error(
    error: Exception,
    category: str,
    error_type: str,
    context: Optional[Dict[str, Any]] = None,
    logger_name: Optional[str] = None
) -> Dict[str, str]:
    """Handle critical error"""
    return ErrorHandler.handle_critical_error(error, category, error_type, context, logger_name)
