"""
Custom Question Data Model
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json
import uuid


@dataclass
class CustomQuestion:
    """Custom interview question data model with validation"""
    
    user_id: str
    question_text: str
    category: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_answer: Optional[str] = None
    ideal_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Valid category values
    VALID_CATEGORIES = ["technical", "behavioral", "system_design", "coding", "general"]
    
    # Valid difficulty values
    VALID_DIFFICULTIES = ["easy", "medium", "hard"]
    
    def __post_init__(self):
        """Validate fields after initialization"""
        self.validate()
    
    def validate(self):
        """Validate custom question data"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not self.question_text or not self.question_text.strip():
            raise ValueError("Question text cannot be empty")
        
        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")
        
        if self.category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category}. Must be one of {self.VALID_CATEGORIES}")
        
        if self.difficulty and self.difficulty not in self.VALID_DIFFICULTIES:
            raise ValueError(f"Invalid difficulty: {self.difficulty}. Must be one of {self.VALID_DIFFICULTIES}")
    
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
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomQuestion':
        """Create CustomQuestion from dictionary"""
        # Parse datetime strings
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'updated_at' in data and data['updated_at']:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CustomQuestion':
        """Create CustomQuestion from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_text': self.question_text,
            'user_answer': self.user_answer,
            'ideal_answer': self.ideal_answer,
            'category': self.category,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'CustomQuestion':
        """Create CustomQuestion from database row"""
        return cls.from_dict(row)
