"""
Question Repository for CRUD operations on custom interview questions
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from models.question import CustomQuestion
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class QuestionRepository:
    """Repository for custom question database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize question repository
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def save(self, question: CustomQuestion) -> bool:
        """
        Save custom question to database
        
        Args:
            question: CustomQuestion instance to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            query = """
                INSERT INTO custom_questions (
                    id, user_id, question_text, user_answer, ideal_answer,
                    category, topic, difficulty, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_dict = question.to_db_dict()
            params = (
                db_dict['id'], db_dict['user_id'], db_dict['question_text'],
                db_dict['user_answer'], db_dict['ideal_answer'], db_dict['category'],
                db_dict['topic'], db_dict['difficulty'],
                db_dict['created_at'], db_dict['updated_at']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to save custom question: {e}")
            return False
    
    def update(self, question: CustomQuestion) -> bool:
        """
        Update custom question in database
        
        Args:
            question: CustomQuestion instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            query = """
                UPDATE custom_questions 
                SET user_id = ?, question_text = ?, user_answer = ?,
                    ideal_answer = ?, category = ?, topic = ?,
                    difficulty = ?, updated_at = ?
                WHERE id = ?
            """
            
            question.updated_at = datetime.now()
            db_dict = question.to_db_dict()
            
            params = (
                db_dict['user_id'], db_dict['question_text'], db_dict['user_answer'],
                db_dict['ideal_answer'], db_dict['category'], db_dict['topic'],
                db_dict['difficulty'], db_dict['updated_at'], db_dict['id']
            )
            
            rows_affected = self.db_manager.execute_update(query, params)
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to update custom question: {e}")
            return False
    
    def find_by_category(self, user_id: str, category: str) -> List[CustomQuestion]:
        """
        Find custom questions by category
        
        Args:
            user_id: User ID to filter by
            category: Question category
            
        Returns:
            List of CustomQuestion instances
        """
        try:
            query = """
                SELECT * FROM custom_questions 
                WHERE user_id = ? AND category = ?
                ORDER BY created_at DESC
            """
            results = self.db_manager.execute_query(query, (user_id, category))
            return [CustomQuestion.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find questions by category: {e}")
            return []
    
    def find_by_topic(self, user_id: str, topic: str) -> List[CustomQuestion]:
        """
        Find custom questions by topic
        
        Args:
            user_id: User ID to filter by
            topic: Question topic
            
        Returns:
            List of CustomQuestion instances
        """
        try:
            query = """
                SELECT * FROM custom_questions 
                WHERE user_id = ? AND topic = ?
                ORDER BY created_at DESC
            """
            results = self.db_manager.execute_query(query, (user_id, topic))
            return [CustomQuestion.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find questions by topic: {e}")
            return []
    
    def find_by_id(self, question_id: str) -> Optional[CustomQuestion]:
        """
        Find custom question by ID
        
        Args:
            question_id: Question ID to search for
            
        Returns:
            CustomQuestion if found, None otherwise
        """
        try:
            query = "SELECT * FROM custom_questions WHERE id = ?"
            results = self.db_manager.execute_query(query, (question_id,))
            
            if results:
                return CustomQuestion.from_db_row(results[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to find question by ID: {e}")
            return None
    
    def find_by_user(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> List[CustomQuestion]:
        """
        Find all custom questions for a user with optional filters
        
        Args:
            user_id: User ID to search for
            filters: Optional dictionary with filters:
                - category: Question category
                - topic: Question topic
                - difficulty: Question difficulty
                
        Returns:
            List of CustomQuestion instances
        """
        try:
            query = "SELECT * FROM custom_questions WHERE user_id = ?"
            params = [user_id]
            
            if filters:
                if 'category' in filters:
                    query += " AND category = ?"
                    params.append(filters['category'])
                
                if 'topic' in filters:
                    query += " AND topic = ?"
                    params.append(filters['topic'])
                
                if 'difficulty' in filters:
                    query += " AND difficulty = ?"
                    params.append(filters['difficulty'])
            
            query += " ORDER BY created_at DESC"
            
            results = self.db_manager.execute_query(query, tuple(params))
            return [CustomQuestion.from_db_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to find questions by user: {e}")
            return []
    
    def delete(self, question_id: str) -> bool:
        """
        Delete custom question by ID
        
        Args:
            question_id: Question ID to delete
            
        Returns:
            True if delete successful, False otherwise
        """
        try:
            query = "DELETE FROM custom_questions WHERE id = ?"
            rows_affected = self.db_manager.execute_update(query, (question_id,))
            return rows_affected > 0
            
        except Exception as e:
            logger.error(f"Failed to delete custom question: {e}")
            return False
    
    def get_categories(self, user_id: str) -> List[str]:
        """
        Get all unique categories for a user
        
        Args:
            user_id: User ID to get categories for
            
        Returns:
            List of unique category names
        """
        try:
            query = """
                SELECT DISTINCT category 
                FROM custom_questions 
                WHERE user_id = ?
                ORDER BY category
            """
            results = self.db_manager.execute_query(query, (user_id,))
            return [row['category'] for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []
    
    def get_topics(self, user_id: str) -> List[str]:
        """
        Get all unique topics for a user
        
        Args:
            user_id: User ID to get topics for
            
        Returns:
            List of unique topic names
        """
        try:
            query = """
                SELECT DISTINCT topic 
                FROM custom_questions 
                WHERE user_id = ? AND topic IS NOT NULL
                ORDER BY topic
            """
            results = self.db_manager.execute_query(query, (user_id,))
            return [row['topic'] for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get topics: {e}")
            return []
