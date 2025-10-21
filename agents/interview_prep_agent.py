"""
Interview Prep Agent for generating interview questions, conducting mock interviews,
and managing custom Q&A library.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from models.job import JobListing
from models.question import CustomQuestion
from database.repositories.question_repository import QuestionRepository
from utils.llm_client import OllamaClient, LLMResponse
from utils.prompts import (
    interview_question_prompt,
    ideal_answer_prompt,
    answer_evaluation_prompt
)

logger = logging.getLogger(__name__)


@dataclass
class Question:
    """Interview question with metadata"""
    text: str
    category: str
    difficulty: str
    topic: Optional[str] = None


@dataclass
class InterviewSession:
    """Mock interview session data"""
    questions: List[Question]
    answers: List[str]
    feedback: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class Feedback:
    """Answer evaluation feedback"""
    rating: float
    strengths: List[str]
    improvements: List[str]
    suggestions: List[str]
    improved_version: str


class InterviewPrepAgent:
    """Agent for interview preparation and question management"""
    
    def __init__(
        self,
        llm_client: OllamaClient,
        question_repository: QuestionRepository
    ):
        """
        Initialize Interview Prep Agent
        
        Args:
            llm_client: LLM client for question generation and evaluation
            question_repository: Repository for custom question storage
        """
        self.llm_client = llm_client
        self.question_repo = question_repository
    
    def generate_questions(
        self,
        job: JobListing,
        question_type: str = "technical",
        difficulty: str = "medium",
        count: int = 10
    ) -> List[Question]:
        """
        Generate interview questions based on job description
        
        Args:
            job: JobListing to generate questions for
            question_type: Type of questions (technical, behavioral, system_design)
            difficulty: Difficulty level (easy, medium, hard)
            count: Number of questions to generate
            
        Returns:
            List of Question objects
            
        Raises:
            ValueError: If invalid question_type or difficulty
            Exception: If LLM generation fails
        """
        # Validate inputs
        valid_types = ["technical", "behavioral", "system_design"]
        valid_difficulties = ["easy", "medium", "hard"]
        
        if question_type not in valid_types:
            raise ValueError(f"Invalid question_type: {question_type}. Must be one of {valid_types}")
        
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")
        
        if count < 1 or count > 50:
            raise ValueError("Count must be between 1 and 50")
        
        logger.info(f"Generating {count} {difficulty} {question_type} questions for {job.title} at {job.company}")
        
        try:
            # Generate prompt
            prompts = interview_question_prompt(
                job_title=job.title,
                job_description=job.description,
                question_type=question_type,
                difficulty=difficulty,
                count=count
            )
            
            # Call LLM
            response = self.llm_client.generate_with_retry(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response into Question objects
            questions = self._parse_questions_from_response(
                response,
                question_type,
                difficulty
            )
            
            logger.info(f"Successfully generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            raise Exception(f"Question generation failed: {str(e)}")
    
    def _parse_questions_from_response(
        self,
        response: LLMResponse,
        question_type: str,
        difficulty: str
    ) -> List[Question]:
        """
        Parse LLM response into Question objects
        
        Args:
            response: LLM response containing questions
            question_type: Type of questions
            difficulty: Difficulty level
            
        Returns:
            List of Question objects
        """
        questions = []
        lines = response.text.strip().split('\n')
        
        current_question = None
        current_category = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for question marker (Q1:, Q2:, **Q1:**, etc.)
            if line.startswith('**Q') or line.startswith('Q'):
                # Extract question text
                # Handle formats like "**Q1: Question text**" or "Q1: Question text"
                if '**Q' in line:
                    # Remove markdown bold
                    line = line.replace('**', '')
                
                # Extract question number and text
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        question_text = parts[1].strip()
                        
                        # Save previous question if exists
                        if current_question:
                            questions.append(Question(
                                text=current_question,
                                category=current_category or question_type,
                                difficulty=difficulty,
                                topic=current_category
                            ))
                        
                        current_question = question_text
                        current_category = None
            
            # Check for category marker
            elif line.startswith('Category:'):
                category_text = line.split(':', 1)[1].strip()
                # Remove quotes if present
                category_text = category_text.strip('"\'')
                current_category = category_text
            
            # Check for topic marker (alternative to category)
            elif line.startswith('Topic:'):
                topic_text = line.split(':', 1)[1].strip()
                topic_text = topic_text.strip('"\'')
                current_category = topic_text
        
        # Add last question
        if current_question:
            questions.append(Question(
                text=current_question,
                category=current_category or question_type,
                difficulty=difficulty,
                topic=current_category
            ))
        
        return questions

    def conduct_mock_interview(
        self,
        questions: List[Question],
        user_answers: List[str]
    ) -> InterviewSession:
        """
        Conduct mock interview session with provided questions and answers
        
        Args:
            questions: List of questions to ask
            user_answers: List of user's answers (must match questions length)
            
        Returns:
            InterviewSession with feedback for each answer
            
        Raises:
            ValueError: If questions and answers length mismatch
        """
        if len(questions) != len(user_answers):
            raise ValueError(f"Questions ({len(questions)}) and answers ({len(user_answers)}) count mismatch")
        
        logger.info(f"Starting mock interview with {len(questions)} questions")
        
        session = InterviewSession(
            questions=questions,
            answers=user_answers,
            feedback=[],
            started_at=datetime.now()
        )
        
        # Evaluate each answer
        for i, (question, answer) in enumerate(zip(questions, user_answers)):
            logger.info(f"Evaluating answer {i+1}/{len(questions)}")
            
            try:
                feedback = self.evaluate_answer(
                    question=question.text,
                    user_answer=answer,
                    question_category=question.category
                )
                
                # Format feedback as text
                feedback_text = self._format_feedback(feedback)
                session.feedback.append(feedback_text)
                
            except Exception as e:
                logger.error(f"Failed to evaluate answer {i+1}: {e}")
                session.feedback.append(f"Error evaluating answer: {str(e)}")
        
        session.completed_at = datetime.now()
        logger.info("Mock interview completed")
        
        return session
    
    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        question_category: str = "technical"
    ) -> Feedback:
        """
        Evaluate user's answer to an interview question
        
        Args:
            question: The interview question
            user_answer: User's answer to evaluate
            question_category: Category of the question
            
        Returns:
            Feedback object with evaluation results
            
        Raises:
            Exception: If LLM evaluation fails
        """
        logger.info(f"Evaluating answer for question: {question[:50]}...")
        
        try:
            # Generate evaluation prompt
            prompts = answer_evaluation_prompt(
                question=question,
                user_answer=user_answer,
                question_category=question_category
            )
            
            # Call LLM
            response = self.llm_client.generate_with_retry(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.5,
                max_tokens=1500
            )
            
            # Parse feedback from response
            feedback = self._parse_feedback_from_response(response)
            
            logger.info(f"Answer evaluated with rating: {feedback.rating}/10")
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to evaluate answer: {e}")
            raise Exception(f"Answer evaluation failed: {str(e)}")
    
    def _parse_feedback_from_response(self, response: LLMResponse) -> Feedback:
        """
        Parse LLM response into Feedback object
        
        Args:
            response: LLM response containing feedback
            
        Returns:
            Feedback object
        """
        text = response.text
        
        # Extract rating
        rating = 7.0  # Default
        for line in text.split('\n'):
            if "rating:" in line.lower():
                # Extract number (e.g., "7/10" or "7.5/10" or "**RATING:** 7.5/10")
                parts = line.split(':')
                if len(parts) >= 2:
                    rating_part = parts[-1].strip()
                    # Remove any markdown formatting
                    rating_part = rating_part.replace('*', '').strip()
                    if '/' in rating_part:
                        rating_str = rating_part.split('/')[0].strip()
                        try:
                            rating = float(rating_str)
                        except ValueError:
                            pass
                break
        
        # Extract strengths
        strengths = []
        if "STRENGTHS:" in text or "Strengths:" in text:
            in_section = False
            for line in text.split('\n'):
                if "strengths:" in line.lower():
                    in_section = True
                    continue
                if in_section:
                    if line.strip().startswith('-') or line.strip().startswith('•'):
                        strengths.append(line.strip().lstrip('-•').strip())
                    elif line.strip().startswith('**') and ':' in line:
                        break
                    elif not line.strip():
                        continue
                    else:
                        if line.strip() and not line.strip().startswith('**'):
                            strengths.append(line.strip())
        
        # Extract improvements
        improvements = []
        if "AREAS FOR IMPROVEMENT:" in text or "Areas for Improvement:" in text or "IMPROVEMENTS:" in text:
            in_section = False
            for line in text.split('\n'):
                if "improvement" in line.lower() and ':' in line:
                    in_section = True
                    continue
                if in_section:
                    if line.strip().startswith('-') or line.strip().startswith('•'):
                        improvements.append(line.strip().lstrip('-•').strip())
                    elif line.strip().startswith('**') and ':' in line:
                        break
                    elif not line.strip():
                        continue
                    else:
                        if line.strip() and not line.strip().startswith('**'):
                            improvements.append(line.strip())
        
        # Extract suggestions
        suggestions = []
        if "SUGGESTIONS:" in text or "Suggestions:" in text:
            in_section = False
            for line in text.split('\n'):
                if "suggestions:" in line.lower():
                    in_section = True
                    continue
                if in_section:
                    if line.strip().startswith('-') or line.strip().startswith('•'):
                        suggestions.append(line.strip().lstrip('-•').strip())
                    elif line.strip().startswith('**') and ':' in line:
                        break
                    elif not line.strip():
                        continue
                    else:
                        if line.strip() and not line.strip().startswith('**'):
                            suggestions.append(line.strip())
        
        # Extract improved version
        improved_version = ""
        # Try different variations of the header
        for header in ["**IMPROVED VERSION:**", "IMPROVED VERSION:", "**Improved Version:**", "Improved Version:"]:
            if header in text:
                parts = text.split(header)
                if len(parts) >= 2:
                    improved_version = parts[1].strip()
                    # Remove any trailing sections that start with **
                    next_section = improved_version.find("\n**")
                    if next_section > 0:
                        improved_version = improved_version[:next_section].strip()
                    break
        
        return Feedback(
            rating=rating,
            strengths=strengths if strengths else ["Answer provided relevant information"],
            improvements=improvements if improvements else ["Could provide more specific examples"],
            suggestions=suggestions if suggestions else ["Consider adding concrete examples"],
            improved_version=improved_version
        )
    
    def _format_feedback(self, feedback: Feedback) -> str:
        """
        Format Feedback object as readable text
        
        Args:
            feedback: Feedback object
            
        Returns:
            Formatted feedback string
        """
        lines = [
            f"Rating: {feedback.rating}/10",
            "",
            "Strengths:",
        ]
        for strength in feedback.strengths:
            lines.append(f"  - {strength}")
        
        lines.append("")
        lines.append("Areas for Improvement:")
        for improvement in feedback.improvements:
            lines.append(f"  - {improvement}")
        
        lines.append("")
        lines.append("Suggestions:")
        for suggestion in feedback.suggestions:
            lines.append(f"  - {suggestion}")
        
        if feedback.improved_version:
            lines.append("")
            lines.append("Improved Version:")
            lines.append(feedback.improved_version)
        
        return "\n".join(lines)
    
    def add_custom_question(
        self,
        user_id: str,
        question_text: str,
        category: str,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        user_answer: Optional[str] = None
    ) -> CustomQuestion:
        """
        Add custom interview question to user's library
        
        Args:
            user_id: User ID
            question_text: Question text
            category: Question category (technical, behavioral, system_design)
            topic: Optional topic (e.g., "LangChain", "RAG")
            difficulty: Optional difficulty (easy, medium, hard)
            user_answer: Optional user's answer
            
        Returns:
            Created CustomQuestion object
            
        Raises:
            ValueError: If validation fails
            Exception: If database save fails
        """
        logger.info(f"Adding custom question for user {user_id}")
        
        try:
            # Create CustomQuestion object (validation happens in __post_init__)
            question = CustomQuestion(
                user_id=user_id,
                question_text=question_text,
                category=category,
                topic=topic,
                difficulty=difficulty,
                user_answer=user_answer
            )
            
            # Save to database
            success = self.question_repo.save(question)
            
            if not success:
                raise Exception("Failed to save question to database")
            
            logger.info(f"Custom question saved with ID: {question.id}")
            return question
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to add custom question: {e}")
            raise Exception(f"Failed to add custom question: {str(e)}")
    
    def generate_ideal_answer(
        self,
        question: str,
        question_category: str = "technical"
    ) -> str:
        """
        Generate ideal answer for a question using LLM
        
        Args:
            question: The interview question
            question_category: Category of the question
            
        Returns:
            Generated ideal answer text
            
        Raises:
            Exception: If LLM generation fails
        """
        logger.info(f"Generating ideal answer for question: {question[:50]}...")
        
        try:
            # Generate prompt
            prompts = ideal_answer_prompt(
                question=question,
                question_category=question_category
            )
            
            # Call LLM
            response = self.llm_client.generate_with_retry(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.7,
                max_tokens=1000
            )
            
            ideal_answer = response.text.strip()
            
            logger.info(f"Generated ideal answer ({len(ideal_answer)} characters)")
            return ideal_answer
            
        except Exception as e:
            logger.error(f"Failed to generate ideal answer: {e}")
            raise Exception(f"Ideal answer generation failed: {str(e)}")
    
    def get_custom_questions(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CustomQuestion]:
        """
        Get custom questions with optional filtering
        
        Args:
            user_id: User ID
            filters: Optional filters (category, topic, difficulty)
            
        Returns:
            List of CustomQuestion objects
        """
        logger.info(f"Retrieving custom questions for user {user_id} with filters: {filters}")
        
        try:
            questions = self.question_repo.find_by_user(user_id, filters)
            logger.info(f"Retrieved {len(questions)} custom questions")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to retrieve custom questions: {e}")
            return []
    
    def update_custom_question(
        self,
        question_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update custom question
        
        Args:
            question_id: Question ID to update
            updates: Dictionary with fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        logger.info(f"Updating custom question {question_id}")
        
        try:
            # Retrieve existing question
            question = self.question_repo.find_by_id(question_id)
            
            if not question:
                logger.error(f"Question {question_id} not found")
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(question, key):
                    setattr(question, key, value)
            
            # Update timestamp
            question.updated_at = datetime.now()
            
            # Validate and save
            question.validate()
            success = self.question_repo.update(question)
            
            if success:
                logger.info(f"Question {question_id} updated successfully")
            else:
                logger.error(f"Failed to update question {question_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update custom question: {e}")
            return False
    
    def link_question_to_job(
        self,
        question_id: str,
        job_id: str
    ) -> bool:
        """
        Link custom question to specific job application
        
        Note: This is a placeholder for future implementation.
        The database schema would need a junction table to support this.
        
        Args:
            question_id: Question ID
            job_id: Job ID
            
        Returns:
            True if link successful, False otherwise
        """
        logger.info(f"Linking question {question_id} to job {job_id}")
        
        # For now, we can store this in the question's notes or a custom field
        # A proper implementation would require a junction table
        
        try:
            question = self.question_repo.find_by_id(question_id)
            
            if not question:
                logger.error(f"Question {question_id} not found")
                return False
            
            # Store job_id in topic field as a workaround
            # In production, this should use a proper junction table
            if not question.topic:
                question.topic = f"job:{job_id}"
            elif f"job:{job_id}" not in question.topic:
                question.topic = f"{question.topic},job:{job_id}"
            
            question.updated_at = datetime.now()
            success = self.question_repo.update(question)
            
            if success:
                logger.info(f"Question {question_id} linked to job {job_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to link question to job: {e}")
            return False
    
    def get_questions_for_job(
        self,
        user_id: str,
        job_id: str
    ) -> List[CustomQuestion]:
        """
        Get custom questions linked to specific job
        
        Args:
            user_id: User ID
            job_id: Job ID
            
        Returns:
            List of CustomQuestion objects linked to the job
        """
        logger.info(f"Retrieving questions for job {job_id}")
        
        try:
            # Get all user questions
            all_questions = self.question_repo.find_by_user(user_id)
            
            # Filter by job_id in topic field
            job_questions = [
                q for q in all_questions
                if q.topic and f"job:{job_id}" in q.topic
            ]
            
            logger.info(f"Found {len(job_questions)} questions for job {job_id}")
            return job_questions
            
        except Exception as e:
            logger.error(f"Failed to retrieve questions for job: {e}")
            return []
