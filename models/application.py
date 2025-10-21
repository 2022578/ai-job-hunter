"""
Application Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json
import uuid


@dataclass
class Application:
    """Application tracking data model with validation"""
    
    job_id: str
    user_id: str
    status: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    applied_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    notes: str = ""
    cover_letter: Optional[str] = None
    hr_contact_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Valid status values
    VALID_STATUSES = ["saved", "applied", "interview", "offered", "rejected", "not_interested"]
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate application data"""
        if not self.job_id or not self.job_id.strip():
            raise ValueError("Job ID cannot be empty")
        
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {self.VALID_STATUSES}")
        
        if self.applied_date and self.interview_date:
            if self.interview_date < self.applied_date:
                raise ValueError("Interview date cannot be before applied date")
    
    def update_status(self, new_status: str):
        """Update application status with validation"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {self.VALID_STATUSES}")
        
        self.status = new_status
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.applied_date:
            data['applied_date'] = self.applied_date.isoformat()
        if self.interview_date:
            data['interview_date'] = self.interview_date.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Application':
        """Create Application from dictionary"""
        # Parse datetime strings
        datetime_fields = ['applied_date', 'interview_date', 'created_at', 'updated_at']
        for field_name in datetime_fields:
            if field_name in data and data[field_name]:
                if isinstance(data[field_name], str):
                    data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Application':
        """Create Application from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'status': self.status,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'notes': self.notes,
            'cover_letter': self.cover_letter,
            'hr_contact_id': self.hr_contact_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Application':
        """Create Application from database row"""
        return cls.from_dict(row)
