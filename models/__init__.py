"""
Data models module for GenAI Job Assistant.
Contains dataclasses and validation logic for core entities.
"""

from models.job import JobListing
from models.user import UserProfile, Project
from models.application import Application
from models.hr_contact import HRContact
from models.question import CustomQuestion
from models.company import CompanyProfile
from models.notification import NotificationPreferences
from models.match_score import MatchScore

__all__ = [
    'JobListing',
    'UserProfile',
    'Project',
    'Application',
    'HRContact',
    'CustomQuestion',
    'CompanyProfile',
    'NotificationPreferences',
    'MatchScore'
]
