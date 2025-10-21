"""
Notification Preferences Data Model
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any
import json


@dataclass
class NotificationPreferences:
    """Notification preferences data model with validation"""
    
    user_id: str
    email_address: str
    email_enabled: bool = True
    whatsapp_enabled: bool = False
    whatsapp_number: str = ""
    daily_digest: bool = True
    interview_reminders: bool = True
    status_updates: bool = True
    digest_time: str = "09:00"
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate notification preferences data"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.email_address or not self.email_address.strip():
            raise ValueError("Email address cannot be empty")
        
        if '@' not in self.email_address:
            raise ValueError("Invalid email format")
        
        if self.whatsapp_enabled and not self.whatsapp_number:
            raise ValueError("WhatsApp number required when WhatsApp is enabled")
        
        # Validate digest_time format (HH:MM)
        if self.digest_time:
            try:
                hours, minutes = self.digest_time.split(':')
                hours_int = int(hours)
                minutes_int = int(minutes)
                if not (0 <= hours_int <= 23) or not (0 <= minutes_int <= 59):
                    raise ValueError("Invalid time format")
            except (ValueError, AttributeError):
                raise ValueError("Digest time must be in HH:MM format (e.g., 09:00)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationPreferences':
        """Create NotificationPreferences from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NotificationPreferences':
        """Create NotificationPreferences from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'email_address': self.email_address,
            'whatsapp_enabled': self.whatsapp_enabled,
            'whatsapp_number': self.whatsapp_number,
            'daily_digest': self.daily_digest,
            'interview_reminders': self.interview_reminders,
            'status_updates': self.status_updates,
            'digest_time': self.digest_time
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'NotificationPreferences':
        """Create NotificationPreferences from database row"""
        return cls.from_dict(row)
