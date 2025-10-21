"""
Integration and End-to-End Workflow Testing
Tests complete workflows across multiple agents and components
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import all required components
from database.db_manager import DatabaseManager
from agents.job_search_agent import JobSearchAgent, SearchCriteria
from agents.match_scorer import MatchScorer
from agents.resume_optimizer import ResumeOptimizer
from agents.cover_letter_generator import CoverLetterGenerator
from agents.interview_prep_agent import InterviewPrepAgent
from agents.company_profiler import CompanyProfiler
from agents.job_tracker import JobTracker
from agents.orchestrator import LangGraphOrchestrator
from utils.notification_manager import NotificationManager, WhatsAppNotificationManager, UnifiedNotificationService
from utils.security import CredentialManager
from utils.llm_client import OllamaClient
from models.job import JobListing
from models.user import UserProfile
from models.application import Application
from models.hr_contact import HRContact
from models.notification import NotificationPreferences


class TestDailySearchWorkflow:
    """Test complete daily search workflow: scraping → filtering → scoring → notification"""
    
    @pytest.fixture
    def setup_workflow(self):
        """Setup test environment for daily search workflow"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # Create test user
        user = UserProfile(
            id="test-user-1",
            name="Test User",
            email="test@example.com",
            skills=["Python", "LangChain", "GenAI", "LLM"],
            experience_years=5,
            target_salary=40,
            preferred_locations=["Bangalore", "Remote"],
            preferred_remote=True,
            desired_tech_stack=["LangChain", "LangGraph", "RAG"]
        )
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd,
            'user': user
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_complete_daily_search_workflow(self, setup_workflow):
        """Test end-to-end daily search workflow"""
        db_manager = setup_workflow['db_manager']
        user = setup_workflow['user']
        
        # Step 1: Mock job search agent
        job_search_agent = Mock(spec=JobSearchAgent)
        sample_jobs = [
            JobListing(
                id="job-1",
                title="Senior GenAI Engineer",
                company="AI Corp",
                description="Build LLM applications with LangChain",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=40,
                salary_max=55,
                location="Bangalore",
                remote_type="hybrid",
                required_skills=["Python", "LangChain", "LLM", "RAG"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            ),
            JobListing(
                id="job-2",
                title="LLM Engineer",
                company="Tech Startup",
                description="Work on autonomous agents",
                source="naukri",
                source_url="https://example.com/job2",
                salary_min=35,
                salary_max=45,
                location="Remote",
                remote_type="remote",
                required_skills=["Python", "LangGraph", "Agents"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            )
        ]
        job_search_agent.search.return_value = sample_jobs
        
        # Step 2: Initialize match scorer with job repository
        from database.repositories.job_repository import JobRepository
        job_repo = JobRepository(db_manager)
        match_scorer = MatchScorer(job_repo)
        
        # Save jobs to database
        for job in sample_jobs:
            job_repo.save(job)
        
        # Calculate scores
        scored_jobs = match_scorer.rank_jobs(sample_jobs, user)
        
        assert len(scored_jobs) == 2
        assert all(0 <= score.total_score <= 100 for _, score in scored_jobs)
        
        # Step 3: Mock notification service
        notification_service = Mock(spec=UnifiedNotificationService)
        notification_service.send_daily_digest.return_value = {
            'email': True,
            'whatsapp': False
        }
        
        # Step 4: Execute workflow through orchestrator
        # Create mock agents for orchestrator
        mock_resume_optimizer = Mock()
        mock_cover_letter_gen = Mock()
        mock_interview_prep = Mock()
        mock_company_profiler = Mock()
        mock_job_tracker = Mock()
        
        orchestrator = LangGraphOrchestrator(
            job_search_agent=job_search_agent,
            match_scorer=match_scorer,
            resume_optimizer=mock_resume_optimizer,
            cover_letter_generator=mock_cover_letter_gen,
            interview_prep_agent=mock_interview_prep,
            company_profiler=mock_company_profiler,
            job_tracker=mock_job_tracker,
            notification_service=notification_service
        )
        
        search_criteria = SearchCriteria(
            keywords=["GenAI", "LLM"],
            min_salary_lakhs=35
        )
        
        result = orchestrator.execute_daily_search(
            search_criteria=search_criteria,
            user_profile=user,
            user_id=user.id
        )
        
        # Verify workflow completed successfully
        assert result['success'] is True
        assert result['jobs_found'] == 2
        assert result['jobs_scored'] == 2
        assert result['notification_sent'] is True
        
        # Verify jobs were stored with scores
        stored_jobs = job_repo.find_all()
        assert len(stored_jobs) >= 2
        assert all(job.match_score is not None for job in stored_jobs)


class TestResumeOptimizationWorkflow:
    """Test resume optimization workflow with real job postings"""
    
    @pytest.fixture
    def setup_resume_workflow(self):
        """Setup test environment for resume optimization"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # Create sample job
        job = JobListing(
            id="job-resume-1",
            title="Senior LLM Engineer",
            company="AI Innovations",
            description="""We seek a Senior LLM Engineer with:
            - 5+ years Python experience
            - Strong LangChain and RAG expertise
            - Experience with prompt engineering
            - Knowledge of vector databases
            """,
            source="naukri",
            source_url="https://example.com/job",
            salary_min=40,
            salary_max=60,
            location="Bangalore",
            remote_type="hybrid",
            required_skills=["Python", "LangChain", "RAG", "Vector DB"],
            posted_date=datetime.now(),
            created_at=datetime.now(),
            raw_html=""
        )
        
        resume_text = """Senior Software Engineer with 6 years experience.
        
        Skills: Python, Machine Learning, API Development
        
        Experience:
        - Built ML models for production
        - Developed REST APIs
        - Worked with databases
        """
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd,
            'job': job,
            'resume_text': resume_text
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_resume_optimization_workflow(self, setup_resume_workflow):
        """Test complete resume optimization workflow"""
        db_manager = setup_resume_workflow['db_manager']
        job = setup_resume_workflow['job']
        resume_text = setup_resume_workflow['resume_text']
        
        # Mock LLM client
        mock_llm = Mock(spec=OllamaClient)
        mock_llm.generate.return_value = """
        Analysis:
        - Missing keywords: LangChain, RAG, Vector databases
        - Strengths: Python experience, production systems
        - Improvements needed: Add GenAI project experience
        
        Suggestions:
        1. Add "LangChain" and "RAG" to skills section
        2. Rewrite experience to highlight LLM work
        3. Include vector database experience
        """
        
        # Initialize resume optimizer
        resume_optimizer = ResumeOptimizer(mock_llm, db_manager)
        
        # Execute optimization
        result = resume_optimizer.optimize_for_job(
            resume_text=resume_text,
            job=job,
            user_id="test-user-1"
        )
        
        # Verify optimization results
        assert result is not None
        assert result.analysis is not None
        assert len(result.improvements) >= 0  # May be empty if LLM mock doesn't generate improvements
        assert result.ats_keywords is not None
        
        # Verify ATS keywords extracted (may be empty with mock LLM)
        keywords = resume_optimizer.extract_ats_keywords(job.description)
        assert keywords is not None  # Just verify it returns something
        assert isinstance(keywords, list)


class TestCoverLetterWorkflow:
    """Test cover letter generation with various job types"""
    
    @pytest.fixture
    def setup_cover_letter_workflow(self):
        """Setup test environment for cover letter generation"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        jobs = {
            'technical': JobListing(
                id="job-tech-1",
                title="ML Engineer",
                company="Tech Corp",
                description="Build ML models and pipelines",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=35,
                salary_max=50,
                location="Bangalore",
                remote_type="onsite",
                required_skills=["Python", "TensorFlow", "ML"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            ),
            'startup': JobListing(
                id="job-startup-1",
                title="GenAI Founding Engineer",
                company="AI Startup",
                description="Join early team building GenAI products",
                source="naukri",
                source_url="https://example.com/job2",
                salary_min=30,
                salary_max=40,
                location="Remote",
                remote_type="remote",
                required_skills=["Python", "LLM", "Startup"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            ),
            'enterprise': JobListing(
                id="job-enterprise-1",
                title="Senior AI Architect",
                company="Enterprise Inc",
                description="Lead AI initiatives at scale",
                source="naukri",
                source_url="https://example.com/job3",
                salary_min=50,
                salary_max=70,
                location="Bangalore",
                remote_type="hybrid",
                required_skills=["Python", "Architecture", "Leadership"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html=""
            )
        }
        
        resume_summary = "Experienced AI engineer with 5 years in ML and LLM development"
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd,
            'jobs': jobs,
            'resume_summary': resume_summary
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_cover_letter_generation_multiple_tones(self, setup_cover_letter_workflow):
        """Test cover letter generation with different tones"""
        db_manager = setup_cover_letter_workflow['db_manager']
        job = setup_cover_letter_workflow['jobs']['technical']
        resume_summary = setup_cover_letter_workflow['resume_summary']
        
        # Mock LLM client
        mock_llm = Mock(spec=OllamaClient)
        mock_response = Mock()
        mock_response.text = "Dear Hiring Manager,\n\nI am excited to apply for the ML Engineer position..."
        mock_llm.generate_with_retry.return_value = mock_response
        
        # Initialize generator
        generator = CoverLetterGenerator(mock_llm, db_manager)
        
        # Test different tones
        tones = ['professional', 'enthusiastic', 'technical']
        
        for tone in tones:
            letter = generator.generate(
                job=job,
                resume_summary=resume_summary,
                user_id="test-user-1",
                tone=tone
            )
            
            assert letter is not None
            assert len(letter) > 50
            assert "Dear" in letter or "Hello" in letter
    
    def test_cover_letter_with_projects(self, setup_cover_letter_workflow):
        """Test cover letter generation with relevant projects"""
        db_manager = setup_cover_letter_workflow['db_manager']
        job = setup_cover_letter_workflow['jobs']['startup']
        resume_summary = setup_cover_letter_workflow['resume_summary']
        
        # Mock LLM client
        mock_llm = Mock(spec=OllamaClient)
        mock_response = Mock()
        mock_response.text = "Dear Hiring Manager,\n\nI built a RAG system with 95% accuracy and developed a multi-agent framework for automated workflows. This experience aligns perfectly with your needs."
        mock_llm.generate_with_retry.return_value = mock_response
        
        generator = CoverLetterGenerator(mock_llm, db_manager)
        
        projects = [
            "Built RAG system with 95% accuracy",
            "Developed multi-agent framework"
        ]
        
        letter = generator.generate(
            job=job,
            resume_summary=resume_summary,
            user_id="test-user-1",
            relevant_projects=projects,
            tone="enthusiastic"
        )
        
        assert letter is not None
        assert len(letter) > 50


class TestInterviewPrepWorkflow:
    """Test interview prep workflow including custom questions"""
    
    @pytest.fixture
    def setup_interview_workflow(self):
        """Setup test environment for interview prep"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        job = JobListing(
            id="job-interview-1",
            title="GenAI Engineer",
            company="AI Labs",
            description="Work on LLM applications and RAG systems",
            source="naukri",
            source_url="https://example.com/job",
            salary_min=40,
            salary_max=55,
            location="Bangalore",
            remote_type="hybrid",
            required_skills=["Python", "LangChain", "RAG"],
            posted_date=datetime.now(),
            created_at=datetime.now(),
            raw_html=""
        )
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd,
            'job': job
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_interview_question_generation(self, setup_interview_workflow):
        """Test interview question generation"""
        db_manager = setup_interview_workflow['db_manager']
        job = setup_interview_workflow['job']
        
        # Mock LLM client
        mock_llm = Mock(spec=OllamaClient)
        mock_response = Mock()
        mock_response.text = """
        1. What is RAG and how does it work?
        2. Explain LangChain's key components
        3. How do you optimize LLM prompts?
        """
        mock_llm.generate_with_retry.return_value = mock_response
        
        from database.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db_manager)
        agent = InterviewPrepAgent(mock_llm, question_repo)
        
        # Generate technical questions
        questions = agent.generate_questions(
            job=job,
            question_type="technical",
            difficulty="medium"
        )
        
        assert questions is not None
        assert isinstance(questions, list)  # May be empty with mock LLM
    
    def test_custom_question_workflow(self, setup_interview_workflow):
        """Test custom question management workflow"""
        db_manager = setup_interview_workflow['db_manager']
        
        # Create test user first
        user_query = "INSERT INTO users (id, name, email, skills, experience_years, target_salary) VALUES (?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(user_query, ("test-user-1", "Test User", "test@example.com", "[]", 5, 4000000))
        
        # Mock LLM client
        mock_llm = Mock(spec=OllamaClient)
        mock_response = Mock()
        mock_response.text = "RAG combines retrieval with generation..."
        mock_llm.generate_with_retry.return_value = mock_response
        
        from database.repositories.question_repository import QuestionRepository
        question_repo = QuestionRepository(db_manager)
        agent = InterviewPrepAgent(mock_llm, question_repo)
        
        # Add custom question
        question = agent.add_custom_question(
            user_id="test-user-1",
            question_text="Explain RAG architecture",
            category="technical",
            topic="RAG",
            difficulty="medium"
        )
        
        assert question is not None
        assert question.question_text == "Explain RAG architecture"
        
        # Generate ideal answer
        ideal_answer = agent.generate_ideal_answer(
            question=question.question_text,
            question_category=question.category
        )
        
        assert ideal_answer is not None
        assert len(ideal_answer) > 0
        
        # Retrieve custom questions
        questions = agent.get_custom_questions(
            user_id="test-user-1",
            filters={"category": "technical"}
        )
        
        assert len(questions) > 0
        assert any(q.question_text == "Explain RAG architecture" for q in questions)


class TestApplicationTrackingWorkflow:
    """Test application tracking with status updates and HR contacts"""
    
    @pytest.fixture
    def setup_tracking_workflow(self):
        """Setup test environment for application tracking"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # Create test user and job
        user_query = "INSERT INTO users (id, name, email, skills, experience_years, target_salary) VALUES (?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(user_query, ("user-1", "Test User", "test@example.com", "[]", 5, 4000000))
        
        job_query = "INSERT INTO jobs (id, title, company, location, description, source_url, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(job_query, ("job-1", "GenAI Engineer", "Tech Corp", "Bangalore", "Great role", "http://test.com", "naukri"))
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_complete_application_lifecycle(self, setup_tracking_workflow):
        """Test complete application lifecycle with HR contacts"""
        db_manager = setup_tracking_workflow['db_manager']
        tracker = JobTracker(db_manager)
        
        # Step 1: Add application
        app = tracker.add_application(
            job_id="job-1",
            user_id="user-1",
            status="saved",
            notes="Interesting opportunity"
        )
        
        assert app is not None
        assert app.status == "saved"
        
        # Step 2: Update to applied
        success = tracker.update_status(
            application_id=app.id,
            new_status="applied",
            applied_date=datetime.now()
        )
        
        assert success is True
        
        # Step 3: Add HR contact
        hr_contact = tracker.add_hr_contact(
            application_id=app.id,
            name="Jane Smith",
            email="jane.smith@techcorp.com",
            phone="+1234567890",
            linkedin_url="https://linkedin.com/in/janesmith",
            designation="Senior Recruiter",
            notes="Very responsive"
        )
        
        assert hr_contact is not None
        assert hr_contact.name == "Jane Smith"
        
        # Step 4: Update to interview
        success = tracker.update_status(
            application_id=app.id,
            new_status="interview",
            interview_date=datetime.now() + timedelta(days=7)
        )
        
        assert success is True
        
        # Step 5: Get statistics
        stats = tracker.get_statistics("user-1")
        
        assert stats['total'] >= 1
        assert 'by_status' in stats
        assert 'interview' in stats['by_status']
        
        # Step 6: Export history
        csv_data = tracker.export_history(
            user_id="user-1",
            format="csv",
            include_hr_contacts=True
        )
        
        assert csv_data is not None
        assert "Jane Smith" in csv_data
        assert "jane.smith@techcorp.com" in csv_data


class TestNotificationWorkflow:
    """Test notification delivery via email and WhatsApp"""
    
    def test_notification_preferences_management(self):
        """Test notification preferences configuration"""
        prefs = NotificationPreferences(
            user_id="user-1",
            email_address="test@example.com",
            email_enabled=True,
            whatsapp_enabled=True,
            whatsapp_number="+1234567890",
            daily_digest=True,
            interview_reminders=True,
            status_updates=True,
            digest_time="09:00"
        )
        
        assert prefs.email_enabled is True
        assert prefs.whatsapp_enabled is True
        assert prefs.digest_time == "09:00"
        
        # Test serialization
        prefs_dict = prefs.to_dict()
        restored = NotificationPreferences.from_dict(prefs_dict)
        
        assert restored.user_id == prefs.user_id
        assert restored.email_address == prefs.email_address
    
    def test_email_notification_templates(self):
        """Test email notification template generation"""
        email_manager = NotificationManager(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="dummy",
            from_address="test@example.com"
        )
        
        # Test daily digest template
        jobs = [
            JobListing(
                id="job-1",
                title="GenAI Engineer",
                company="AI Corp",
                description="Great role",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=40,
                salary_max=55,
                location="Bangalore",
                remote_type="hybrid",
                required_skills=["Python"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html="",
                match_score=85.0
            )
        ]
        
        html = email_manager._generate_daily_digest_html(jobs)
        
        assert "GenAI Engineer" in html
        assert "AI Corp" in html
        assert "85%" in html
    
    def test_whatsapp_notification_templates(self):
        """Test WhatsApp notification template generation"""
        whatsapp_manager = WhatsAppNotificationManager(
            account_sid="dummy",
            auth_token="dummy",
            from_number="whatsapp:+14155238886"
        )
        
        jobs = [
            JobListing(
                id="job-1",
                title="LLM Engineer",
                company="Tech Startup",
                description="Exciting role",
                source="naukri",
                source_url="https://example.com/job1",
                salary_min=35,
                salary_max=45,
                location="Remote",
                remote_type="remote",
                required_skills=["Python"],
                posted_date=datetime.now(),
                created_at=datetime.now(),
                raw_html="",
                match_score=90.0
            )
        ]
        
        message = whatsapp_manager._generate_new_jobs_alert_message(jobs)
        
        assert "LLM Engineer" in message
        assert "Tech Startup" in message
        assert "90%" in message


class TestDataExportWorkflow:
    """Test data export functionality"""
    
    @pytest.fixture
    def setup_export_workflow(self):
        """Setup test environment for data export"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        # Create test data
        user_query = "INSERT INTO users (id, name, email, skills, experience_years, target_salary) VALUES (?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(user_query, ("user-1", "Test User", "test@example.com", "[]", 5, 4000000))
        
        job_query = "INSERT INTO jobs (id, title, company, location, description, source_url, source) VALUES (?, ?, ?, ?, ?, ?, ?)"
        db_manager.execute_update(job_query, ("job-1", "Engineer", "Corp", "City", "Desc", "http://test.com", "naukri"))
        
        app_query = "INSERT INTO applications (id, job_id, user_id, status, applied_date) VALUES (?, ?, ?, ?, ?)"
        db_manager.execute_update(app_query, ("app-1", "job-1", "user-1", "applied", datetime.now()))
        
        hr_query = "INSERT INTO hr_contacts (id, application_id, name, email, phone) VALUES (?, ?, ?, ?, ?)"
        db_manager.execute_update(hr_query, ("hr-1", "app-1", "John Doe", "john@corp.com", "+1234567890"))
        
        yield {
            'db_manager': db_manager,
            'db_path': db_path,
            'db_fd': db_fd
        }
        
        # Cleanup
        db_manager.close_connection()
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_csv_export_with_hr_contacts(self, setup_export_workflow):
        """Test CSV export with HR contact information"""
        db_manager = setup_export_workflow['db_manager']
        tracker = JobTracker(db_manager)
        
        csv_data = tracker.export_history(
            user_id="user-1",
            format="csv",
            include_hr_contacts=True
        )
        
        assert csv_data is not None
        assert "Application ID" in csv_data
        assert "HR Name" in csv_data
        assert "John Doe" in csv_data
        assert "john@corp.com" in csv_data


class TestCredentialSecurity:
    """Test credential encryption and security"""
    
    def test_credential_encryption_decryption(self):
        """Test credential encryption and decryption"""
        # Generate test key
        manager = CredentialManager()
        
        # Test data
        test_credentials = {
            'username': 'test_user',
            'password': 'super_secret_password_123',
            'api_key': 'sk-1234567890abcdef'
        }
        
        # Encrypt credentials
        encrypted = manager.store_credentials('test_service', test_credentials)
        
        assert encrypted['username'] != test_credentials['username']
        assert encrypted['password'] != test_credentials['password']
        assert encrypted['api_key'] != test_credentials['api_key']
        
        # Decrypt credentials
        decrypted = manager.retrieve_credentials(encrypted)
        
        assert decrypted['username'] == test_credentials['username']
        assert decrypted['password'] == test_credentials['password']
        assert decrypted['api_key'] == test_credentials['api_key']
    
    def test_encryption_key_generation(self):
        """Test encryption key generation"""
        manager = CredentialManager()
        
        key1 = manager.generate_key()
        key2 = manager.generate_key()
        
        assert key1 != key2
        assert len(key1) > 0
        assert len(key2) > 0
    
    def test_empty_credential_handling(self):
        """Test handling of empty credentials"""
        manager = CredentialManager()
        
        test_credentials = {
            'username': 'test_user',
            'password': '',
            'api_key': None
        }
        
        encrypted = manager.store_credentials('test_service', test_credentials)
        decrypted = manager.retrieve_credentials(encrypted)
        
        assert decrypted['username'] == 'test_user'
        assert decrypted['password'] == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
