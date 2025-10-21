"""
Database Manager for GenAI Job Assistant
Handles SQLite connection management, initialization, and backup operations
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self, db_path: str = "data/job_assistant.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.schema_path = "database/schema.sql"
        self._connections: dict = {}  # Store connections per thread
        
    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create database connection for current thread
        
        Returns:
            SQLite connection object
        """
        import threading
        thread_id = threading.get_ident()
        
        if thread_id not in self._connections:
            # Ensure database directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Create connection with row factory for dict-like access
            # check_same_thread=False allows the connection object to be used across threads
            # but we still create one connection per thread for safety
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            
            self._connections[thread_id] = conn
            logger.info(f"Database connection established for thread {thread_id}: {self.db_path}")
        
        return self._connections[thread_id]
    
    def close_connection(self):
        """Close database connections for all threads"""
        import threading
        thread_id = threading.get_ident()
        
        if thread_id in self._connections:
            self._connections[thread_id].close()
            del self._connections[thread_id]
            logger.info(f"Database connection closed for thread {thread_id}")
    
    def close_all_connections(self):
        """Close all database connections"""
        for thread_id, conn in list(self._connections.items()):
            conn.close()
            logger.info(f"Database connection closed for thread {thread_id}")
        self._connections.clear()
    
    def initialize_database(self) -> bool:
        """
        Initialize database with schema if not exists
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            conn = self.get_connection()
            
            # Read schema file
            if not os.path.exists(self.schema_path):
                logger.error(f"Schema file not found: {self.schema_path}")
                return False
            
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema
            conn.executescript(schema_sql)
            conn.commit()
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    def backup_database(self, backup_dir: str = "data/backups") -> Optional[str]:
        """
        Create backup of database
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            # Ensure backup directory exists
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"job_assistant_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Close existing connection before backup
            self.close_connection()
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Close existing connection
            self.close_connection()
            
            # Create backup of current database before restore
            if os.path.exists(self.db_path):
                current_backup = f"{self.db_path}.before_restore"
                shutil.copy2(self.db_path, current_backup)
                logger.info(f"Current database backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def get_schema_version(self) -> int:
        """
        Get current schema version
        
        Returns:
            Current schema version number
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute("SELECT MAX(version) as version FROM schema_version")
            result = cursor.fetchone()
            return result['version'] if result['version'] else 0
        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0
    
    def apply_migration(self, version: int, migration_sql: str, description: str) -> bool:
        """
        Apply database migration
        
        Args:
            version: Migration version number
            migration_sql: SQL statements to execute
            description: Migration description
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            conn = self.get_connection()
            current_version = self.get_schema_version()
            
            if version <= current_version:
                logger.info(f"Migration {version} already applied")
                return True
            
            # Execute migration
            conn.executescript(migration_sql)
            
            # Record migration
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, description)
            )
            conn.commit()
            
            logger.info(f"Migration {version} applied: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            conn.rollback()
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute SELECT query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            conn.rollback()
            return 0
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: str = "data/job_assistant.db") -> DatabaseManager:
    """
    Get global database manager instance
    
    Args:
        db_path: Path to database file
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager
