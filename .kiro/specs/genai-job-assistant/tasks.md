# Implementation Plan

- [x] 1. Set up project structure and core dependencies





  - Create directory structure: `agents/`, `models/`, `database/`, `scrapers/`, `ui/`, `utils/`, `config/`, `tests/`
  - Create `requirements.txt` with dependencies: streamlit, langgraph, langchain, ollama, selenium, beautifulsoup4, apscheduler, cryptography, twilio, pandas
  - Create `config.yaml` template with placeholders for LLM model, SMTP settings, Twilio credentials, user contact details
  - Create `.env.example` file for environment variables
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 2. Implement database layer and data models






  - [x] 2.1 Create SQLite database schema and initialization script

    - Write `database/schema.sql` with all table definitions (users, jobs, applications, hr_contacts, custom_questions, company_profiles, credentials, notification_preferences)
    - Create `database/db_manager.py` with connection management, initialization, and backup functions
    - Implement database migration support for future schema changes
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  

  - [x] 2.2 Implement data model classes with validation

    - Create `models/job.py` with JobListing dataclass and validation methods
    - Create `models/user.py` with UserProfile dataclass
    - Create `models/application.py` with Application dataclass
    - Create `models/hr_contact.py` with HRContact dataclass
    - Create `models/question.py` with CustomQuestion dataclass
    - Create `models/company.py` with CompanyProfile dataclass
    - Create `models/notification.py` with NotificationPreferences dataclass
    - Add JSON serialization/deserialization methods to all models
    - _Requirements: 1.5, 8.1, 8.4, 4.6, 9.1, 13.9_
  

  - [x] 2.3 Create database repository layer for CRUD operations

    - Implement `database/repositories/job_repository.py` with methods: save, find_by_id, find_all, find_by_criteria, update_match_score
    - Implement `database/repositories/application_repository.py` with methods: save, update_status, find_by_user, get_statistics
    - Implement `database/repositories/hr_contact_repository.py` with methods: save, update, find_by_application, search
    - Implement `database/repositories/question_repository.py` with methods: save, update, find_by_category, find_by_topic
    - Implement `database/repositories/company_repository.py` with methods: save, find_by_name, get_cached
    - Implement `database/repositories/user_repository.py` with methods: save, update, find_by_id
    - _Requirements: 1.5, 8.1, 8.5, 4.6, 9.5, 12.1_

- [x] 3. Implement credential encryption and security utilities




  - Create `utils/security.py` with CredentialManager class using Fernet encryption
  - Implement methods: encrypt, decrypt, generate_key, store_credentials, retrieve_credentials
  - Create `database/repositories/credential_repository.py` for secure credential storage
  - Add environment variable support for encryption key
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4. Implement Naukri scraper with anti-detection measures






  - [x] 4.1 Create base scraper infrastructure

    - Implement `scrapers/base_scraper.py` with common scraping utilities (rate limiting, retry logic, user agent rotation)
    - Create `scrapers/naukri_scraper.py` with NaukriScraper class
    - Implement Selenium WebDriver setup with headless Chrome configuration
    - Add CAPTCHA detection and handling logic
    - _Requirements: 1.1, 1.5_
  

  - [x] 4.2 Implement Naukri login and search functionality

    - Implement login method with encrypted credential handling
    - Create search method with keyword and filter parameters
    - Implement job listing extraction from search results
    - Add pagination handling for multiple pages of results
    - _Requirements: 1.1, 1.2, 1.3, 7.3_
  
  - [x] 4.3 Implement job detail extraction and parsing


    - Create method to extract detailed job information from individual job pages
    - Parse salary, location, remote type, required skills, description
    - Store raw HTML for future re-parsing
    - Implement deduplication logic against existing database entries
    - _Requirements: 1.5, 1.1_

- [x] 5. Implement Job Search Agent with filtering logic





  - Create `agents/job_search_agent.py` with JobSearchAgent class
  - Implement search method that orchestrates scraper and applies filters
  - Create filter_by_keywords method to match GenAI-related terms
  - Create filter_by_salary method to enforce minimum salary threshold
  - Implement deduplicate method to avoid storing duplicate jobs
  - Integrate with job repository to persist discovered jobs
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
-

- [x] 6. Implement Match Scorer for job relevance calculation




  - Create `agents/match_scorer.py` with MatchScorer class
  - Implement calculate_score method with weighted scoring algorithm
  - Create component scoring methods: calculate_skills_match, calculate_salary_match, calculate_tech_stack_match, calculate_remote_flexibility, calculate_company_profile_score
  - Implement get_score_breakdown method to explain score components
  - Create rank_jobs method to sort jobs by match score
  - Update job records with calculated match scores
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
-

- [x] 7. Implement LLM integration layer




  - [x] 7.1 Create LLM client wrapper for Ollama


    - Implement `utils/llm_client.py` with OllamaClient class
    - Add methods: generate, generate_with_retry, stream_generate
    - Implement timeout handling and error recovery
    - Add output parsing utilities for structured responses
    - _Requirements: 2.1, 3.1, 4.1, 9.2_
  
  - [x] 7.2 Create prompt templates for different agents


    - Create `utils/prompts.py` with template functions
    - Implement resume_analysis_prompt, cover_letter_prompt, interview_question_prompt, ideal_answer_prompt, company_summary_prompt
    - Add few-shot examples for better LLM performance
    - _Requirements: 2.1, 3.2, 4.1, 4.7, 9.3_
-

- [x] 8. Implement Resume Optimizer agent









  - Create `agents/resume_optimizer.py` with ResumeOptimizer class
  - Implement analyze_resume method using LLM to identify strengths and weaknesses
  - Create optimize_for_job method that generates targeted suggestions
  - Implement extract_ats_keywords method to parse job descriptions
  - Create suggest_improvements method with before/after comparisons
  - Store resume versions in database for tracking
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 9. Implement Cover Letter Generator agent





  - Create `agents/cover_letter_generator.py` with CoverLetterGenerator class
  - Implement generate method that creates personalized cover letters using LLM
  - Add support for different tones (professional, enthusiastic, technical)
  - Create regenerate_with_tone method for style variations
  - Implement save_letter method to persist generated letters
  - Cache generated letters for 7 days to avoid redundant generation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 10. Implement Interview Prep Agent with custom Q&A management





  - [x] 10.1 Create interview question generation functionality


    - Implement `agents/interview_prep_agent.py` with InterviewPrepAgent class
    - Create generate_questions method that produces technical and behavioral questions using LLM
    - Implement question categorization (technical, behavioral, system design)
    - Add difficulty level assignment (easy, medium, hard)
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [x] 10.2 Implement mock interview and answer evaluation

    - Create conduct_mock_interview method for interactive Q&A sessions
    - Implement evaluate_answer method that provides feedback using LLM
    - Add follow-up question generation based on user responses
    - _Requirements: 4.3, 4.4_
  
  - [x] 10.3 Implement custom question management

    - Create add_custom_question method to store user-provided questions
    - Implement generate_ideal_answer method using LLM to create model answers
    - Create get_custom_questions method with filtering by category, topic, difficulty
    - Implement update_custom_question method for editing stored questions
    - Add methods to link custom questions to specific job applications
    - _Requirements: 4.6, 4.7, 4.8, 4.9, 4.10_

- [x] 11. Implement Company Profiler agent





  - Create `agents/company_profiler.py` with CompanyProfiler class
  - Implement profile_company method that aggregates data from multiple sources
  - Create scraper for Glassdoor ratings and reviews (with rate limiting)
  - Integrate with Google News API for recent company news
  - Implement assess_genai_focus method to evaluate AI investment
  - Create summarize_fit method using LLM to generate company-candidate fit analysis
  - Implement 30-day caching mechanism for company profiles
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 12. Implement Job Tracker with HR contact management





  - Create `agents/job_tracker.py` with JobTracker class
  - Implement add_application method to record new applications
  - Create update_status method with status transition validation
  - Implement mark_as_saved and mark_as_not_interested methods
  - Create add_hr_contact method to store HR information
  - Implement update_hr_contact method for editing contact details
  - Create get_hr_contacts method with search and filter capabilities
  - Implement get_statistics method to calculate application metrics
  - Create export_history method to generate CSV/Excel files with HR contacts
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 13. Implement Notification Manager for email and WhatsApp




  - [x] 13.1 Create email notification functionality


    - Implement `utils/notification_manager.py` with NotificationManager class
    - Create send_email method using SMTP (smtplib)
    - Implement email templates for: daily digest, interview reminder, status update
    - Add HTML email formatting for better presentation
    - Configure SMTP settings for Gmail and Outlook
    - _Requirements: 13.1, 13.3, 13.5, 13.7_
  
  - [x] 13.2 Create WhatsApp notification functionality


    - Integrate Twilio API for WhatsApp messaging
    - Implement send_whatsapp method with message templates
    - Create WhatsApp templates for: new jobs alert, interview reminder
    - Add error handling for API failures
    - _Requirements: 13.2, 13.4, 13.8_
  
  - [x] 13.3 Implement notification preferences and scheduling


    - Create configure_preferences method to store user notification settings
    - Implement send_daily_digest method that batches jobs into single notification
    - Create send_interview_reminder method triggered 24 hours before interview
    - Implement send_status_update method for application status changes
    - Add notification preference checking before sending
    - Store user email and WhatsApp number securely in database
    - _Requirements: 13.6, 13.9, 13.10_

- [x] 14. Implement LangGraph orchestrator for agent coordination





  - Create `agents/orchestrator.py` with LangGraphOrchestrator class
  - Define state graph with nodes for each agent (JobSearch, MatchScorer, ResumeOptimizer, CoverLetterGenerator, InterviewPrep, CompanyProfiler)
  - Implement execute_daily_search workflow: JobSearch → MatchScorer → NotificationManager
  - Create optimize_resume workflow: ResumeOptimizer with job context
  - Implement generate_cover_letter workflow: CoverLetterGenerator with resume and job data
  - Create prepare_interview workflow: InterviewPrep with job description
  - Implement profile_company workflow: CompanyProfiler with caching
  - Add error handling and recovery for failed agent executions
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 15. Implement task scheduler for autonomous daily searches





  - Create `utils/scheduler.py` with TaskScheduler class using APScheduler
  - Implement schedule_daily_search method with cron-like configuration
  - Create background service that runs independently of Streamlit UI
  - Add job execution logging and error notifications
  - Implement graceful shutdown and restart handling
  - Configure default schedule for 9:00 AM daily
  - _Requirements: 1.1, 1.4, 10.1_

- [x] 16. Build Streamlit UI - Dashboard and navigation




  - [x] 16.1 Create main application structure


    - Implement `app.py` as main entry point with Streamlit configuration
    - Create navigation sidebar with pages: Dashboard, Job Search, Applications, Interview Prep, Settings
    - Implement session state management for user data
    - Add page routing logic
    - _Requirements: 10.5_
  
  - [x] 16.2 Build Dashboard page


    - Create `ui/pages/dashboard.py` with overview metrics
    - Display: total jobs found, applications submitted, interviews scheduled, match score distribution
    - Implement visualizations: application funnel chart, timeline graph, top companies
    - Show daily actionable insights and next steps
    - Add quick action buttons: Search Jobs, Optimize Resume, Prepare Interview
    - _Requirements: 8.8, 10.1, 10.2, 10.5_

- [x] 17. Build Streamlit UI - Job Search and Listings





  - Create `ui/pages/job_search.py` for job discovery interface
  - Implement manual search form with keyword, salary, location filters
  - Display job listings in cards with: title, company, salary, match score, remote type
  - Add sorting options: match score, salary, posted date
  - Implement job detail view with full description and company profile
  - Create action buttons: Save, Apply, Generate Cover Letter, View Company Profile
  - Add pagination for large result sets
  - _Requirements: 1.1, 1.2, 1.3, 6.4, 6.5_


- [x] 18. Build Streamlit UI - Application Tracker



  - Create `ui/pages/applications.py` for application management
  - Display applications in table with: job title, company, status, applied date, HR contact
  - Implement status update dropdown for each application
  - Create HR contact form with fields: name, email, phone, LinkedIn, designation, notes
  - Add HR contact directory view with search functionality
  - Implement export button to download application history as CSV/Excel
  - Show application statistics: total applied, interview rate, offer rate
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 19. Build Streamlit UI - Resume Optimizer





  - Create `ui/pages/resume_optimizer.py` for resume analysis
  - Implement file upload for resume (PDF, DOCX, TXT)
  - Add text area for manual resume input
  - Create job selection dropdown for targeted optimization
  - Display analysis results: ATS keywords, missing skills, improvement suggestions
  - Show before/after comparisons for suggested rewrites
  - Add copy button for optimized sections
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 20. Build Streamlit UI - Cover Letter Generator





  - Create `ui/pages/cover_letter.py` for letter generation
  - Implement job selection dropdown
  - Add tone selection: Professional, Enthusiastic, Technical
  - Display generated cover letter in editable text area
  - Create action buttons: Regenerate, Copy, Save, Download
  - Show character count and formatting preview
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 21. Build Streamlit UI - Interview Prep





  - [x] 21.1 Create interview question generation interface


    - Implement `ui/pages/interview_prep.py` with job selection
    - Add question type selector: Technical, Behavioral, Both
    - Display generated questions in expandable sections
    - Show difficulty level and category for each question
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [x] 21.2 Create mock interview interface


    - Implement interactive Q&A mode with question display and answer input
    - Add timer for each question
    - Display feedback and improvement suggestions after each answer
    - Show overall interview performance summary
    - _Requirements: 4.3, 4.4_
  
  - [x] 21.3 Create custom question management interface


    - Add form to input custom interview questions
    - Implement category, topic, and difficulty selectors
    - Create button to generate ideal answer using LLM
    - Display custom questions library with filters
    - Add edit and delete buttons for each question
    - Show user answer and ideal answer side-by-side
    - Implement search functionality for question library
    - _Requirements: 4.6, 4.7, 4.8, 4.9, 4.10_

- [x] 22. Build Streamlit UI - Company Profiler





  - Create `ui/pages/company_profile.py` for company research
  - Implement company name input or selection from job listings
  - Display company information: Glassdoor rating, employee count, funding stage
  - Show recent news articles with links
  - Display GenAI focus score with explanation
  - Show LLM-generated fit analysis summary
  - Add refresh button to update cached profile
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 23. Build Streamlit UI - Settings and Configuration





  - Create `ui/pages/settings.py` for user preferences
  - Implement user profile form: name, email, skills, experience, target salary, preferred locations
  - Add resume upload and management
  - Create notification preferences form: email enabled, WhatsApp enabled, daily digest time, notification types
  - Implement credential management: Naukri login, SMTP settings, Twilio settings
  - Add search criteria configuration: keywords, salary threshold, remote preference
  - Create database backup and restore buttons
  - _Requirements: 7.4, 13.6, 13.9, 13.10_

- [x] 24. Implement configuration management and initialization





  - Create `config/config_manager.py` to load and validate config.yaml
  - Implement default configuration generation on first run
  - Add configuration validation with helpful error messages
  - Create initialization script `scripts/init_app.py` that sets up database, config, and dependencies
  - Implement health check for all dependencies (Ollama, Selenium, database)
  - _Requirements: 12.3_

- [x] 25. Implement logging and error handling





  - Create `utils/logger.py` with rotating file handler
  - Implement log levels: DEBUG, INFO, ERROR
  - Add context logging for agent executions
  - Create error notification system for critical failures
  - Implement user-friendly error messages in UI
  - _Requirements: 11.5_

- [x] 26. Create setup and deployment scripts





  - Create `scripts/setup.sh` for initial installation (install dependencies, download Ollama model, initialize database)
  - Implement `scripts/run_scheduler.py` for background task execution
  - Create `scripts/backup_db.py` for database backup automation
  - Write `README.md` with installation instructions, configuration guide, and usage examples
  - Create `docker-compose.yml` for containerized deployment (optional)
  - _Requirements: 12.4_

- [x] 27. Integration and end-to-end workflow testing





  - Test complete daily search workflow: scraping → filtering → scoring → notification
  - Verify resume optimization workflow with real job postings
  - Test cover letter generation with various job types
  - Validate interview prep workflow including custom questions
  - Test application tracking with status updates and HR contacts
  - Verify notification delivery via email and WhatsApp
  - Test data export functionality
  - Validate credential encryption and security
  - _Requirements: All requirements_
