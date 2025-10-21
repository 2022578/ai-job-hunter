"""
Resume Optimizer Agent
Analyzes resumes and provides optimization suggestions for GenAI/LLM roles
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import re
import uuid
from utils.llm_client import OllamaClient, LLMResponse
from utils.prompts import resume_analysis_prompt
from models.job import JobListing
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ResumeAnalysis:
    """Results from resume analysis"""
    overall_score: float  # 0-10
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    present_keywords: List[str] = field(default_factory=list)
    keyword_density_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    analysis_text: str = ""
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResumeImprovement:
    """Before/after comparison for resume section"""
    section_name: str
    before: str
    after: str
    reason: str


@dataclass
class OptimizedResume:
    """Complete optimization results for a job"""
    job_id: str
    analysis: ResumeAnalysis
    improvements: List[ResumeImprovement] = field(default_factory=list)
    ats_keywords: List[str] = field(default_factory=list)
    genai_highlights: List[str] = field(default_factory=list)
    optimized_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResumeVersion:
    """Stored resume version"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    resume_text: str = ""
    version_number: int = 1
    job_id: Optional[str] = None
    optimization_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class ResumeOptimizer:
    """Agent for resume analysis and optimization"""
    
    def __init__(
        self,
        llm_client: OllamaClient,
        db_manager: DatabaseManager
    ):
        """
        Initialize Resume Optimizer
        
        Args:
            llm_client: LLM client for text generation
            db_manager: Database manager for storing resume versions
        """
        self.llm_client = llm_client
        self.db_manager = db_manager
        self._ensure_resume_versions_table()
    
    def _ensure_resume_versions_table(self):
        """Create resume_versions table if it doesn't exist"""
        try:
            conn = self.db_manager.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resume_versions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    resume_text TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    job_id TEXT,
                    optimization_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resume_versions_user_id 
                ON resume_versions(user_id)
            """)
            conn.commit()
            logger.info("Resume versions table ensured")
        except Exception as e:
            logger.error(f"Failed to create resume_versions table: {e}")
    
    def analyze_resume(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> ResumeAnalysis:
        """
        Analyze resume and identify strengths and weaknesses
        
        Args:
            resume_text: The resume content to analyze
            job_description: Optional job description for targeted analysis
            
        Returns:
            ResumeAnalysis with detailed feedback
        """
        try:
            logger.info("Starting resume analysis")
            
            # Generate prompt
            prompts = resume_analysis_prompt(resume_text, job_description)
            
            # Get LLM analysis
            response = self.llm_client.generate_with_retry(
                prompt=prompts['user'],
                system_prompt=prompts['system'],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response
            analysis = self._parse_analysis_response(response)
            analysis.analysis_text = response.text
            
            logger.info(f"Resume analysis completed with score: {analysis.overall_score}/10")
            return analysis
            
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            # Return empty analysis on failure
            return ResumeAnalysis(
                overall_score=0.0,
                analysis_text=f"Analysis failed: {str(e)}"
            )
    
    def _parse_analysis_response(self, response: LLMResponse) -> ResumeAnalysis:
        """
        Parse LLM response into ResumeAnalysis structure
        
        Args:
            response: LLM response to parse
            
        Returns:
            Parsed ResumeAnalysis
        """
        text = response.text
        analysis = ResumeAnalysis(overall_score=5.0)
        
        # Extract missing keywords
        missing_match = re.search(
            r'Missing critical keywords?:?\s*\n?(.*?)(?=\n\n|\n-|\nPresent|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if missing_match:
            keywords_text = missing_match.group(1)
            analysis.missing_keywords = self._extract_list_items(keywords_text)
        
        # Extract present keywords
        present_match = re.search(
            r'Present keywords?:?\s*\n?(.*?)(?=\n\n|\n-|\nKeyword density|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if present_match:
            keywords_text = present_match.group(1)
            analysis.present_keywords = self._extract_list_items(keywords_text)
        
        # Extract keyword density score
        density_match = re.search(
            r'Keyword density score:?\s*(\d+(?:\.\d+)?)\s*/\s*10',
            text,
            re.IGNORECASE
        )
        if density_match:
            analysis.keyword_density_score = float(density_match.group(1))
        
        # Extract strengths
        strengths_match = re.search(
            r'\*\*STRENGTHS:?\*\*\s*\n(.*?)(?=\n\*\*[A-Z]|\n\n\*\*|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if strengths_match:
            analysis.strengths = self._extract_list_items(strengths_match.group(1))
        
        # Extract weaknesses/areas for improvement
        weakness_match = re.search(
            r'\*\*AREAS FOR IMPROVEMENT:?\*\*\s*\n(.*?)(?=\n\*\*[A-Z]|\n\n\*\*|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if weakness_match:
            analysis.weaknesses = self._extract_list_items(weakness_match.group(1))
        
        # Extract recommendations
        rec_match = re.search(
            r'\*\*RECOMMENDED IMPROVEMENTS?:?\*\*\s*\n(.*?)(?=\n\*\*[A-Z]|\n\n\*\*|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if rec_match:
            analysis.recommendations = self._extract_list_items(rec_match.group(1))
        
        # Extract overall score if present
        score_match = re.search(
            r'(?:Current strength|Overall assessment):?\s*(\d+(?:\.\d+)?)\s*/\s*10',
            text,
            re.IGNORECASE
        )
        if score_match:
            analysis.overall_score = float(score_match.group(1))
        
        return analysis
    
    def _extract_list_items(self, text: str) -> List[str]:
        """
        Extract list items from text
        
        Args:
            text: Text containing list items
            
        Returns:
            List of extracted items
        """
        items = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove list markers
            line = re.sub(r'^\d+\.\s*', '', line)  # Numbered lists
            line = re.sub(r'^[-•*]\s*', '', line)  # Bullet points
            line = re.sub(r'^\[.*?\]\s*', '', line)  # Bracketed items
            
            if line:
                items.append(line)
        
        return items
    
    def optimize_for_job(
        self,
        resume_text: str,
        job: JobListing,
        user_id: Optional[str] = None
    ) -> OptimizedResume:
        """
        Generate targeted optimization suggestions for specific job
        
        Args:
            resume_text: Current resume content
            job: Job listing to optimize for
            user_id: Optional user ID for storing version
            
        Returns:
            OptimizedResume with complete optimization results
        """
        try:
            logger.info(f"Optimizing resume for job: {job.title} at {job.company}")
            
            # Analyze resume with job context
            analysis = self.analyze_resume(resume_text, job.description)
            
            # Extract ATS keywords from job description
            ats_keywords = self.extract_ats_keywords(job.description)
            
            # Generate improvements
            improvements = self._generate_improvements(
                resume_text,
                job.description,
                analysis
            )
            
            # Generate GenAI-specific highlights
            genai_highlights = self._generate_genai_highlights(
                resume_text,
                job.description
            )
            
            optimized = OptimizedResume(
                job_id=job.id,
                analysis=analysis,
                improvements=improvements,
                ats_keywords=ats_keywords,
                genai_highlights=genai_highlights
            )
            
            # Store resume version if user_id provided
            if user_id:
                self._store_resume_version(
                    user_id=user_id,
                    resume_text=resume_text,
                    job_id=job.id,
                    notes=f"Optimized for {job.title} at {job.company}"
                )
            
            logger.info("Resume optimization completed")
            return optimized
            
        except Exception as e:
            logger.error(f"Resume optimization failed: {e}")
            # Return minimal result on failure
            return OptimizedResume(
                job_id=job.id,
                analysis=ResumeAnalysis(overall_score=0.0)
            )
    
    def extract_ats_keywords(self, job_description: str) -> List[str]:
        """
        Extract ATS keywords from job description
        
        Args:
            job_description: Job description text
            
        Returns:
            List of important keywords for ATS
        """
        try:
            logger.info("Extracting ATS keywords from job description")
            
            prompt = f"""Extract the most important ATS (Applicant Tracking System) keywords from this job description.
Focus on:
- Technical skills and technologies
- Required qualifications
- Key responsibilities
- Industry-specific terms
- GenAI/LLM specific terms

Job Description:
{job_description}

List only the keywords, one per line, without explanations or categories.
Focus on the 15-20 most critical keywords."""

            response = self.llm_client.generate_with_retry(
                prompt=prompt,
                system_prompt="You are an ATS keyword extraction expert.",
                temperature=0.3,
                max_tokens=500
            )
            
            keywords = self.llm_client.parse_list_response(response)
            logger.info(f"Extracted {len(keywords)} ATS keywords")
            return keywords
            
        except Exception as e:
            logger.error(f"ATS keyword extraction failed: {e}")
            return []
    
    def _generate_improvements(
        self,
        resume_text: str,
        job_description: str,
        analysis: ResumeAnalysis
    ) -> List[ResumeImprovement]:
        """
        Generate before/after improvements for resume sections
        
        Args:
            resume_text: Current resume
            job_description: Target job description
            analysis: Resume analysis results
            
        Returns:
            List of ResumeImprovement suggestions
        """
        try:
            logger.info("Generating resume improvements")
            
            prompt = f"""Based on this resume analysis, provide 3-5 specific before/after rewrites for resume sections.

Job Description:
{job_description}

Current Resume:
{resume_text}

Analysis Findings:
- Missing Keywords: {', '.join(analysis.missing_keywords[:10])}
- Weaknesses: {', '.join(analysis.weaknesses[:5])}

For each improvement, provide:
SECTION: [name of section, e.g., "Professional Summary", "Work Experience - Project X"]
BEFORE: [original text from resume]
AFTER: [improved version]
REASON: [why this is better]

Separate each improvement with "---"

Focus on:
1. Adding missing ATS keywords naturally
2. Quantifying achievements
3. Highlighting GenAI/LLM experience
4. Improving clarity and impact"""

            response = self.llm_client.generate_with_retry(
                prompt=prompt,
                system_prompt="You are an expert resume writer specializing in GenAI roles.",
                temperature=0.7,
                max_tokens=2000
            )
            
            improvements = self._parse_improvements(response.text)
            logger.info(f"Generated {len(improvements)} improvements")
            return improvements
            
        except Exception as e:
            logger.error(f"Improvement generation failed: {e}")
            return []
    
    def _parse_improvements(self, text: str) -> List[ResumeImprovement]:
        """
        Parse improvements from LLM response
        
        Args:
            text: LLM response text
            
        Returns:
            List of parsed ResumeImprovement objects
        """
        improvements = []
        
        # Split by separator
        sections = re.split(r'\n---+\n', text)
        
        for section in sections:
            if not section.strip():
                continue
            
            # Extract components
            section_match = re.search(
                r'SECTION:?\s*(.*?)(?=\n|$)',
                section,
                re.IGNORECASE
            )
            before_match = re.search(
                r'BEFORE:?\s*(.*?)(?=\nAFTER:|\n\n)',
                section,
                re.IGNORECASE | re.DOTALL
            )
            after_match = re.search(
                r'AFTER:?\s*(.*?)(?=\nREASON:|\n\n)',
                section,
                re.IGNORECASE | re.DOTALL
            )
            reason_match = re.search(
                r'REASON:?\s*(.*?)(?=\n\n|$)',
                section,
                re.IGNORECASE | re.DOTALL
            )
            
            if section_match and before_match and after_match and reason_match:
                improvements.append(ResumeImprovement(
                    section_name=section_match.group(1).strip(),
                    before=before_match.group(1).strip(),
                    after=after_match.group(1).strip(),
                    reason=reason_match.group(1).strip()
                ))
        
        return improvements
    
    def _generate_genai_highlights(
        self,
        resume_text: str,
        job_description: str
    ) -> List[str]:
        """
        Generate suggestions for highlighting GenAI experience
        
        Args:
            resume_text: Current resume
            job_description: Target job description
            
        Returns:
            List of GenAI highlight suggestions
        """
        try:
            logger.info("Generating GenAI experience highlights")
            
            prompt = f"""Suggest 3-5 ways to better emphasize GenAI and LLM experience in this resume for the target job.

Job Description:
{job_description}

Current Resume:
{resume_text}

Provide specific suggestions for highlighting:
- LLM and prompt engineering experience
- LangChain/LangGraph or similar frameworks
- Autonomous agents development
- RAG systems implementation
- Fine-tuning and model optimization

List each suggestion on a new line, starting with a dash (-)."""

            response = self.llm_client.generate_with_retry(
                prompt=prompt,
                system_prompt="You are an expert in GenAI career development.",
                temperature=0.7,
                max_tokens=800
            )
            
            highlights = self.llm_client.parse_list_response(response)
            logger.info(f"Generated {len(highlights)} GenAI highlights")
            return highlights
            
        except Exception as e:
            logger.error(f"GenAI highlights generation failed: {e}")
            return []
    
    def suggest_improvements(
        self,
        resume_text: str,
        target_keywords: List[str]
    ) -> List[ResumeImprovement]:
        """
        Suggest improvements with before/after comparisons
        
        Args:
            resume_text: Current resume content
            target_keywords: Keywords to incorporate
            
        Returns:
            List of improvement suggestions
        """
        try:
            logger.info("Generating improvement suggestions")
            
            prompt = f"""Suggest specific improvements to incorporate these keywords into the resume naturally.

Target Keywords: {', '.join(target_keywords)}

Current Resume:
{resume_text}

Provide 3-5 specific rewrites showing:
SECTION: [section name]
BEFORE: [original text]
AFTER: [improved version with keywords]
REASON: [explanation]

Separate each with "---"

Make improvements natural and impactful, not just keyword stuffing."""

            response = self.llm_client.generate_with_retry(
                prompt=prompt,
                system_prompt="You are an expert resume optimizer.",
                temperature=0.7,
                max_tokens=1500
            )
            
            improvements = self._parse_improvements(response.text)
            logger.info(f"Generated {len(improvements)} improvement suggestions")
            return improvements
            
        except Exception as e:
            logger.error(f"Improvement suggestion failed: {e}")
            return []
    
    def _store_resume_version(
        self,
        user_id: str,
        resume_text: str,
        job_id: Optional[str] = None,
        notes: str = ""
    ) -> bool:
        """
        Store resume version in database
        
        Args:
            user_id: User ID
            resume_text: Resume content
            job_id: Optional job ID this version is for
            notes: Optional notes about this version
            
        Returns:
            True if stored successfully
        """
        try:
            # Get next version number
            query = """
                SELECT COALESCE(MAX(version_number), 0) + 1 as next_version
                FROM resume_versions
                WHERE user_id = ?
            """
            results = self.db_manager.execute_query(query, (user_id,))
            version_number = results[0]['next_version'] if results else 1
            
            # Insert new version
            version = ResumeVersion(
                user_id=user_id,
                resume_text=resume_text,
                version_number=version_number,
                job_id=job_id,
                optimization_notes=notes
            )
            
            insert_query = """
                INSERT INTO resume_versions (
                    id, user_id, resume_text, version_number,
                    job_id, optimization_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                version.id,
                version.user_id,
                version.resume_text,
                version.version_number,
                version.job_id,
                version.optimization_notes,
                version.created_at.isoformat()
            )
            
            rows = self.db_manager.execute_update(insert_query, params)
            
            if rows > 0:
                logger.info(f"Stored resume version {version_number} for user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to store resume version: {e}")
            return False
    
    def get_resume_versions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ResumeVersion]:
        """
        Get stored resume versions for user
        
        Args:
            user_id: User ID
            limit: Maximum number of versions to return
            
        Returns:
            List of ResumeVersion objects
        """
        try:
            query = """
                SELECT * FROM resume_versions
                WHERE user_id = ?
                ORDER BY version_number DESC
                LIMIT ?
            """
            
            results = self.db_manager.execute_query(query, (user_id, limit))
            
            versions = []
            for row in results:
                version = ResumeVersion(
                    id=row['id'],
                    user_id=row['user_id'],
                    resume_text=row['resume_text'],
                    version_number=row['version_number'],
                    job_id=row['job_id'],
                    optimization_notes=row['optimization_notes'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                versions.append(version)
            
            logger.info(f"Retrieved {len(versions)} resume versions for user {user_id}")
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get resume versions: {e}")
            return []
    
    def get_resume_version_by_id(self, version_id: str) -> Optional[ResumeVersion]:
        """
        Get specific resume version by ID
        
        Args:
            version_id: Version ID
            
        Returns:
            ResumeVersion if found, None otherwise
        """
        try:
            query = "SELECT * FROM resume_versions WHERE id = ?"
            results = self.db_manager.execute_query(query, (version_id,))
            
            if results:
                row = results[0]
                return ResumeVersion(
                    id=row['id'],
                    user_id=row['user_id'],
                    resume_text=row['resume_text'],
                    version_number=row['version_number'],
                    job_id=row['job_id'],
                    optimization_notes=row['optimization_notes'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get resume version: {e}")
            return None
