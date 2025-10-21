# Requirements Document

## Introduction

The GenAI Job Assistant is an autonomous, LLM-powered system designed to streamline job searching, application preparation, and interview readiness for professionals targeting GenAI/LLM roles. The system leverages open-source tools, LangGraph for agentic workflows, and provides a Streamlit-based interface for user interaction. It automates daily job searches, optimizes resumes, generates cover letters, provides interview preparation, and tracks application history while maintaining user privacy and security.

## Glossary

- **Job Assistant System**: The complete autonomous job search and career management application
- **Job Search Agent**: The component responsible for discovering and filtering job listings
- **Resume Optimizer**: The LLM-powered component that analyzes and improves resume content
- **Cover Letter Generator**: The component that creates customized cover letters for specific job postings
- **Interview Prep Agent**: The component that generates interview questions and provides mock interview capabilities
- **Job Tracker**: The component that maintains application history and status
- **Company Profiler**: The component that researches and summarizes company information
- **Match Scorer**: The component that calculates job-candidate alignment scores
- **User**: The job seeker using the system
- **Job Listing**: A job posting from Naukri.com or other sources
- **ATS**: Applicant Tracking System used by employers to filter resumes
- **LangGraph**: The framework used for building multi-agent workflows
- **Streamlit**: The web framework used for the user interface

## Requirements

### Requirement 1

**User Story:** As a job seeker, I want the system to automatically search for relevant jobs daily, so that I don't miss new opportunities matching my criteria

#### Acceptance Criteria

1. WHEN the scheduled time arrives each day, THE Job Search Agent SHALL execute a search across configured job sources
2. WHILE executing the search, THE Job Search Agent SHALL filter listings by salary threshold of ₹35L or higher
3. WHEN filtering results, THE Job Search Agent SHALL include only listings containing at least one keyword from the set: "GenAI", "LLM", "Autonomous Agents", "LangChain", "LangGraph"
4. WHEN new matching listings are found, THE Job Assistant System SHALL notify the User through the configured notification channel
5. THE Job Search Agent SHALL store all discovered listings in the local database with timestamp and source information

### Requirement 2

**User Story:** As a job seeker, I want my resume analyzed and optimized for specific jobs, so that I can improve my chances of passing ATS screening

#### Acceptance Criteria

1. WHEN the User requests resume analysis, THE Resume Optimizer SHALL process the current resume using an open-source LLM
2. THE Resume Optimizer SHALL identify missing ATS keywords relevant to GenAI roles
3. WHEN analyzing for a specific job, THE Resume Optimizer SHALL suggest custom rewrites highlighting relevant experience
4. THE Resume Optimizer SHALL provide recommendations for emphasizing GenAI, LLM, and autonomous agent experience
5. THE Resume Optimizer SHALL present suggestions in the Streamlit interface with before-and-after comparisons

### Requirement 3

**User Story:** As a job seeker, I want custom cover letters generated for each job, so that I can quickly apply with personalized content

#### Acceptance Criteria

1. WHEN the User selects a job listing, THE Cover Letter Generator SHALL create a customized cover letter using the job description, User resume, and relevant projects
2. THE Cover Letter Generator SHALL incorporate specific keywords and requirements from the job posting
3. THE Cover Letter Generator SHALL maintain a professional tone appropriate for the target company and role
4. WHEN generation is complete, THE Job Assistant System SHALL display the cover letter in an editable text area
5. THE Job Assistant System SHALL provide options to copy, save, or regenerate the cover letter

### Requirement 4

**User Story:** As a job seeker, I want interview preparation materials for shortlisted roles, so that I can practice and improve my interview performance

#### Acceptance Criteria

1. WHEN the User marks a job as shortlisted, THE Interview Prep Agent SHALL generate relevant technical interview questions based on the job description
2. THE Interview Prep Agent SHALL generate behavioral interview questions appropriate for the role level and company type
3. WHEN the User requests mock interview mode, THE Interview Prep Agent SHALL conduct an interactive question-answer session using an open-source LLM
4. WHEN the User provides answers, THE Interview Prep Agent SHALL analyze responses and provide improvement feedback
5. THE Interview Prep Agent SHALL maintain separate question sets for technical and behavioral categories
6. WHEN the User adds a custom interview question, THE Interview Prep Agent SHALL store the question in the local database
7. WHEN the User provides an answer to their custom question, THE Interview Prep Agent SHALL generate an ideal answer using an open-source LLM and store both versions
8. WHEN preparing for future interviews, THE Interview Prep Agent SHALL retrieve and display the User's custom questions with their answers and ideal answers for review
9. THE Interview Prep Agent SHALL allow the User to edit, delete, or refine stored questions and answers
10. THE Interview Prep Agent SHALL categorize custom questions by topic, difficulty level, and question type for easy retrieval

### Requirement 5

**User Story:** As a job seeker, I want career insights and recommendations, so that I can make informed decisions about my job search strategy

#### Acceptance Criteria

1. WHEN the User requests career insights, THE Job Assistant System SHALL analyze current market trends for GenAI roles
2. THE Job Assistant System SHALL identify companies with active hiring in GenAI and LLM domains
3. THE Job Assistant System SHALL recommend skills or certifications that increase hiring probability based on job listing analysis
4. THE Job Assistant System SHALL suggest relevant thought leaders and influencers to follow in the GenAI space
5. THE Job Assistant System SHALL present insights through visualizations in the Streamlit dashboard

### Requirement 6

**User Story:** As a job seeker, I want each job scored by relevance, so that I can prioritize applications efficiently

#### Acceptance Criteria

1. WHEN a new job listing is added, THE Match Scorer SHALL calculate a relevance score from 0 to 100
2. THE Match Scorer SHALL evaluate alignment with User experience, salary goals, and desired technology stack
3. THE Match Scorer SHALL weight factors including: required skills match, salary range, remote flexibility, and company profile
4. WHEN displaying job listings, THE Job Assistant System SHALL sort results by match score in descending order
5. THE Job Assistant System SHALL display the score and contributing factors for each job in the interface

### Requirement 7

**User Story:** As a job seeker, I want my credentials stored securely, so that my private data remains protected

#### Acceptance Criteria

1. WHEN the User provides authentication credentials, THE Job Assistant System SHALL store them using encryption in local storage or environment variables
2. THE Job Assistant System SHALL NOT store plain-text passwords in any file or database
3. WHEN accessing external services, THE Job Assistant System SHALL use secure token-based authentication where available
4. THE Job Assistant System SHALL require explicit User opt-in before storing any private data
5. THE Job Assistant System SHALL provide a mechanism to delete all stored credentials on User request

### Requirement 8

**User Story:** As a job seeker, I want to track my application history, status, and HR contacts, so that I can manage my job search pipeline and maintain professional relationships

#### Acceptance Criteria

1. WHEN the User applies to a job, THE Job Tracker SHALL record the job title, company name, application date, and initial status
2. THE Job Tracker SHALL allow the User to update status to one of: "Applied", "Interview Scheduled", "Offered", "Rejected"
3. THE Job Tracker SHALL support marking jobs as "Saved for Later" or "Not Interested"
4. WHEN the User adds HR contact information, THE Job Tracker SHALL store name, email, phone, LinkedIn URL, designation, and notes
5. THE Job Tracker SHALL link HR contacts to specific applications
6. THE Job Tracker SHALL provide a searchable directory of all HR contacts
7. WHEN the User requests export, THE Job Tracker SHALL generate a CSV or Excel file containing complete application history including HR contact details
8. THE Job Tracker SHALL display application statistics and timeline in the Streamlit dashboard

### Requirement 9

**User Story:** As a job seeker, I want company profiles for job postings, so that I can evaluate cultural fit and company quality

#### Acceptance Criteria

1. WHEN the User views a job listing, THE Company Profiler SHALL retrieve available information including funding status, Glassdoor rating, and recent news
2. THE Company Profiler SHALL analyze the company's focus on AI and GenAI technologies
3. WHEN analysis is complete, THE Company Profiler SHALL generate an LLM-powered summary assessing company-candidate fit
4. THE Company Profiler SHALL present information including company culture, growth trajectory, and AI investment
5. THE Job Assistant System SHALL cache company profiles to minimize redundant API calls

### Requirement 10

**User Story:** As a job seeker, I want actionable next-step suggestions, so that I can maintain momentum in my job search

#### Acceptance Criteria

1. WHEN the User accesses the dashboard, THE Job Assistant System SHALL display daily or weekly actionable insights
2. THE Job Assistant System SHALL recommend specific jobs to apply to based on match scores and application history
3. THE Job Assistant System SHALL suggest networking actions such as connecting with specific recruiters
4. THE Job Assistant System SHALL recommend learning resources including courses, articles, and videos relevant to skill gaps
5. THE Job Assistant System SHALL generate a personalized roadmap showing progress toward job search goals

### Requirement 11

**User Story:** As a job seeker, I want the system built with modular agents, so that functionality can be extended and improved over time

#### Acceptance Criteria

1. THE Job Assistant System SHALL implement separate LangGraph agents for: Job Search, Resume Optimization, Cover Letter Generation, Interview Prep, and Company Profiling
2. THE Job Assistant System SHALL support sequential and parallel agent execution using LangGraph's multi-actor nodes
3. WHEN adding new functionality, THE Job Assistant System SHALL allow new agents to be integrated without modifying existing agent code
4. THE Job Assistant System SHALL maintain clear interfaces between agents for data exchange
5. THE Job Assistant System SHALL log agent execution flow for debugging and optimization

### Requirement 12

**User Story:** As a job seeker, I want all data stored locally, so that I maintain control and can access it offline

#### Acceptance Criteria

1. THE Job Assistant System SHALL use SQLite or MongoDB for local data storage
2. THE Job Assistant System SHALL store job listings, application history, user feedback, and tracker status in the local database
3. WHEN the application starts, THE Job Assistant System SHALL initialize the database if it does not exist
4. THE Job Assistant System SHALL provide database backup and restore functionality
5. THE Job Assistant System SHALL ensure all core features function without requiring internet connectivity after initial setup


### Requirement 13

**User Story:** As a job seeker, I want to receive notifications via email and WhatsApp, so that I stay updated on new jobs and important events without constantly checking the app

#### Acceptance Criteria

1. WHEN new matching jobs are found, THE Job Assistant System SHALL send a notification to the User's configured email address
2. WHEN new matching jobs are found, THE Job Assistant System SHALL send a notification to the User's configured WhatsApp number
3. THE Job Assistant System SHALL support daily digest mode where all new jobs are batched into a single email sent at the User's preferred time
4. WHEN an interview date is approaching within 24 hours, THE Job Assistant System SHALL send a reminder notification via email and WhatsApp
5. WHEN an application status changes, THE Job Assistant System SHALL send a notification if the User has enabled status update notifications
6. THE Job Assistant System SHALL allow the User to configure notification preferences including: email enabled/disabled, WhatsApp enabled/disabled, daily digest time, and notification types
7. THE Job Assistant System SHALL use SMTP for email delivery with support for Gmail and Outlook
8. THE Job Assistant System SHALL use Twilio API for WhatsApp message delivery
9. THE Job Assistant System SHALL store the User's email address and WhatsApp number securely in the database
10. THE Job Assistant System SHALL respect the User's notification preferences and not send unwanted notifications
