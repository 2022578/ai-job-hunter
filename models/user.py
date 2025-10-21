"""
User Profile Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import uuid


@dataclass
class Project:
    """Project information"""
    name: str
    description: str
    technologies: List[str] = field(default_factory=list)
    url: Optional[str] = None


@dataclass
class UserProfile:
    """User profile data model with validation"""
    
    name: str
    email: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resume_text: str = ""
    resume_path: str = ""
    skills: List[str] = field(default_factory=list)
    experience_years: int = 0
    target_salary: int = 0
    preferred_locations: List[str] = field(default_factory=list)
    preferred_remote: bool = False
    desired_tech_stack: List[str] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate user profile data"""
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        
        if not self.email or not self.email.strip():
            raise ValueError("Email cannot be empty")
        
        if '@' not in self.email:
            raise ValueError("Invalid email format")
        
        if self.experience_years < 0:
            raise ValueError("Experience years cannot be negative")
        
        if self.target_salary < 0:
            raise ValueError("Target salary cannot be negative")
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary"""
        # Parse datetime strings
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Handle list fields as JSON strings or lists
        for field_name in ['skills', 'preferred_locations', 'desired_tech_stack']:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = json.loads(data[field_name]) if data[field_name] else []
        
        # Handle projects
        if 'projects' in data:
            if isinstance(data['projects'], str):
                projects_data = json.loads(data['projects']) if data['projects'] else []
                data['projects'] = [Project(**p) for p in projects_data]
            elif isinstance(data['projects'], list) and data['projects']:
                if isinstance(data['projects'][0], dict):
                    data['projects'] = [Project(**p) for p in data['projects']]
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UserProfile':
        """Create UserProfile from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'resume_text': self.resume_text,
            'resume_path': self.resume_path,
            'skills': json.dumps(self.skills),
            'experience_years': self.experience_years,
            'target_salary': self.target_salary,
            'preferred_locations': json.dumps(self.preferred_locations),
            'preferred_remote': self.preferred_remote,
            'desired_tech_stack': json.dumps(self.desired_tech_stack),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from database row"""
        return cls.from_dict(row)
