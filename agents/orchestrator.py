"""
LangGraph Orchestrator for Agent Coordination
Implements workflows for job search, resume optimization, cover letter generation,
interview prep, and company profiling.
"""

import logging
from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.job_search_agent import JobSearchAgent, SearchCriteria
from agents.match_scorer import MatchScorer
from agents.resume_optimizer import ResumeOptimizer
from agents.cover_letter_generator import CoverLetterGenerator
from agents.interview_prep_agent import InterviewPrepAgent
from agents.company_profiler import CompanyProfiler
from agents.job_tracker import JobTracker
from utils.notification_manager import UnifiedNotificationService
from models.job import JobListing
from models.user import UserProfile
from models.application import Application

logger = logging.getLogger(__name__)


# State definitions for different workflows
# Using Dict instead of TypedDict for better serialization compatibility
DailySearchState = Dict[str, Any]
ResumeOptimizationState = Dict[str, Any]
CoverLetterState = Dict[str, Any]
InterviewPrepState = Dict[str, Any]
CompanyProfileState = Dict[str, Any]


class LangGraphOrchestrator:
    """
    Orchestrator for coordinating multiple agents using LangGraph.
    Implements workflows for various job search and preparation tasks.
    """
    
    def __init__(
        self,
        job_search_agent: JobSearchAgent,
        match_scorer: MatchScorer,
        resume_optimizer: ResumeOptimizer,
        cover_letter_generator: CoverLetterGenerator,
        interview_prep_agent: InterviewPrepAgent,
        company_profiler: CompanyProfiler,
        job_tracker: Optional[JobTracker] = None,
        notification_service: Optional[UnifiedNotificationService] = None
    ):
        """
        Initialize LangGraph Orchestrator with all agents.
        
        Args:
            job_search_agent: Agent for job discovery
            match_scorer: Agent for scoring job matches
            resume_optimizer: Agent for resume optimization
            cover_letter_generator: Agent for cover letter generation
            interview_prep_agent: Agent for interview preparation
            company_profiler: Agent for company profiling
            job_tracker: Optional job tracker for application management
            notification_service: Optional notification service
        """
        self.job_search_agent = job_search_agent
        self.match_scorer = match_scorer
        self.resume_optimizer = resume_optimizer
        self.cover_letter_generator = cover_letter_generator
        self.interview_prep_agent = interview_prep_agent
        self.company_profiler = company_profiler
        self.job_tracker = job_tracker
        self.notification_service = notification_service
        
        logger.info("LangGraphOrchestrator initialized with all agents")
    
    # ==================== Daily Search Workflow ====================
    
    def _search_jobs_node(self, state: DailySearchState) -> DailySearchState:
        """Node: Search for jobs using JobSearchAgent"""
        try:
            logger.info("Executing job search node")
            
            if not state.get("search_criteria"):
                state["error"] = "Search criteria not provided"
                return state
            
            # Execute job search
            jobs = self.job_search_agent.search(state["search_criteria"])
            state["jobs_found"] = jobs
            
            logger.info(f"Found {len(jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Job search node failed: {e}")
            state["error"] = str(e)
            state["jobs_found"] = []
        
        return state
    
    def _score_jobs_node(self, state: DailySearchState) -> DailySearchState:
        """Node: Score jobs using MatchScorer"""
        try:
            logger.info("Executing job scoring node")
            
            if not state.get("jobs_found"):
                logger.info("No jobs to score")
                state["jobs_scored"] = []
                return state
            
            if not state.get("user_profile"):
                state["error"] = "User profile not provided"
                return state
            
            # Score and rank jobs
            scored_jobs = self.match_scorer.rank_jobs(
                state["jobs_found"],
                state["user_profile"]
            )
            state["jobs_scored"] = scored_jobs
            
            # Update job scores in database
            self.match_scorer.update_job_scores(
                state["jobs_found"],
                state["user_profile"]
            )
            
            logger.info(f"Scored {len(scored_jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Job scoring node failed: {e}")
            state["error"] = str(e)
            state["jobs_scored"] = []
        
        return state
    
    def _notify_user_node(self, state: DailySearchState) -> DailySearchState:
        """Node: Send notifications using NotificationManager"""
        try:
            logger.info("Executing notification node")
            
            if not self.notification_service:
                logger.warning("Notification service not configured")
                state["notification_sent"] = False
                return state
            
            if not state.get("jobs_scored"):
                logger.info("No jobs to notify about")
                state["notification_sent"] = True
                return state
            
            # Extract jobs from scored tuples
            jobs = [job for job, score in state["jobs_scored"]]
            
            # Send daily digest
            results = self.notification_service.send_daily_digest(
                state["user_id"],
                jobs
            )
            
            state["notification_sent"] = results.get("email", False) or results.get("whatsapp", False)
            
            logger.info(f"Notification sent: {state['notification_sent']}")
            
        except Exception as e:
            logger.error(f"Notification node failed: {e}")
            state["error"] = str(e)
            state["notification_sent"] = False
        
        return state
    
    def execute_daily_search(
        self,
        search_criteria: SearchCriteria,
        user_profile: UserProfile,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute daily job search workflow: JobSearch → MatchScorer → NotificationManager
        
        Args:
            search_criteria: Search criteria for job discovery
            user_profile: User profile for scoring
            user_id: User ID for notifications
            
        Returns:
            Dictionary with workflow results
        """
        try:
            logger.info("Starting daily search workflow")
            
            # Build workflow graph
            workflow = StateGraph(DailySearchState)
            
            # Add nodes
            workflow.add_node("search_jobs", self._search_jobs_node)
            workflow.add_node("score_jobs", self._score_jobs_node)
            workflow.add_node("notify_user", self._notify_user_node)
            
            # Define edges
            workflow.set_entry_point("search_jobs")
            workflow.add_edge("search_jobs", "score_jobs")
            workflow.add_edge("score_jobs", "notify_user")
            workflow.add_edge("notify_user", END)
            
            # Compile graph
            app = workflow.compile()
            
            # Initialize state
            initial_state = {
                "search_criteria": search_criteria,
                "user_profile": user_profile,
                "user_id": user_id,
                "jobs_found": [],
                "jobs_scored": [],
                "notification_sent": False,
                "error": None
            }
            
            # Execute workflow
            final_state = app.invoke(initial_state)
            
            # Prepare results
            results = {
                "success": final_state.get("error") is None,
                "jobs_found": len(final_state.get("jobs_found", [])),
                "jobs_scored": len(final_state.get("jobs_scored", [])),
                "notification_sent": final_state.get("notification_sent", False),
                "error": final_state.get("error"),
                "jobs": final_state.get("jobs_found", [])
            }
            
            logger.info(f"Daily search workflow completed: {results['jobs_found']} jobs found")
            return results
            
        except Exception as e:
            logger.error(f"Daily search workflow failed: {e}")
            return {
                "success": False,
                "jobs_found": 0,
                "jobs_scored": 0,
                "notification_sent": False,
                "error": str(e),
                "jobs": []
            }
    
    # ==================== Resume Optimization Workflow ====================
    
    def _load_job_node(self, state: ResumeOptimizationState) -> ResumeOptimizationState:
        """Node: Load job details from database"""
        try:
            logger.info(f"Loading job {state['job_id']}")
            
            # Get job from database via job repository
            if hasattr(self.match_scorer, 'job_repository') and self.match_scorer.job_repository:
                job = self.match_scorer.job_repository.find_by_id(state["job_id"])
                state["job"] = job
                
                if not job:
                    state["error"] = f"Job {state['job_id']} not found"
            else:
                state["error"] = "Job repository not available"
            
        except Exception as e:
            logger.error(f"Load job node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def _optimize_resume_node(self, state: ResumeOptimizationState) -> ResumeOptimizationState:
        """Node: Optimize resume using ResumeOptimizer"""
        try:
            logger.info("Executing resume optimization node")
            
            if not state.get("job"):
                state["error"] = "Job not loaded"
                return state
            
            # Optimize resume for job
            optimization_result = self.resume_optimizer.optimize_for_job(
                resume_text=state["resume_text"],
                job=state["job"],
                user_id=state["user_id"]
            )
            
            state["optimization_result"] = optimization_result
            
            logger.info("Resume optimization completed")
            
        except Exception as e:
            logger.error(f"Resume optimization node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def optimize_resume(
        self,
        user_id: str,
        resume_text: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Execute resume optimization workflow: Load Job → ResumeOptimizer
        
        Args:
            user_id: User ID
            resume_text: Current resume content
            job_id: Job ID to optimize for
            
        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info(f"Starting resume optimization workflow for job {job_id}")
            
            # Build workflow graph
            workflow = StateGraph(ResumeOptimizationState)
            
            # Add nodes
            workflow.add_node("load_job", self._load_job_node)
            workflow.add_node("optimize_resume", self._optimize_resume_node)
            
            # Define edges
            workflow.set_entry_point("load_job")
            workflow.add_edge("load_job", "optimize_resume")
            workflow.add_edge("optimize_resume", END)
            
            # Compile graph
            app = workflow.compile()
            
            # Initialize state
            initial_state = {
                "user_id": user_id,
                "resume_text": resume_text,
                "job_id": job_id,
                "job": None,
                "optimization_result": None,
                "error": None
            }
            
            # Execute workflow
            final_state = app.invoke(initial_state)
            
            # Prepare results
            results = {
                "success": final_state.get("error") is None,
                "optimization_result": final_state.get("optimization_result"),
                "error": final_state.get("error")
            }
            
            logger.info("Resume optimization workflow completed")
            return results
            
        except Exception as e:
            logger.error(f"Resume optimization workflow failed: {e}")
            return {
                "success": False,
                "optimization_result": None,
                "error": str(e)
            }
    
    # ==================== Cover Letter Generation Workflow ====================
    
    def _generate_cover_letter_node(self, state: CoverLetterState) -> CoverLetterState:
        """Node: Generate cover letter using CoverLetterGenerator"""
        try:
            logger.info("Executing cover letter generation node")
            
            if not state.get("job"):
                state["error"] = "Job not loaded"
                return state
            
            # Generate cover letter
            cover_letter = self.cover_letter_generator.generate(
                job=state["job"],
                resume_summary=state["resume_summary"],
                user_id=state["user_id"],
                relevant_projects=state.get("relevant_projects"),
                tone=state.get("tone", "professional")
            )
            
            state["cover_letter"] = cover_letter
            
            logger.info("Cover letter generated")
            
        except Exception as e:
            logger.error(f"Cover letter generation node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def generate_cover_letter(
        self,
        user_id: str,
        job_id: str,
        resume_summary: str,
        relevant_projects: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Execute cover letter generation workflow: Load Job → CoverLetterGenerator
        
        Args:
            user_id: User ID
            job_id: Job ID to generate letter for
            resume_summary: Summary of candidate's experience
            relevant_projects: Optional list of relevant projects
            tone: Desired tone (professional, enthusiastic, technical)
            
        Returns:
            Dictionary with cover letter results
        """
        try:
            logger.info(f"Starting cover letter generation workflow for job {job_id}")
            
            # Build workflow graph
            workflow = StateGraph(CoverLetterState)
            
            # Add nodes
            workflow.add_node("load_job", lambda state: self._load_job_for_cover_letter(state))
            workflow.add_node("generate_letter", self._generate_cover_letter_node)
            
            # Define edges
            workflow.set_entry_point("load_job")
            workflow.add_edge("load_job", "generate_letter")
            workflow.add_edge("generate_letter", END)
            
            # Compile graph
            app = workflow.compile()
            
            # Initialize state
            initial_state = {
                "user_id": user_id,
                "job_id": job_id,
                "job": None,
                "resume_summary": resume_summary,
                "relevant_projects": relevant_projects,
                "tone": tone,
                "cover_letter": None,
                "error": None
            }
            
            # Execute workflow
            final_state = app.invoke(initial_state)
            
            # Prepare results
            results = {
                "success": final_state.get("error") is None,
                "cover_letter": final_state.get("cover_letter"),
                "error": final_state.get("error")
            }
            
            logger.info("Cover letter generation workflow completed")
            return results
            
        except Exception as e:
            logger.error(f"Cover letter generation workflow failed: {e}")
            return {
                "success": False,
                "cover_letter": None,
                "error": str(e)
            }
    
    def _load_job_for_cover_letter(self, state: CoverLetterState) -> CoverLetterState:
        """Helper to load job for cover letter state"""
        try:
            if hasattr(self.match_scorer, 'job_repository') and self.match_scorer.job_repository:
                job = self.match_scorer.job_repository.find_by_id(state["job_id"])
                state["job"] = job
                if not job:
                    state["error"] = f"Job {state['job_id']} not found"
            else:
                state["error"] = "Job repository not available"
        except Exception as e:
            state["error"] = str(e)
        return state
    
    # ==================== Interview Prep Workflow ====================
    
    def _generate_questions_node(self, state: InterviewPrepState) -> InterviewPrepState:
        """Node: Generate interview questions using InterviewPrepAgent"""
        try:
            logger.info("Executing question generation node")
            
            if not state.get("job"):
                state["error"] = "Job not loaded"
                return state
            
            # Generate questions
            questions = self.interview_prep_agent.generate_questions(
                job=state["job"],
                question_type=state.get("question_type", "technical"),
                difficulty=state.get("difficulty", "medium"),
                count=10
            )
            
            state["questions"] = questions
            
            logger.info(f"Generated {len(questions)} questions")
            
        except Exception as e:
            logger.error(f"Question generation node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def prepare_interview(
        self,
        user_id: str,
        job_id: str,
        question_type: str = "technical",
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Execute interview preparation workflow: Load Job → InterviewPrepAgent
        
        Args:
            user_id: User ID
            job_id: Job ID to prepare for
            question_type: Type of questions (technical, behavioral, system_design)
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Dictionary with interview prep results
        """
        try:
            logger.info(f"Starting interview prep workflow for job {job_id}")
            
            # Build workflow graph
            workflow = StateGraph(InterviewPrepState)
            
            # Add nodes
            workflow.add_node("load_job", lambda state: self._load_job_for_interview(state))
            workflow.add_node("generate_questions", self._generate_questions_node)
            
            # Define edges
            workflow.set_entry_point("load_job")
            workflow.add_edge("load_job", "generate_questions")
            workflow.add_edge("generate_questions", END)
            
            # Compile graph
            app = workflow.compile()
            
            # Initialize state
            initial_state = {
                "user_id": user_id,
                "job_id": job_id,
                "job": None,
                "question_type": question_type,
                "difficulty": difficulty,
                "questions": None,
                "error": None
            }
            
            # Execute workflow
            final_state = app.invoke(initial_state)
            
            # Prepare results
            results = {
                "success": final_state.get("error") is None,
                "questions": final_state.get("questions"),
                "error": final_state.get("error")
            }
            
            logger.info("Interview prep workflow completed")
            return results
            
        except Exception as e:
            logger.error(f"Interview prep workflow failed: {e}")
            return {
                "success": False,
                "questions": None,
                "error": str(e)
            }
    
    def _load_job_for_interview(self, state: InterviewPrepState) -> InterviewPrepState:
        """Helper to load job for interview prep state"""
        try:
            if hasattr(self.match_scorer, 'job_repository') and self.match_scorer.job_repository:
                job = self.match_scorer.job_repository.find_by_id(state["job_id"])
                state["job"] = job
                if not job:
                    state["error"] = f"Job {state['job_id']} not found"
            else:
                state["error"] = "Job repository not available"
        except Exception as e:
            state["error"] = str(e)
        return state
    
    # ==================== Company Profiling Workflow ====================
    
    def _profile_company_node(self, state: CompanyProfileState) -> CompanyProfileState:
        """Node: Profile company using CompanyProfiler"""
        try:
            logger.info(f"Executing company profiling node for {state['company_name']}")
            
            # Profile company (with caching)
            profile = self.company_profiler.profile_company(
                company_name=state["company_name"],
                force_refresh=not state.get("use_cache", True)
            )
            
            state["profile"] = profile
            
            if not profile:
                state["error"] = f"Failed to profile company {state['company_name']}"
            
            logger.info("Company profiling completed")
            
        except Exception as e:
            logger.error(f"Company profiling node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def _generate_fit_summary_node(self, state: CompanyProfileState) -> CompanyProfileState:
        """Node: Generate fit summary using CompanyProfiler"""
        try:
            logger.info("Executing fit summary generation node")
            
            if not state.get("profile"):
                state["error"] = "Company profile not available"
                return state
            
            if not state.get("user_preferences"):
                logger.warning("User preferences not provided, skipping fit summary")
                return state
            
            # Generate fit summary
            fit_summary = self.company_profiler.summarize_fit(
                company_profile=state["profile"],
                user_preferences=state["user_preferences"]
            )
            
            state["fit_summary"] = fit_summary
            
            logger.info("Fit summary generated")
            
        except Exception as e:
            logger.error(f"Fit summary generation node failed: {e}")
            state["error"] = str(e)
        
        return state
    
    def profile_company(
        self,
        company_name: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute company profiling workflow: CompanyProfiler → FitSummary (optional)
        
        Args:
            company_name: Name of company to profile
            user_preferences: Optional user preferences for fit analysis
            use_cache: Whether to use cached profile if available
            
        Returns:
            Dictionary with company profile results
        """
        try:
            logger.info(f"Starting company profiling workflow for {company_name}")
            
            # Build workflow graph
            workflow = StateGraph(CompanyProfileState)
            
            # Add nodes
            workflow.add_node("profile_company", self._profile_company_node)
            workflow.add_node("generate_fit_summary", self._generate_fit_summary_node)
            
            # Define edges
            workflow.set_entry_point("profile_company")
            workflow.add_edge("profile_company", "generate_fit_summary")
            workflow.add_edge("generate_fit_summary", END)
            
            # Compile graph
            app = workflow.compile()
            
            # Initialize state
            initial_state = {
                "company_name": company_name,
                "user_preferences": user_preferences,
                "profile": None,
                "fit_summary": None,
                "use_cache": use_cache,
                "error": None
            }
            
            # Execute workflow
            final_state = app.invoke(initial_state)
            
            # Prepare results
            results = {
                "success": final_state.get("error") is None,
                "profile": final_state.get("profile"),
                "fit_summary": final_state.get("fit_summary"),
                "error": final_state.get("error")
            }
            
            logger.info("Company profiling workflow completed")
            return results
            
        except Exception as e:
            logger.error(f"Company profiling workflow failed: {e}")
            return {
                "success": False,
                "profile": None,
                "fit_summary": None,
                "error": str(e)
            }
    
    # ==================== Error Recovery ====================
    
    def handle_workflow_error(self, workflow_name: str, error: Exception) -> Dict[str, Any]:
        """
        Handle workflow errors with recovery strategies
        
        Args:
            workflow_name: Name of the workflow that failed
            error: Exception that occurred
            
        Returns:
            Dictionary with error details and recovery suggestions
        """
        logger.error(f"Workflow '{workflow_name}' failed: {error}")
        
        # Determine recovery strategy based on error type
        recovery_strategy = "retry"
        
        if "timeout" in str(error).lower():
            recovery_strategy = "retry_with_backoff"
        elif "not found" in str(error).lower():
            recovery_strategy = "check_data"
        elif "connection" in str(error).lower():
            recovery_strategy = "check_network"
        
        return {
            "workflow": workflow_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "recovery_strategy": recovery_strategy,
            "timestamp": datetime.now().isoformat()
        }
