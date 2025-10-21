"""
Job Listing Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import uuid


@dataclass
class JobListing:
    """Job listing data model with validation"""
    
    title: str
    company: str
    description: str
    source: str
    source_url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: str = ""
    remote_type: str = "onsite"
    required_skills: List[str] = field(default_factory=list)
    posted_date: Optional[datetime] = None
    raw_html: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    match_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate job listing data"""
        if not self.title or not self.title.strip():
            raise ValueError("Job title cannot be empty")
        
        if not self.company or not self.company.strip():
            raise ValueError("Company name cannot be empty")
        
        if not self.source_url or not self.source_url.strip():
            raise ValueError("Source URL cannot be empty")
        
        if self.remote_type not in ["remote", "hybrid", "onsite"]:
            raise ValueError(f"Invalid remote_type: {self.remote_type}")
        
        if self.salary_min is not None and self.salary_min < 0:
            raise ValueError("Minimum salary cannot be negative")
        
        if self.salary_max is not None and self.salary_max < 0:
            raise ValueError("Maximum salary cannot be negative")
        
        if (self.salary_min is not None and self.salary_max is not None 
            and self.salary_min > self.salary_max):
            raise ValueError("Minimum salary cannot exceed maximum salary")
        
        if self.match_score is not None and not (0 <= self.match_score <= 100):
            raise ValueError("Match score must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.posted_date:
            data['posted_date'] = self.posted_date.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobListing':
        """Create JobListing from dictionary"""
        # Parse datetime strings
        if 'posted_date' in data and data['posted_date']:
            if isinstance(data['posted_date'], str):
                data['posted_date'] = datetime.fromisoformat(data['posted_date'])
        
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Handle required_skills as JSON string or list
        if 'required_skills' in data and isinstance(data['required_skills'], str):
            data['required_skills'] = json.loads(data['required_skills']) if data['required_skills'] else []
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobListing':
        """Create JobListing from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'location': self.location,
            'remote_type': self.remote_type,
            'description': self.description,
            'required_skills': json.dumps(self.required_skills),
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'source_url': self.source_url,
            'source': self.source,
            'raw_html': self.raw_html,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'match_score': self.match_score
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'JobListing':
        """Create JobListing from database row"""
        return cls.from_dict(row)
