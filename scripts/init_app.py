"""
Application Initialization Script for GenAI Job Assistant
Sets up database, configuration, and validates dependencies
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_manager import ConfigManager, ConfigurationError
from database.db_manager import DatabaseManager
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key


class InitializationError(Exception):
    """Custom exception for initialization errors"""
    pass


class AppInitializer:
    """Handles application initialization and setup"""
    
    def __init__(self):
        """Initialize the app initializer"""
        self.config_manager = ConfigManager()
        self.db_manager = None
        self.checks_passed: List[str] = []
        self.checks_failed: List[Tuple[str, str]] = []
        self.warnings: List[str] = []
        
        # Setup basic logging with UTF-8 encoding for Windows compatibility
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        # Force UTF-8 encoding for stdout on Windows
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """
        Run complete initialization process
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("GenAI Job Assistant - Initialization")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Setup directories
            self.logger.info("\n[1/7] Setting up directories...")
            self._setup_directories()
            
            # Step 2: Setup environment variables
            self.logger.info("\n[2/7] Setting up environment variables...")
            self._setup_environment()
            
            # Step 3: Load/generate configuration
            self.logger.info("\n[3/7] Loading configuration...")
            self._setup_configuration()
            
            # Step 4: Initialize database
            self.logger.info("\n[4/7] Initializing database...")
            self._setup_database()
            
            # Step 5: Run health checks
            self.logger.info("\n[5/7] Running dependency health checks...")
            self._run_health_checks()
            
            # Step 6: Setup logging
            self.logger.info("\n[6/7] Setting up application logging...")
            self._setup_logging()
            
            # Step 7: Display summary
            self.logger.info("\n[7/7] Initialization complete!")
            self._display_summary()
            
            return len(self.checks_failed) == 0
            
        except Exception as e:
            self.logger.error(f"\nInitialization failed: {e}")
            return False
    
    def _setup_directories(self) -> None:
        """Create necessary directories"""
        directories = [
            'data',
            'data/backups',
            'logs',
            'config'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"  ✓ Created directory: {directory}")
            else:
                self.logger.info(f"  ✓ Directory exists: {directory}")
        
        self.checks_passed.append("Directory structure")
    
    def _setup_environment(self) -> None:
        """Setup environment variables"""
        env_file = '.env'
        env_example = '.env.example'
        
        # Load existing .env if it exists
        if os.path.exists(env_file):
            load_dotenv(env_file)
            self.logger.info(f"  ✓ Loaded environment from: {env_file}")
        else:
            # Create .env from .env.example
            if os.path.exists(env_example):
                with open(env_example, 'r') as f:
                    content = f.read()
                with open(env_file, 'w') as f:
                    f.write(content)
                self.logger.info(f"  ✓ Created {env_file} from {env_example}")
            else:
                # Create minimal .env
                with open(env_file, 'w') as f:
                    f.write("# GenAI Job Assistant Environment Variables\n")
                self.logger.info(f"  ✓ Created minimal {env_file}")
        
        # Check/generate encryption key
        encryption_key = os.getenv('ENCRYPTION_KEY') or os.getenv('JOB_ASSISTANT_ENCRYPTION_KEY')
        
        if not encryption_key or encryption_key == 'your-encryption-key-here':
            # Generate new encryption key
            new_key = Fernet.generate_key().decode()
            set_key(env_file, 'ENCRYPTION_KEY', new_key)
            os.environ['ENCRYPTION_KEY'] = new_key
            self.logger.info("  ✓ Generated new encryption key")
        else:
            self.logger.info("  ✓ Encryption key found")
        
        self.checks_passed.append("Environment variables")
    
    def _setup_configuration(self) -> None:
        """Load or generate configuration"""
        try:
            config = self.config_manager.load_config()
            self.logger.info(f"  ✓ Configuration loaded from: {self.config_manager.config_path}")
            
            # Check if user has configured basic settings
            if config.user.name == "[Your Name]":
                self.warnings.append("User profile not configured. Please update config/config.yaml")
            
            if not config.notifications.email.enabled and not config.notifications.whatsapp.enabled:
                self.warnings.append("No notification channels enabled")
            
            self.checks_passed.append("Configuration")
            
        except ConfigurationError as e:
            self.checks_failed.append(("Configuration", str(e)))
            raise InitializationError(f"Configuration setup failed: {e}")
    
    def _setup_database(self) -> None:
        """Initialize database"""
        try:
            config = self.config_manager.get_config()
            db_path = config.database.path
            
            self.db_manager = DatabaseManager(db_path)
            
            # Check if database exists
            db_exists = os.path.exists(db_path)
            
            if not db_exists:
                self.logger.info(f"  Creating new database: {db_path}")
            
            # Initialize database (creates tables if not exist)
            success = self.db_manager.initialize_database()
            
            if success:
                if db_exists:
                    self.logger.info(f"  ✓ Database verified: {db_path}")
                else:
                    self.logger.info(f"  ✓ Database created: {db_path}")
                self.checks_passed.append("Database")
            else:
                self.checks_failed.append(("Database", "Failed to initialize database"))
                
        except Exception as e:
            self.checks_failed.append(("Database", str(e)))
            raise InitializationError(f"Database setup failed: {e}")
    
    def _run_health_checks(self) -> None:
        """Run health checks for all dependencies"""
        
        # Check Python version
        self._check_python_version()
        
        # Check Ollama
        self._check_ollama()
        
        # Check Selenium/Chrome
        self._check_selenium()
        
        # Check database connectivity
        self._check_database()
        
        # Check required packages
        self._check_packages()
    
    def _check_python_version(self) -> None:
        """Check Python version"""
        import sys
        version = sys.version_info
        
        if version.major >= 3 and version.minor >= 8:
            self.logger.info(f"  ✓ Python version: {version.major}.{version.minor}.{version.micro}")
            self.checks_passed.append("Python version")
        else:
            self.checks_failed.append(("Python version", f"Python 3.8+ required, found {version.major}.{version.minor}"))
    
    def _check_ollama(self) -> None:
        """Check Ollama availability"""
        try:
            import requests
            
            config = self.config_manager.get_config()
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            
            # Try to connect to Ollama
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Check if configured model is available
                configured_model = config.llm.model_name
                if any(configured_model in name for name in model_names):
                    self.logger.info(f"  ✓ Ollama running with model: {configured_model}")
                    self.checks_passed.append("Ollama")
                else:
                    self.warnings.append(f"Ollama running but model '{configured_model}' not found. Available: {', '.join(model_names[:3])}")
                    self.logger.info(f"  ⚠ Ollama running but model '{configured_model}' not installed")
                    self.checks_passed.append("Ollama (partial)")
            else:
                self.checks_failed.append(("Ollama", f"Unexpected response: {response.status_code}"))
                
        except requests.exceptions.ConnectionError:
            self.checks_failed.append(("Ollama", "Not running or not accessible. Start with: ollama serve"))
        except Exception as e:
            self.checks_failed.append(("Ollama", str(e)))
    
    def _check_selenium(self) -> None:
        """Check Selenium and Chrome WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            
            # Try to create a headless Chrome instance
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.quit()
                self.logger.info("  ✓ Selenium WebDriver (Chrome)")
                self.checks_passed.append("Selenium WebDriver")
            except Exception as e:
                self.checks_failed.append(("Selenium WebDriver", "Chrome/ChromeDriver not found or incompatible"))
                
        except ImportError:
            self.checks_failed.append(("Selenium", "Package not installed"))
    
    def _check_database(self) -> None:
        """Check database connectivity"""
        try:
            if self.db_manager:
                conn = self.db_manager.get_connection()
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result:
                    self.logger.info("  ✓ Database connectivity")
                    self.checks_passed.append("Database connectivity")
                else:
                    self.checks_failed.append(("Database connectivity", "Query failed"))
            else:
                self.checks_failed.append(("Database connectivity", "Database manager not initialized"))
                
        except Exception as e:
            self.checks_failed.append(("Database connectivity", str(e)))
    
    def _check_packages(self) -> None:
        """Check required Python packages"""
        required_packages = [
            'streamlit',
            'langgraph',
            'langchain',
            'selenium',
            'beautifulsoup4',
            'apscheduler',
            'cryptography',
            'twilio',
            'pandas',
            'pyyaml',
            'requests'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            self.logger.info(f"  ✓ All required packages installed")
            self.checks_passed.append("Required packages")
        else:
            self.checks_failed.append(("Required packages", f"Missing: {', '.join(missing_packages)}"))
    
    def _setup_logging(self) -> None:
        """Setup application logging"""
        try:
            config = self.config_manager.get_config()
            log_path = config.logging.file_path
            log_dir = os.path.dirname(log_path)
            
            # Ensure log directory exists
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure logging
            from logging.handlers import RotatingFileHandler
            
            log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
            max_bytes = config.logging.max_file_size_mb * 1024 * 1024
            
            # Create rotating file handler with UTF-8 encoding
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=config.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            # Add handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
            
            self.logger.info(f"  ✓ Logging configured: {log_path}")
            self.checks_passed.append("Logging")
            
        except Exception as e:
            self.checks_failed.append(("Logging", str(e)))
    
    def _display_summary(self) -> None:
        """Display initialization summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("INITIALIZATION SUMMARY")
        self.logger.info("=" * 60)
        
        # Display passed checks
        if self.checks_passed:
            self.logger.info(f"\n✓ Passed ({len(self.checks_passed)}):")
            for check in self.checks_passed:
                self.logger.info(f"  • {check}")
        
        # Display warnings
        if self.warnings:
            self.logger.info(f"\n⚠ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                self.logger.info(f"  • {warning}")
        
        # Display failed checks
        if self.checks_failed:
            self.logger.info(f"\n✗ Failed ({len(self.checks_failed)}):")
            for check, reason in self.checks_failed:
                self.logger.info(f"  • {check}: {reason}")
        
        self.logger.info("\n" + "=" * 60)
        
        if not self.checks_failed:
            self.logger.info("✓ All checks passed! Application is ready to use.")
            self.logger.info("\nNext steps:")
            self.logger.info("  1. Update config/config.yaml with your preferences")
            self.logger.info("  2. Run: streamlit run app.py")
        else:
            self.logger.info("✗ Some checks failed. Please resolve issues before running the application.")
            self.logger.info("\nCommon fixes:")
            if any("Ollama" in check for check, _ in self.checks_failed):
                self.logger.info("  • Install Ollama: https://ollama.ai/download")
                self.logger.info("  • Start Ollama: ollama serve")
                self.logger.info("  • Pull model: ollama pull llama3")
            if any("Selenium" in check for check, _ in self.checks_failed):
                self.logger.info("  • Install Chrome browser")
                self.logger.info("  • Install ChromeDriver or use webdriver-manager")
            if any("packages" in check.lower() for check, _ in self.checks_failed):
                self.logger.info("  • Install dependencies: pip install -r requirements.txt")
        
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    initializer = AppInitializer()
    success = initializer.initialize()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
