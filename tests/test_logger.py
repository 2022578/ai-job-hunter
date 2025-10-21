"""
Tests for logging and error handling utilities
"""

import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from utils.logger import (
    AgentLogger,
    ErrorHandler,
    RecoveryAction,
    get_logger,
    log_agent_start,
    log_agent_complete,
    log_agent_error,
    handle_error,
    handle_critical_error
)


class TestAgentLogger:
    """Test AgentLogger functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        AgentLogger._initialized = False
        AgentLogger._loggers = {}
    
    def teardown_method(self):
        """Cleanup test environment"""
        if Path(self.test_log_dir).exists():
            shutil.rmtree(self.test_log_dir)
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        AgentLogger.initialize(
            log_dir=self.test_log_dir,
            log_file='test.log',
            level=logging.INFO
        )
        
        assert AgentLogger._initialized is True
        log_file = Path(self.test_log_dir) / 'test.log'
        assert log_file.exists()
    
    def test_get_logger(self):
        """Test getting logger instance"""
        AgentLogger.initialize(log_dir=self.test_log_dir)
        logger = AgentLogger.get_logger('test_agent')
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_agent'
    
    def test_log_agent_execution_started(self):
        """Test logging agent execution start"""
        AgentLogger.initialize(log_dir=self.test_log_dir)
        
        AgentLogger.log_agent_execution(
            agent_name='TestAgent',
            action='test_action',
            status='started',
            details={'param': 'value'}
        )
        
        log_file = Path(self.test_log_dir) / 'job_assistant.log'
        assert log_file.exists()
        
        log_content = log_file.read_text()
        assert 'TestAgent' in log_content
        assert 'test_action' in log_content
        assert 'started' in log_content
    
    def test_log_agent_execution_completed(self):
        """Test logging agent execution completion"""
        AgentLogger.initialize(log_dir=self.test_log_dir)
        
        AgentLogger.log_agent_execution(
            agent_name='TestAgent',
            action='test_action',
            status='completed',
            details={'result': 'success'}
        )
        
        log_file = Path(self.test_log_dir) / 'job_assistant.log'
        log_content = log_file.read_text()
        assert 'completed' in log_content
    
    def test_log_agent_execution_failed(self):
        """Test logging agent execution failure"""
        AgentLogger.initialize(log_dir=self.test_log_dir)
        
        test_error = Exception("Test error")
        AgentLogger.log_agent_execution(
            agent_name='TestAgent',
            action='test_action',
            status='failed',
            error=test_error
        )
        
        log_file = Path(self.test_log_dir) / 'job_assistant.log'
        log_content = log_file.read_text()
        assert 'failed' in log_content
        assert 'Test error' in log_content
    
    def test_convenience_functions(self):
        """Test convenience logging functions"""
        AgentLogger.initialize(log_dir=self.test_log_dir)
        
        log_agent_start('TestAgent', 'test_action')
        log_agent_complete('TestAgent', 'test_action')
        log_agent_error('TestAgent', 'test_action', Exception("Test error"))
        
        log_file = Path(self.test_log_dir) / 'job_assistant.log'
        log_content = log_file.read_text()
        assert 'started' in log_content
        assert 'completed' in log_content
        assert 'failed' in log_content


class TestErrorHandler:
    """Test ErrorHandler functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        AgentLogger._initialized = False
        AgentLogger.initialize(log_dir=self.test_log_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if Path(self.test_log_dir).exists():
            shutil.rmtree(self.test_log_dir)
    
    def test_get_user_friendly_message_scraping(self):
        """Test getting user-friendly message for scraping errors"""
        error_info = ErrorHandler.get_user_friendly_message(
            category='scraping',
            error_type='network_timeout'
        )
        
        assert 'user_message' in error_info
        assert 'technical_message' in error_info
        assert 'internet connection' in error_info['user_message'].lower()
    
    def test_get_user_friendly_message_llm(self):
        """Test getting user-friendly message for LLM errors"""
        error_info = ErrorHandler.get_user_friendly_message(
            category='llm',
            error_type='model_unavailable'
        )
        
        assert 'Ollama' in error_info['user_message']
    
    def test_get_user_friendly_message_database(self):
        """Test getting user-friendly message for database errors"""
        error_info = ErrorHandler.get_user_friendly_message(
            category='database',
            error_type='connection_failed'
        )
        
        assert 'Database' in error_info['user_message']
    
    def test_get_user_friendly_message_default(self):
        """Test getting default message for unknown error type"""
        error_info = ErrorHandler.get_user_friendly_message(
            category='unknown_category',
            error_type='unknown_type'
        )
        
        assert 'unexpected error' in error_info['user_message'].lower()
    
    def test_handle_error(self):
        """Test error handling"""
        test_error = Exception("Test error message")
        error_info = ErrorHandler.handle_error(
            error=test_error,
            category='scraping',
            error_type='network_timeout',
            context={'url': 'https://example.com'}
        )
        
        assert 'user_message' in error_info
        assert 'technical_message' in error_info
        assert 'context' in error_info
        assert 'stack_trace' in error_info
        assert error_info['context']['url'] == 'https://example.com'
    
    def test_handle_critical_error(self):
        """Test critical error handling"""
        test_error = Exception("Critical error")
        error_info = ErrorHandler.handle_critical_error(
            error=test_error,
            category='database',
            error_type='corruption'
        )
        
        assert error_info['severity'] == 'critical'
        assert 'user_message' in error_info
    
    def test_handle_error_convenience_function(self):
        """Test convenience error handling function"""
        test_error = Exception("Test error")
        error_info = handle_error(
            error=test_error,
            category='llm',
            error_type='generation_timeout'
        )
        
        assert 'user_message' in error_info
        assert 'took too long' in error_info['user_message'].lower()


class TestRecoveryAction:
    """Test RecoveryAction functionality"""
    
    def test_get_recovery_action_scraping_timeout(self):
        """Test recovery action for scraping timeout"""
        action = RecoveryAction.get_recovery_action('scraping', 'network_timeout')
        assert action == RecoveryAction.RETRY
    
    def test_get_recovery_action_scraping_captcha(self):
        """Test recovery action for CAPTCHA detection"""
        action = RecoveryAction.get_recovery_action('scraping', 'captcha_detected')
        assert action == RecoveryAction.NOTIFY_USER
    
    def test_get_recovery_action_llm_unavailable(self):
        """Test recovery action for LLM unavailable"""
        action = RecoveryAction.get_recovery_action('llm', 'model_unavailable')
        assert action == RecoveryAction.FALLBACK
    
    def test_get_recovery_action_database_constraint(self):
        """Test recovery action for database constraint violation"""
        action = RecoveryAction.get_recovery_action('database', 'constraint_violation')
        assert action == RecoveryAction.SKIP
    
    def test_get_recovery_action_authentication_invalid(self):
        """Test recovery action for invalid credentials"""
        action = RecoveryAction.get_recovery_action('authentication', 'invalid_credentials')
        assert action == RecoveryAction.NOTIFY_USER
    
    def test_get_recovery_action_default(self):
        """Test default recovery action"""
        action = RecoveryAction.get_recovery_action('unknown', 'unknown')
        assert action == RecoveryAction.RETRY


class TestLoggingIntegration:
    """Test logging integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_log_dir = tempfile.mkdtemp()
        AgentLogger._initialized = False
        AgentLogger.initialize(log_dir=self.test_log_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if Path(self.test_log_dir).exists():
            shutil.rmtree(self.test_log_dir)
    
    def test_agent_workflow_logging(self):
        """Test logging for complete agent workflow"""
        agent_name = 'JobSearchAgent'
        
        # Start
        log_agent_start(agent_name, 'search_jobs', {'keywords': ['GenAI']})
        
        # Complete
        log_agent_complete(agent_name, 'search_jobs', {'jobs_found': 5})
        
        # Verify logs
        log_file = Path(self.test_log_dir) / 'job_assistant.log'
        log_content = log_file.read_text()
        
        assert 'JobSearchAgent' in log_content
        assert 'search_jobs' in log_content
        assert 'started' in log_content
        assert 'completed' in log_content
    
    def test_error_handling_workflow(self):
        """Test error handling workflow"""
        try:
            # Simulate an error
            raise ValueError("Invalid input")
        except Exception as e:
            error_info = handle_error(
                e,
                category='general',
                error_type='invalid_input',
                context={'input': 'test_value'}
            )
            
            assert 'user_message' in error_info
            assert 'Invalid input' in error_info['user_message']
            
            # Verify error was logged
            log_file = Path(self.test_log_dir) / 'job_assistant.log'
            log_content = log_file.read_text()
            assert 'Invalid input' in log_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
