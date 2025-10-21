"""
Match Scorer Agent for calculating job-candidate alignment scores
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
from models.job import JobListing
from models.user import UserProfile
from models.match_score import MatchScore
from models.company import CompanyProfile
from database.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class MatchScorer:
    """
    Agent responsible for calculating job relevance scores based on multiple factors.
    
    Scoring Algorithm:
    Total Score = (Skills Match × 0.35) + (Salary Match × 0.25) + 
                  (Tech Stack Match × 0.20) + (Remote Flexibility × 0.10) + 
                  (Company Profile × 0.10)
    """
    
    # Scoring weights
    WEIGHTS = {
        'skills_match': 0.35,
        'salary_match': 0.25,
        'tech_stack_match': 0.20,
        'remote_flexibility': 0.10,
        'company_profile': 0.10
    }
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        """
        Initialize match scorer
        
        Args:
            job_repository: Optional job repository for updating scores
        """
        self.job_repository = job_repository
    
    def calculate_score(self, job: JobListing, user_profile: UserProfile, 
                       company_profile: Optional[CompanyProfile] = None) -> MatchScore:
        """
        Calculate overall match score for a job listing
        
        Args:
            job: Job listing to score
            user_profile: User profile with preferences and skills
            company_profile: Optional company profile for company scoring
            
        Returns:
            MatchScore object with total score and breakdown
        """
        try:
            # Calculate individual component scores
            skills_score = self.calculate_skills_match(job, user_profile)
            salary_score = self.calculate_salary_match(job, user_profile)
            tech_stack_score = self.calculate_tech_stack_match(job, user_profile)
            remote_score = self.calculate_remote_flexibility(job, user_profile)
            company_score = self.calculate_company_profile_score(company_profile)
            
            # Calculate weighted total score
            total_score = (
                skills_score * self.WEIGHTS['skills_match'] +
                salary_score * self.WEIGHTS['salary_match'] +
                tech_stack_score * self.WEIGHTS['tech_stack_match'] +
                remote_score * self.WEIGHTS['remote_flexibility'] +
                company_score * self.WEIGHTS['company_profile']
            )
            
            # Create detailed breakdown
            breakdown = {
                'skills_match_details': {
                    'score': skills_score,
                    'weight': self.WEIGHTS['skills_match'],
                    'contribution': skills_score * self.WEIGHTS['skills_match']
                },
                'salary_match_details': {
                    'score': salary_score,
                    'weight': self.WEIGHTS['salary_match'],
                    'contribution': salary_score * self.WEIGHTS['salary_match']
                },
                'tech_stack_match_details': {
                    'score': tech_stack_score,
                    'weight': self.WEIGHTS['tech_stack_match'],
                    'contribution': tech_stack_score * self.WEIGHTS['tech_stack_match']
                },
                'remote_flexibility_details': {
                    'score': remote_score,
                    'weight': self.WEIGHTS['remote_flexibility'],
                    'contribution': remote_score * self.WEIGHTS['remote_flexibility']
                },
                'company_profile_details': {
                    'score': company_score,
                    'weight': self.WEIGHTS['company_profile'],
                    'contribution': company_score * self.WEIGHTS['company_profile']
                }
            }
            
            match_score = MatchScore(
                job_id=job.id,
                total_score=round(total_score, 2),
                skills_match=round(skills_score, 2),
                salary_match=round(salary_score, 2),
                tech_stack_match=round(tech_stack_score, 2),
                remote_flexibility=round(remote_score, 2),
                company_profile_score=round(company_score, 2),
                breakdown=breakdown
            )
            
            logger.info(f"Calculated match score for job {job.id}: {match_score.total_score}")
            return match_score
            
        except Exception as e:
            logger.error(f"Failed to calculate match score for job {job.id}: {e}")
            # Return a default low score on error
            return MatchScore(
                job_id=job.id,
                total_score=0.0,
                skills_match=0.0,
                salary_match=0.0,
                tech_stack_match=0.0,
                remote_flexibility=0.0,
                company_profile_score=0.0
            )
    
    def calculate_skills_match(self, job: JobListing, user_profile: UserProfile) -> float:
        """
        Calculate skills match score based on overlap between required and user skills
        
        Args:
            job: Job listing with required skills
            user_profile: User profile with skills
            
        Returns:
            Score from 0 to 100
        """
        if not job.required_skills or not user_profile.skills:
            return 0.0
        
        # Normalize skills to lowercase for comparison
        required_skills = set(skill.lower().strip() for skill in job.required_skills)
        user_skills = set(skill.lower().strip() for skill in user_profile.skills)
        
        if not required_skills:
            return 100.0  # No specific requirements means perfect match
        
        # Calculate overlap
        matching_skills = required_skills.intersection(user_skills)
        match_percentage = (len(matching_skills) / len(required_skills)) * 100
        
        logger.debug(f"Skills match: {len(matching_skills)}/{len(required_skills)} = {match_percentage}%")
        return min(match_percentage, 100.0)
    
    def calculate_salary_match(self, job: JobListing, user_profile: UserProfile) -> float:
        """
        Calculate salary match score based on how close job salary is to target
        
        Args:
            job: Job listing with salary range
            user_profile: User profile with target salary
            
        Returns:
            Score from 0 to 100
        """
        if user_profile.target_salary == 0:
            return 100.0  # No preference means perfect match
        
        # Use salary_max if available, otherwise salary_min
        job_salary = job.salary_max if job.salary_max else job.salary_min
        
        if not job_salary:
            return 50.0  # Unknown salary gets neutral score
        
        target = user_profile.target_salary
        
        # Calculate score based on how close to target
        if job_salary >= target:
            # Job pays at or above target - excellent match
            # Give 100% for exact match, scale up to 100% for higher salaries
            excess_percentage = ((job_salary - target) / target) * 100
            score = 100.0 + min(excess_percentage * 0.1, 10.0)  # Bonus up to 10 points
            return min(score, 100.0)
        else:
            # Job pays below target - score decreases linearly
            # 90% of target = 90 points, 80% = 80 points, etc.
            percentage_of_target = (job_salary / target) * 100
            return max(percentage_of_target, 0.0)
    
    def calculate_tech_stack_match(self, job: JobListing, user_profile: UserProfile) -> float:
        """
        Calculate tech stack match score based on desired technologies
        
        Args:
            job: Job listing with description and required skills
            user_profile: User profile with desired tech stack
            
        Returns:
            Score from 0 to 100
        """
        if not user_profile.desired_tech_stack:
            return 100.0  # No preference means perfect match
        
        # Normalize desired tech stack
        desired_tech = set(tech.lower().strip() for tech in user_profile.desired_tech_stack)
        
        # Check job description and required skills for tech stack mentions
        job_text = (job.description + " " + " ".join(job.required_skills)).lower()
        
        matching_tech = sum(1 for tech in desired_tech if tech in job_text)
        
        if not desired_tech:
            return 100.0
        
        match_percentage = (matching_tech / len(desired_tech)) * 100
        
        logger.debug(f"Tech stack match: {matching_tech}/{len(desired_tech)} = {match_percentage}%")
        return min(match_percentage, 100.0)
    
    def calculate_remote_flexibility(self, job: JobListing, user_profile: UserProfile) -> float:
        """
        Calculate remote flexibility score based on user preference
        
        Args:
            job: Job listing with remote type
            user_profile: User profile with remote preference
            
        Returns:
            Score from 0 to 100
        """
        if not user_profile.preferred_remote:
            return 100.0  # No preference means perfect match
        
        # Score based on remote type
        remote_scores = {
            'remote': 100.0,
            'hybrid': 70.0,
            'onsite': 30.0
        }
        
        score = remote_scores.get(job.remote_type.lower(), 50.0)
        logger.debug(f"Remote flexibility score for {job.remote_type}: {score}")
        return score
    
    def calculate_company_profile_score(self, company_profile: Optional[CompanyProfile]) -> float:
        """
        Calculate company profile score based on rating and GenAI focus
        
        Args:
            company_profile: Optional company profile with ratings
            
        Returns:
            Score from 0 to 100
        """
        if not company_profile:
            return 50.0  # Unknown company gets neutral score
        
        # Weight Glassdoor rating (60%) and GenAI focus (40%)
        glassdoor_score = 0.0
        if company_profile.glassdoor_rating:
            # Convert 0-5 rating to 0-100 scale
            glassdoor_score = (company_profile.glassdoor_rating / 5.0) * 100
        else:
            glassdoor_score = 50.0  # No rating gets neutral score
        
        # Convert 0-10 GenAI focus to 0-100 scale
        genai_score = (company_profile.genai_focus_score / 10.0) * 100
        
        total_score = (glassdoor_score * 0.6) + (genai_score * 0.4)
        
        logger.debug(f"Company profile score: {total_score} (Glassdoor: {glassdoor_score}, GenAI: {genai_score})")
        return round(total_score, 2)
    
    def get_score_breakdown(self, match_score: MatchScore) -> Dict[str, Any]:
        """
        Get detailed breakdown of score components with explanations
        
        Args:
            match_score: MatchScore object to explain
            
        Returns:
            Dictionary with detailed breakdown and explanations
        """
        breakdown = {
            'total_score': match_score.total_score,
            'components': {
                'skills_match': {
                    'score': match_score.skills_match,
                    'weight': self.WEIGHTS['skills_match'],
                    'contribution': round(match_score.skills_match * self.WEIGHTS['skills_match'], 2),
                    'explanation': f"Skills alignment: {match_score.skills_match}% of required skills matched"
                },
                'salary_match': {
                    'score': match_score.salary_match,
                    'weight': self.WEIGHTS['salary_match'],
                    'contribution': round(match_score.salary_match * self.WEIGHTS['salary_match'], 2),
                    'explanation': f"Salary alignment: {match_score.salary_match}% match with target"
                },
                'tech_stack_match': {
                    'score': match_score.tech_stack_match,
                    'weight': self.WEIGHTS['tech_stack_match'],
                    'contribution': round(match_score.tech_stack_match * self.WEIGHTS['tech_stack_match'], 2),
                    'explanation': f"Technology stack: {match_score.tech_stack_match}% of desired technologies present"
                },
                'remote_flexibility': {
                    'score': match_score.remote_flexibility,
                    'weight': self.WEIGHTS['remote_flexibility'],
                    'contribution': round(match_score.remote_flexibility * self.WEIGHTS['remote_flexibility'], 2),
                    'explanation': f"Remote work flexibility: {match_score.remote_flexibility}% alignment"
                },
                'company_profile': {
                    'score': match_score.company_profile_score,
                    'weight': self.WEIGHTS['company_profile'],
                    'contribution': round(match_score.company_profile_score * self.WEIGHTS['company_profile'], 2),
                    'explanation': f"Company quality: {match_score.company_profile_score}% based on ratings and focus"
                }
            },
            'detailed_breakdown': match_score.breakdown
        }
        
        return breakdown
    
    def rank_jobs(self, jobs: List[JobListing], user_profile: UserProfile,
                  company_profiles: Optional[Dict[str, CompanyProfile]] = None) -> List[Tuple[JobListing, MatchScore]]:
        """
        Rank jobs by match score in descending order
        
        Args:
            jobs: List of job listings to rank
            user_profile: User profile for scoring
            company_profiles: Optional dictionary mapping company names to profiles
            
        Returns:
            List of tuples (JobListing, MatchScore) sorted by score descending
        """
        scored_jobs = []
        
        for job in jobs:
            # Get company profile if available
            company_profile = None
            if company_profiles and job.company in company_profiles:
                company_profile = company_profiles[job.company]
            
            # Calculate score
            match_score = self.calculate_score(job, user_profile, company_profile)
            scored_jobs.append((job, match_score))
        
        # Sort by total score descending
        ranked_jobs = sorted(scored_jobs, key=lambda x: x[1].total_score, reverse=True)
        
        logger.info(f"Ranked {len(ranked_jobs)} jobs by match score")
        return ranked_jobs
    
    def update_job_scores(self, jobs: List[JobListing], user_profile: UserProfile,
                         company_profiles: Optional[Dict[str, CompanyProfile]] = None) -> int:
        """
        Calculate and update match scores for multiple jobs in database
        
        Args:
            jobs: List of job listings to score
            user_profile: User profile for scoring
            company_profiles: Optional dictionary mapping company names to profiles
            
        Returns:
            Number of jobs successfully updated
        """
        if not self.job_repository:
            logger.warning("No job repository provided, cannot update scores")
            return 0
        
        updated_count = 0
        
        for job in jobs:
            try:
                # Get company profile if available
                company_profile = None
                if company_profiles and job.company in company_profiles:
                    company_profile = company_profiles[job.company]
                
                # Calculate score
                match_score = self.calculate_score(job, user_profile, company_profile)
                
                # Update in database
                if self.job_repository.update_match_score(job.id, match_score.total_score):
                    updated_count += 1
                    logger.debug(f"Updated match score for job {job.id}: {match_score.total_score}")
                
            except Exception as e:
                logger.error(f"Failed to update score for job {job.id}: {e}")
                continue
        
        logger.info(f"Updated match scores for {updated_count}/{len(jobs)} jobs")
        return updated_count
