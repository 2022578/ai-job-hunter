"""
Company Profile Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import uuid


@dataclass
class CompanyProfile:
    """Company profile data model with validation"""
    
    company_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    glassdoor_rating: Optional[float] = None
    employee_count: Optional[int] = None
    funding_stage: Optional[str] = None
    recent_news: List[str] = field(default_factory=list)
    genai_focus_score: float = 0.0
    culture_summary: str = ""
    cached_at: datetime = field(default_factory=datetime.now)
    cache_expiry: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate company profile data"""
        if not self.company_name or not self.company_name.strip():
            raise ValueError("Company name cannot be empty")
        
        if self.glassdoor_rating is not None and not (0 <= self.glassdoor_rating <= 5):
            raise ValueError("Glassdoor rating must be between 0 and 5")
        
        if self.employee_count is not None and self.employee_count < 0:
            raise ValueError("Employee count cannot be negative")
        
        if not (0 <= self.genai_focus_score <= 10):
            raise ValueError("GenAI focus score must be between 0 and 10")
    
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        return datetime.now() < self.cache_expiry
    
    def refresh_cache(self, days: int = 30):
        """Refresh cache expiry"""
        self.cached_at = datetime.now()
        self.cache_expiry = datetime.now() + timedelta(days=days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.cached_at:
            data['cached_at'] = self.cached_at.isoformat()
        if self.cache_expiry:
            data['cache_expiry'] = self.cache_expiry.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyProfile':
        """Create CompanyProfile from dictionary"""
        # Parse datetime strings
        if 'cached_at' in data and data['cached_at']:
            if isinstance(data['cached_at'], str):
                data['cached_at'] = datetime.fromisoformat(data['cached_at'])
        
        if 'cache_expiry' in data and data['cache_expiry']:
            if isinstance(data['cache_expiry'], str):
                data['cache_expiry'] = datetime.fromisoformat(data['cache_expiry'])
        
        # Handle recent_news as JSON string or list
        if 'recent_news' in data and isinstance(data['recent_news'], str):
            data['recent_news'] = json.loads(data['recent_news']) if data['recent_news'] else []
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CompanyProfile':
        """Create CompanyProfile from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'glassdoor_rating': self.glassdoor_rating,
            'employee_count': self.employee_count,
            'funding_stage': self.funding_stage,
            'recent_news': json.dumps(self.recent_news),
            'genai_focus_score': self.genai_focus_score,
            'culture_summary': self.culture_summary,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'cache_expiry': self.cache_expiry.isoformat() if self.cache_expiry else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'CompanyProfile':
        """Create CompanyProfile from database row"""
        return cls.from_dict(row)
