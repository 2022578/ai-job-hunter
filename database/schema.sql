-- GenAI Job Assistant Database Schema
-- SQLite database for local storage of job listings, applications, and user data

-- Users table: stores user profile information
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    resume_text TEXT,
    resume_path TEXT,
    skills TEXT,  -- JSON array
    experience_years INTEGER,
    target_salary INTEGER,
    preferred_locations TEXT,  -- JSON array
    preferred_remote BOOLEAN,
    desired_tech_stack TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table: stores discovered job listings
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    salary_min INTEGER,
    salary_max INTEGER,
    location TEXT,
    remote_type TEXT,
    description TEXT,
    required_skills TEXT,  -- JSON array
    posted_date TIMESTAMP,
    source_url TEXT UNIQUE,
    source TEXT,
    raw_html TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_score REAL
);

-- Applications table: tracks job applications and their status
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    applied_date TIMESTAMP,
    interview_date TIMESTAMP,
    notes TEXT,
    cover_letter TEXT,
    hr_contact_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (hr_contact_id) REFERENCES hr_contacts(id)
);

-- HR Contacts table: stores HR contact information linked to applications
CREATE TABLE IF NOT EXISTS hr_contacts (
    id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    designation TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- Custom Questions table: stores user's custom interview questions and answers
CREATE TABLE IF NOT EXISTS custom_questions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    user_answer TEXT,
    ideal_answer TEXT,
    category TEXT NOT NULL,
    topic TEXT,
    difficulty TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Company Profiles table: caches company information
CREATE TABLE IF NOT EXISTS company_profiles (
    id TEXT PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL,
    glassdoor_rating REAL,
    employee_count INTEGER,
    funding_stage TEXT,
    recent_news TEXT,  -- JSON array
    genai_focus_score REAL,
    culture_summary TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cache_expiry TIMESTAMP
);

-- Credentials table: stores encrypted credentials for external services
CREATE TABLE IF NOT EXISTS credentials (
    id TEXT PRIMARY KEY,
    service TEXT UNIQUE NOT NULL,  -- "naukri", "linkedin", etc.
    encrypted_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Preferences table: stores user notification settings
CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id TEXT PRIMARY KEY,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_address TEXT NOT NULL,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    whatsapp_number TEXT,
    daily_digest BOOLEAN DEFAULT TRUE,
    interview_reminders BOOLEAN DEFAULT TRUE,
    status_updates BOOLEAN DEFAULT TRUE,
    digest_time TEXT DEFAULT '09:00',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Schema version table: tracks database migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_questions_category ON custom_questions(category);
CREATE INDEX IF NOT EXISTS idx_custom_questions_topic ON custom_questions(topic);
CREATE INDEX IF NOT EXISTS idx_hr_contacts_application_id ON hr_contacts(application_id);
CREATE INDEX IF NOT EXISTS idx_hr_contacts_name ON hr_contacts(name);

-- Insert initial schema version
INSERT OR IGNORE INTO schema_version (version, description) VALUES (1, 'Initial schema');
