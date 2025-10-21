"""
Configuration Manager for GenAI Job Assistant
Handles loading, validation, and management of application configuration
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration settings"""
    provider: str = "ollama"
    model_name: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


@dataclass
class JobSearchConfig:
    """Job search configuration settings"""
    keywords: List[str] = field(default_factory=lambda: ["GenAI", "LLM", "Autonomous Agents", "LangChain", "LangGraph"])
    min_salary: int = 3500000
    preferred_locations: List[str] = field(default_factory=lambda: ["Bangalore", "Remote"])
    remote_preference: bool = True
    search_schedule: str = "0 9 * * *"


@dataclass
class ScrapingConfig:
    """Web scraping configuration settings"""
    naukri_enabled: bool = True
    rate_limit_delay: int = 2
    max_retries: int = 3
    timeout: int = 30
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ])


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    type: str = "sqlite"
    path: str = "data/job_assistant.db"
    backup_enabled: bool = True
    backup_schedule: str = "0 0 * * *"
    backup_retention_days: int = 30


@dataclass
class EmailConfig:
    """Email notification configuration"""
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_address: str = ""
    to_address: str = ""


@dataclass
class WhatsAppConfig:
    """WhatsApp notification configuration"""
    enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    user_whatsapp_number: str = ""


@dataclass
class NotificationPreferencesConfig:
    """Notification preferences"""
    daily_digest: bool = True
    digest_time: str = "09:00"
    interview_reminders: bool = True
    status_updates: bool = True


@dataclass
class NotificationConfig:
    """Notification configuration settings"""
    email: EmailConfig = field(default_factory=EmailConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    preferences: NotificationPreferencesConfig = field(default_factory=NotificationPreferencesConfig)


@dataclass
class UserConfig:
    """User profile configuration"""
    name: str = "[Your Name]"
    email: str = "[your-email@example.com]"
    experience_years: int = 0
    target_salary: int = 3500000
    skills: List[str] = field(default_factory=lambda: ["Python", "LangChain", "GenAI"])
    desired_tech_stack: List[str] = field(default_factory=lambda: ["LangChain", "LangGraph", "OpenAI", "Ollama"])


@dataclass
class ScoringConfig:
    """Match scoring weights configuration"""
    skills_match_weight: float = 0.35
    salary_match_weight: float = 0.25
    tech_stack_match_weight: float = 0.20
    remote_flexibility_weight: float = 0.10
    company_profile_weight: float = 0.10


@dataclass
class CompanyProfilingConfig:
    """Company profiling configuration"""
    cache_duration_days: int = 30
    glassdoor_enabled: bool = False
    news_api_enabled: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key_env_var: str = "JOB_ASSISTANT_ENCRYPTION_KEY"
    credential_storage: str = "database"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "logs/job_assistant.log"
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class UIConfig:
    """UI configuration"""
    theme: str = "light"
    page_title: str = "GenAI Job Assistant"
    page_icon: str = "🤖"
    layout: str = "wide"


@dataclass
class AppConfig:
    """Complete application configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    job_search: JobSearchConfig = field(default_factory=JobSearchConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    user: UserConfig = field(default_factory=UserConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    company_profiling: CompanyProfilingConfig = field(default_factory=CompanyProfilingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config: Optional[AppConfig] = None
        self._raw_config: Dict[str, Any] = {}
    
    def load_config(self) -> AppConfig:
        """
        Load configuration from file
        
        Returns:
            AppConfig object
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Check if config file exists
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file not found: {self.config_path}")
                logger.info("Generating default configuration...")
                self.generate_default_config()
            
            # Load YAML file
            with open(self.config_path, 'r') as f:
                self._raw_config = yaml.safe_load(f)
            
            # Parse configuration
            self.config = self._parse_config(self._raw_config)
            
            # Validate configuration
            self.validate_config()
            
            logger.info(f"Configuration loaded successfully from: {self.config_path}")
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _parse_config(self, raw_config: Dict[str, Any]) -> AppConfig:
        """
        Parse raw configuration dictionary into AppConfig object
        
        Args:
            raw_config: Raw configuration dictionary
            
        Returns:
            AppConfig object
        """
        config = AppConfig()
        
        # Parse LLM config
        if 'llm' in raw_config:
            llm_data = raw_config['llm']
            config.llm = LLMConfig(
                provider=llm_data.get('provider', 'ollama'),
                model_name=llm_data.get('model_name', 'llama3'),
                temperature=llm_data.get('temperature', 0.7),
                max_tokens=llm_data.get('max_tokens', 2000),
                timeout=llm_data.get('timeout', 30)
            )
        
        # Parse job search config
        if 'job_search' in raw_config:
            js_data = raw_config['job_search']
            config.job_search = JobSearchConfig(
                keywords=js_data.get('keywords', []),
                min_salary=js_data.get('min_salary', 3500000),
                preferred_locations=js_data.get('preferred_locations', []),
                remote_preference=js_data.get('remote_preference', True),
                search_schedule=js_data.get('search_schedule', '0 9 * * *')
            )
        
        # Parse scraping config
        if 'scraping' in raw_config:
            scraping_data = raw_config['scraping']
            naukri_data = scraping_data.get('naukri', {})
            config.scraping = ScrapingConfig(
                naukri_enabled=naukri_data.get('enabled', True),
                rate_limit_delay=naukri_data.get('rate_limit_delay', 2),
                max_retries=naukri_data.get('max_retries', 3),
                timeout=naukri_data.get('timeout', 30),
                user_agents=scraping_data.get('user_agents', [])
            )
        
        # Parse database config
        if 'database' in raw_config:
            db_data = raw_config['database']
            config.database = DatabaseConfig(
                type=db_data.get('type', 'sqlite'),
                path=db_data.get('path', 'data/job_assistant.db'),
                backup_enabled=db_data.get('backup_enabled', True),
                backup_schedule=db_data.get('backup_schedule', '0 0 * * *'),
                backup_retention_days=db_data.get('backup_retention_days', 30)
            )
        
        # Parse notification config
        if 'notifications' in raw_config:
            notif_data = raw_config['notifications']
            
            # Email config
            email_data = notif_data.get('email', {})
            email_config = EmailConfig(
                enabled=email_data.get('enabled', False),
                smtp_server=email_data.get('smtp_server', 'smtp.gmail.com'),
                smtp_port=email_data.get('smtp_port', 587),
                smtp_username=email_data.get('smtp_username', ''),
                smtp_password=email_data.get('smtp_password', ''),
                from_address=email_data.get('from_address', ''),
                to_address=email_data.get('to_address', '')
            )
            
            # WhatsApp config
            whatsapp_data = notif_data.get('whatsapp', {})
            whatsapp_config = WhatsAppConfig(
                enabled=whatsapp_data.get('enabled', False),
                twilio_account_sid=whatsapp_data.get('twilio_account_sid', ''),
                twilio_auth_token=whatsapp_data.get('twilio_auth_token', ''),
                twilio_whatsapp_number=whatsapp_data.get('twilio_whatsapp_number', 'whatsapp:+14155238886'),
                user_whatsapp_number=whatsapp_data.get('user_whatsapp_number', '')
            )
            
            # Preferences config
            pref_data = notif_data.get('preferences', {})
            pref_config = NotificationPreferencesConfig(
                daily_digest=pref_data.get('daily_digest', True),
                digest_time=pref_data.get('digest_time', '09:00'),
                interview_reminders=pref_data.get('interview_reminders', True),
                status_updates=pref_data.get('status_updates', True)
            )
            
            config.notifications = NotificationConfig(
                email=email_config,
                whatsapp=whatsapp_config,
                preferences=pref_config
            )
        
        # Parse user config
        if 'user' in raw_config:
            user_data = raw_config['user']
            config.user = UserConfig(
                name=user_data.get('name', '[Your Name]'),
                email=user_data.get('email', '[your-email@example.com]'),
                experience_years=user_data.get('experience_years', 0),
                target_salary=user_data.get('target_salary', 3500000),
                skills=user_data.get('skills', []),
                desired_tech_stack=user_data.get('desired_tech_stack', [])
            )
        
        # Parse scoring config
        if 'scoring' in raw_config:
            scoring_data = raw_config['scoring']
            config.scoring = ScoringConfig(
                skills_match_weight=scoring_data.get('skills_match_weight', 0.35),
                salary_match_weight=scoring_data.get('salary_match_weight', 0.25),
                tech_stack_match_weight=scoring_data.get('tech_stack_match_weight', 0.20),
                remote_flexibility_weight=scoring_data.get('remote_flexibility_weight', 0.10),
                company_profile_weight=scoring_data.get('company_profile_weight', 0.10)
            )
        
        # Parse company profiling config
        if 'company_profiling' in raw_config:
            cp_data = raw_config['company_profiling']
            config.company_profiling = CompanyProfilingConfig(
                cache_duration_days=cp_data.get('cache_duration_days', 30),
                glassdoor_enabled=cp_data.get('glassdoor_enabled', False),
                news_api_enabled=cp_data.get('news_api_enabled', False)
            )
        
        # Parse security config
        if 'security' in raw_config:
            sec_data = raw_config['security']
            config.security = SecurityConfig(
                encryption_key_env_var=sec_data.get('encryption_key_env_var', 'JOB_ASSISTANT_ENCRYPTION_KEY'),
                credential_storage=sec_data.get('credential_storage', 'database')
            )
        
        # Parse logging config
        if 'logging' in raw_config:
            log_data = raw_config['logging']
            config.logging = LoggingConfig(
                level=log_data.get('level', 'INFO'),
                file_path=log_data.get('file_path', 'logs/job_assistant.log'),
                max_file_size_mb=log_data.get('max_file_size_mb', 10),
                backup_count=log_data.get('backup_count', 5)
            )
        
        # Parse UI config
        if 'ui' in raw_config:
            ui_data = raw_config['ui']
            config.ui = UIConfig(
                theme=ui_data.get('theme', 'light'),
                page_title=ui_data.get('page_title', 'GenAI Job Assistant'),
                page_icon=ui_data.get('page_icon', '🤖'),
                layout=ui_data.get('layout', 'wide')
            )
        
        return config

    
    def validate_config(self) -> None:
        """
        Validate configuration settings
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        errors = []
        warnings = []
        
        # Validate LLM config
        if self.config.llm.provider not in ['ollama', 'llamacpp']:
            errors.append(f"Invalid LLM provider: {self.config.llm.provider}. Must be 'ollama' or 'llamacpp'")
        
        if self.config.llm.temperature < 0 or self.config.llm.temperature > 2:
            warnings.append(f"LLM temperature {self.config.llm.temperature} is outside typical range (0-2)")
        
        if self.config.llm.max_tokens < 100:
            warnings.append(f"LLM max_tokens {self.config.llm.max_tokens} is very low, may truncate responses")
        
        # Validate job search config
        if not self.config.job_search.keywords:
            warnings.append("No job search keywords configured")
        
        if self.config.job_search.min_salary < 0:
            errors.append(f"Invalid min_salary: {self.config.job_search.min_salary}. Must be non-negative")
        
        # Validate scraping config
        if self.config.scraping.rate_limit_delay < 1:
            warnings.append(f"Rate limit delay {self.config.scraping.rate_limit_delay}s is very low, may trigger anti-bot measures")
        
        if self.config.scraping.max_retries < 0:
            errors.append(f"Invalid max_retries: {self.config.scraping.max_retries}. Must be non-negative")
        
        # Validate database config
        if self.config.database.type != 'sqlite':
            warnings.append(f"Database type '{self.config.database.type}' is not fully supported. Only 'sqlite' is tested")
        
        # Validate notification config
        if self.config.notifications.email.enabled:
            if not self.config.notifications.email.smtp_server:
                errors.append("Email notifications enabled but smtp_server not configured")
            if not self.config.notifications.email.smtp_username:
                warnings.append("Email notifications enabled but smtp_username not configured")
            if not self.config.notifications.email.to_address or '[' in self.config.notifications.email.to_address:
                warnings.append("Email notifications enabled but to_address not properly configured")
        
        if self.config.notifications.whatsapp.enabled:
            if not self.config.notifications.whatsapp.twilio_account_sid or '[' in self.config.notifications.whatsapp.twilio_account_sid:
                errors.append("WhatsApp notifications enabled but Twilio credentials not configured")
            if not self.config.notifications.whatsapp.user_whatsapp_number or '[' in self.config.notifications.whatsapp.user_whatsapp_number:
                warnings.append("WhatsApp notifications enabled but user_whatsapp_number not properly configured")
        
        # Validate scoring weights
        total_weight = (
            self.config.scoring.skills_match_weight +
            self.config.scoring.salary_match_weight +
            self.config.scoring.tech_stack_match_weight +
            self.config.scoring.remote_flexibility_weight +
            self.config.scoring.company_profile_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            warnings.append(f"Scoring weights sum to {total_weight:.2f}, not 1.0. Scores may not be normalized correctly")
        
        # Validate logging config
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level.upper() not in valid_log_levels:
            errors.append(f"Invalid logging level: {self.config.logging.level}. Must be one of {valid_log_levels}")
        
        # Validate UI config
        if self.config.ui.theme not in ['light', 'dark']:
            warnings.append(f"UI theme '{self.config.ui.theme}' may not be supported. Use 'light' or 'dark'")
        
        if self.config.ui.layout not in ['centered', 'wide']:
            warnings.append(f"UI layout '{self.config.ui.layout}' may not be supported. Use 'centered' or 'wide'")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        # Raise errors if any
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def generate_default_config(self) -> None:
        """
        Generate default configuration file
        """
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Create default config
            default_config = AppConfig()
            
            # Convert to dictionary
            config_dict = self._config_to_dict(default_config)
            
            # Write to file
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Default configuration generated: {self.config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to generate default configuration: {e}")
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """
        Convert AppConfig object to dictionary for YAML serialization
        
        Args:
            config: AppConfig object
            
        Returns:
            Dictionary representation
        """
        return {
            'llm': {
                'provider': config.llm.provider,
                'model_name': config.llm.model_name,
                'temperature': config.llm.temperature,
                'max_tokens': config.llm.max_tokens,
                'timeout': config.llm.timeout
            },
            'job_search': {
                'keywords': config.job_search.keywords,
                'min_salary': config.job_search.min_salary,
                'preferred_locations': config.job_search.preferred_locations,
                'remote_preference': config.job_search.remote_preference,
                'search_schedule': config.job_search.search_schedule
            },
            'scraping': {
                'naukri': {
                    'enabled': config.scraping.naukri_enabled,
                    'rate_limit_delay': config.scraping.rate_limit_delay,
                    'max_retries': config.scraping.max_retries,
                    'timeout': config.scraping.timeout
                },
                'user_agents': config.scraping.user_agents
            },
            'database': {
                'type': config.database.type,
                'path': config.database.path,
                'backup_enabled': config.database.backup_enabled,
                'backup_schedule': config.database.backup_schedule,
                'backup_retention_days': config.database.backup_retention_days
            },
            'notifications': {
                'email': {
                    'enabled': config.notifications.email.enabled,
                    'smtp_server': config.notifications.email.smtp_server,
                    'smtp_port': config.notifications.email.smtp_port,
                    'smtp_username': config.notifications.email.smtp_username,
                    'smtp_password': config.notifications.email.smtp_password,
                    'from_address': config.notifications.email.from_address,
                    'to_address': config.notifications.email.to_address
                },
                'whatsapp': {
                    'enabled': config.notifications.whatsapp.enabled,
                    'twilio_account_sid': config.notifications.whatsapp.twilio_account_sid,
                    'twilio_auth_token': config.notifications.whatsapp.twilio_auth_token,
                    'twilio_whatsapp_number': config.notifications.whatsapp.twilio_whatsapp_number,
                    'user_whatsapp_number': config.notifications.whatsapp.user_whatsapp_number
                },
                'preferences': {
                    'daily_digest': config.notifications.preferences.daily_digest,
                    'digest_time': config.notifications.preferences.digest_time,
                    'interview_reminders': config.notifications.preferences.interview_reminders,
                    'status_updates': config.notifications.preferences.status_updates
                }
            },
            'user': {
                'name': config.user.name,
                'email': config.user.email,
                'experience_years': config.user.experience_years,
                'target_salary': config.user.target_salary,
                'skills': config.user.skills,
                'desired_tech_stack': config.user.desired_tech_stack
            },
            'scoring': {
                'skills_match_weight': config.scoring.skills_match_weight,
                'salary_match_weight': config.scoring.salary_match_weight,
                'tech_stack_match_weight': config.scoring.tech_stack_match_weight,
                'remote_flexibility_weight': config.scoring.remote_flexibility_weight,
                'company_profile_weight': config.scoring.company_profile_weight
            },
            'company_profiling': {
                'cache_duration_days': config.company_profiling.cache_duration_days,
                'glassdoor_enabled': config.company_profiling.glassdoor_enabled,
                'news_api_enabled': config.company_profiling.news_api_enabled
            },
            'security': {
                'encryption_key_env_var': config.security.encryption_key_env_var,
                'credential_storage': config.security.credential_storage
            },
            'logging': {
                'level': config.logging.level,
                'file_path': config.logging.file_path,
                'max_file_size_mb': config.logging.max_file_size_mb,
                'backup_count': config.logging.backup_count
            },
            'ui': {
                'theme': config.ui.theme,
                'page_title': config.ui.page_title,
                'page_icon': config.ui.page_icon,
                'layout': config.ui.layout
            }
        }
    
    def get_config(self) -> AppConfig:
        """
        Get current configuration
        
        Returns:
            AppConfig object
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded. Call load_config() first")
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        # Merge updates into raw config
        self._merge_dict(self._raw_config, updates)
        
        # Re-parse configuration
        self.config = self._parse_config(self._raw_config)
        
        # Validate updated configuration
        self.validate_config()
        
        logger.info("Configuration updated")
    
    def save_config(self) -> None:
        """
        Save current configuration to file
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        try:
            config_dict = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Configuration saved to: {self.config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def _merge_dict(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Recursively merge updates into base dictionary
        
        Args:
            base: Base dictionary to update
            updates: Updates to apply
        """
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: str = "config/config.yaml") -> ConfigManager:
    """
    Get global configuration manager instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """
    Load application configuration
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        AppConfig object
    """
    manager = get_config_manager(config_path)
    return manager.load_config()
