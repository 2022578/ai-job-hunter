# Quick Start Guide

Get up and running with GenAI Job Assistant in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- 4GB RAM minimum
- Internet connection

## Installation

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

### Option 2: Docker

```bash
docker-compose up -d
```

Access at: http://localhost:8501

## Configuration

1. **Edit your profile** in `config/config.yaml`:
   ```yaml
   user:
     name: "Your Name"
     email: "your.email@example.com"
     skills:
       - "Python"
       - "LangChain"
       - "GenAI"
     experience_years: 5
     target_salary: 3500000  # ₹35L
   ```

2. **Set job search criteria**:
   ```yaml
   job_search:
     keywords:
       - "GenAI"
       - "LLM"
       - "LangChain"
     min_salary: 3500000
     preferred_locations:
       - "Bangalore"
       - "Remote"
   ```

3. **Configure notifications** (optional):
   ```yaml
   notifications:
     email:
       enabled: true
       smtp_server: "smtp.gmail.com"
       smtp_port: 587
       username: "your.email@gmail.com"
       password: "your-app-password"
   ```

## First Run

### Start the UI

```bash
streamlit run app.py
```

Open browser to: http://localhost:8501

### Start Background Scheduler

```bash
python scripts/run_scheduler.py
```

This will run daily job searches automatically.

## Basic Usage

### 1. Search for Jobs

**Manual Search:**
- Go to "Job Search" page
- Enter keywords and filters
- Click "Search"

**Automated Search:**
- Scheduler runs daily at 9 AM (configurable)
- Sends notifications for new jobs

### 2. Optimize Resume

- Go to "Resume Optimizer" page
- Upload your resume or paste text
- Select a job to optimize for
- Get ATS-friendly suggestions

### 3. Generate Cover Letter

- Go to "Cover Letter" page
- Select a job
- Choose tone (Professional/Enthusiastic/Technical)
- Click "Generate"
- Copy or download

### 4. Prepare for Interview

- Go to "Interview Prep" page
- Select a job
- Generate questions
- Practice with mock interview
- Add custom questions

### 5. Track Applications

- Go to "Applications" page
- Update application status
- Add HR contact information
- Export history to Excel

## Tips

### Get Better Results

1. **Update your profile** with accurate skills and experience
2. **Add specific keywords** relevant to your target roles
3. **Configure notifications** to stay updated
4. **Review match scores** to prioritize applications
5. **Use custom questions** to prepare for specific companies

### Optimize Performance

1. **Use smaller LLM models** for faster responses:
   ```yaml
   llm:
     model_name: "llama3:8b"  # Instead of llama3:70b
   ```

2. **Adjust scraping delays** if getting rate limited:
   ```yaml
   scraping:
     delay_between_requests: 3  # Increase from 2
   ```

3. **Enable caching** for company profiles (already enabled by default)

### Troubleshooting

**Ollama not running:**
```bash
ollama serve
```

**Model not found:**
```bash
ollama pull llama3
```

**Database issues:**
```bash
python scripts/init_app.py
```

**Check logs:**
```bash
tail -f logs/job_assistant.log
```

## Next Steps

1. **Set up automated backups:**
   ```bash
   python scripts/backup_db.py backup
   ```

2. **Configure daily schedule** in `config/config.yaml`:
   ```yaml
   scheduler:
     daily_search_time: "09:00"  # 9 AM
   ```

3. **Explore advanced features:**
   - Company profiling
   - Custom interview questions
   - HR contact management
   - Application analytics

## Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [Troubleshooting](#troubleshooting) section
- Check logs in `logs/` directory
- Run health check: `python scripts/init_app.py`

## Common Commands

```bash
# Start UI
streamlit run app.py

# Start scheduler
python scripts/run_scheduler.py

# Backup database
python scripts/backup_db.py backup

# List backups
python scripts/backup_db.py list

# Restore backup
python scripts/backup_db.py restore

# Check health
python scripts/init_app.py

# View logs
tail -f logs/job_assistant.log
```

## Security Notes

- Encryption key is auto-generated in `.env`
- Credentials are encrypted before storage
- All data stored locally
- No cloud uploads or telemetry

## Support

For issues or questions:
1. Check logs: `logs/job_assistant.log`
2. Run diagnostics: `python scripts/init_app.py`
3. Review configuration: `config/config.yaml`

Happy job hunting! 🚀
