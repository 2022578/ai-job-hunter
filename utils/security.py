"""
Security utilities for credential encryption and management.
Implements Fernet symmetric encryption for secure credential storage.
"""

import os
from typing import Optional, Dict
from cryptography.fernet import Fernet
from pathlib import Path


class CredentialManager:
    """
    Manages encryption and decryption of sensitive credentials.
    Uses Fernet symmetric encryption with a key stored in environment variables.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize the CredentialManager with an encryption key.
        
        Args:
            key: Optional encryption key. If not provided, attempts to load from
                 environment variable ENCRYPTION_KEY or generates a new one.
        """
        if key is None:
            key = self._load_or_generate_key()
        
        self.cipher = Fernet(key)
        self._key = key
    
    def _load_or_generate_key(self) -> bytes:
        """
        Load encryption key from environment variable or generate a new one.
        
        Returns:
            Encryption key as bytes
        """
        # Try to load from environment variable
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Try to load from .env file in project root
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ENCRYPTION_KEY='):
                        key_str = line.split('=', 1)[1].strip()
                        return key_str.encode()
        
        # Generate new key if not found
        new_key = Fernet.generate_key()
        
        # Save to .env file for persistence
        with open('.env', 'a') as f:
            f.write(f'\nENCRYPTION_KEY={new_key.decode()}\n')
        
        return new_key
    
    def generate_key(self) -> bytes:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            New encryption key as bytes
        """
        return Fernet.generate_key()
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string using Fernet encryption.
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(data.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a Fernet-encrypted string.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plain text string
            
        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        if not encrypted_data:
            return ""
        
        decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
    
    def store_credentials(self, service: str, credentials: Dict[str, str]) -> Dict[str, str]:
        """
        Encrypt and prepare credentials for storage.
        
        Args:
            service: Service name (e.g., "naukri", "smtp", "twilio")
            credentials: Dictionary of credential key-value pairs
            
        Returns:
            Dictionary with encrypted credential values
        """
        encrypted_creds = {}
        for key, value in credentials.items():
            if value:  # Only encrypt non-empty values
                encrypted_creds[key] = self.encrypt(value)
            else:
                encrypted_creds[key] = ""
        
        return encrypted_creds
    
    def retrieve_credentials(self, encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt stored credentials.
        
        Args:
            encrypted_credentials: Dictionary with encrypted credential values
            
        Returns:
            Dictionary with decrypted credential values
        """
        decrypted_creds = {}
        for key, encrypted_value in encrypted_credentials.items():
            if encrypted_value:  # Only decrypt non-empty values
                try:
                    decrypted_creds[key] = self.decrypt(encrypted_value)
                except Exception as e:
                    # If decryption fails, return empty string
                    decrypted_creds[key] = ""
            else:
                decrypted_creds[key] = ""
        
        return decrypted_creds
    
    def get_key(self) -> bytes:
        """
        Get the current encryption key.
        
        Returns:
            Encryption key as bytes
        """
        return self._key
