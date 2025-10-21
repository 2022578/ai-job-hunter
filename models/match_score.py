"""
Match Score Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class MatchScore:
    """Match score data model for job-candidate alignment"""
    
    job_id: str
    total_score: float
    skills_match: float
    salary_match: float
    tech_stack_match: float
    remote_flexibility: float
    company_profile_score: float
    breakdown: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate match score data"""
        if not self.job_id or not self.job_id.strip():
            raise ValueError("Job ID cannot be empty")
        
        # Validate all scores are between 0 and 100
        scores = [
            ('total_score', self.total_score),
            ('skills_match', self.skills_match),
            ('salary_match', self.salary_match),
            ('tech_stack_match', self.tech_stack_match),
            ('remote_flexibility', self.remote_flexibility),
            ('company_profile_score', self.company_profile_score)
        ]
        
        for name, score in scores:
            if not (0 <= score <= 100):
                raise ValueError(f"{name} must be between 0 and 100, got {score}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.calculated_at:
            data['calculated_at'] = self.calculated_at.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchScore':
        """Create MatchScore from dictionary"""
        # Parse datetime string
        if 'calculated_at' in data and data['calculated_at']:
            if isinstance(data['calculated_at'], str):
                data['calculated_at'] = datetime.fromisoformat(data['calculated_at'])
        
        # Handle breakdown as JSON string or dict
        if 'breakdown' in data and isinstance(data['breakdown'], str):
            data['breakdown'] = json.loads(data['breakdown']) if data['breakdown'] else {}
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MatchScore':
        """Create MatchScore from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
