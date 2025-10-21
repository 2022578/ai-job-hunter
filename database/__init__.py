"""
Database module for GenAI Job Assistant.
Contains database schema, connection management, and repository layer.
"""

from database.db_manager import DatabaseManager, get_db_manager
from database.repositories import (
    JobRepository,
    ApplicationRepository,
    HRContactRepository,
    QuestionRepository,
    CompanyRepository,
    UserRepository
)

__all__ = [
    'DatabaseManager',
    'get_db_manager',
    'JobRepository',
    'ApplicationRepository',
    'HRContactRepository',
    'QuestionRepository',
    'CompanyRepository',
    'UserRepository'
]
