"""
Repository for secure credential storage and retrieval.
Handles database operations for encrypted credentials.
"""

import sqlite3
import json
from typing import Optional, Dict
from datetime import datetime
from utils.security import CredentialManager


class CredentialRepository:
    """
    Repository for managing encrypted credentials in the database.
    """
    
    def __init__(self, db_path: str, credential_manager: Optional[CredentialManager] = None):
        """
        Initialize the credential repository.
        
        Args:
            db_path: Path to the SQLite database
            credential_manager: Optional CredentialManager instance for encryption/decryption
        """
        self.db_path = db_path
        self.credential_manager = credential_manager or CredentialManager()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save(self, service: str, credentials: Dict[str, str]) -> bool:
        """
        Save encrypted credentials for a service.
        
        Args:
            service: Service name (e.g., "naukri", "smtp", "twilio")
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt credentials
            encrypted_creds = self.credential_manager.store_credentials(service, credentials)
            encrypted_data = json.dumps(encrypted_creds)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Generate unique ID
            credential_id = f"{service}_{datetime.now().timestamp()}"
            
            # Insert or replace credentials
            cursor.execute("""
                INSERT OR REPLACE INTO credentials (id, service, encrypted_data, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (credential_id, service, encrypted_data))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def retrieve(self, service: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt credentials for a service.
        
        Args:
            service: Service name (e.g., "naukri", "smtp", "twilio")
            
        Returns:
            Dictionary of decrypted credentials or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT encrypted_data FROM credentials
                WHERE service = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (service,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                encrypted_creds = json.loads(row['encrypted_data'])
                decrypted_creds = self.credential_manager.retrieve_credentials(encrypted_creds)
                return decrypted_creds
            
            return None
        except Exception as e:
            print(f"Error retrieving credentials: {e}")
            return None
    
    def delete(self, service: str) -> bool:
        """
        Delete credentials for a service.
        
        Args:
            service: Service name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM credentials WHERE service = ?", (service,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error deleting credentials: {e}")
            return False
    
    def list_services(self) -> list:
        """
        List all services with stored credentials.
        
        Returns:
            List of service names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT service FROM credentials ORDER BY service")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row['service'] for row in rows]
        except Exception as e:
            print(f"Error listing services: {e}")
            return []
    
    def update(self, service: str, credentials: Dict[str, str]) -> bool:
        """
        Update existing credentials for a service.
        
        Args:
            service: Service name
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt credentials
            encrypted_creds = self.credential_manager.store_credentials(service, credentials)
            encrypted_data = json.dumps(encrypted_creds)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE credentials
                SET encrypted_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE service = ?
            """, (encrypted_data, service))
            
            # If no rows were updated, insert new record
            if cursor.rowcount == 0:
                credential_id = f"{service}_{datetime.now().timestamp()}"
                cursor.execute("""
                    INSERT INTO credentials (id, service, encrypted_data, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (credential_id, service, encrypted_data))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error updating credentials: {e}")
            return False
    
    def exists(self, service: str) -> bool:
        """
        Check if credentials exist for a service.
        
        Args:
            service: Service name
            
        Returns:
            True if credentials exist, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM credentials WHERE service = ?", (service,))
            
            row = cursor.fetchone()
            conn.close()
            
            return row['count'] > 0
        except Exception as e:
            print(f"Error checking credentials existence: {e}")
            return False
