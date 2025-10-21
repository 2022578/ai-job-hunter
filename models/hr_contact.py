"""
HR Contact Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json
import uuid


@dataclass
class HRContact:
    """HR contact information data model with validation"""
    
    application_id: str
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    designation: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate HR contact data"""
        if not self.application_id or not self.application_id.strip():
            raise ValueError("Application ID cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("HR contact name cannot be empty")
        
        if self.email and '@' not in self.email:
            raise ValueError("Invalid email format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HRContact':
        """Create HRContact from dictionary"""
        # Parse datetime strings
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'HRContact':
        """Create HRContact from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'designation': self.designation,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'HRContact':
        """Create HRContact from database row"""
        return cls.from_dict(row)
