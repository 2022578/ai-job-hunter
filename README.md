# GenAI Job Assistant 🤖

An autonomous, LLM-powered job search assistant designed to streamline job searching, application preparation, and interview readiness for GenAI/LLM roles.

## Features

- **Autonomous Job Search**: Daily automated searches on Naukri.com with smart filtering
- **Resume Optimization**: AI-powered resume analysis and ATS optimization
- **Cover Letter Generation**: Personalized cover letters for each job application
- **Interview Preparation**: Custom question generation and mock interview sessions
- **Company Profiling**: Research companies with AI-powered fit analysis
- **Application Tracking**: Manage your job pipeline with HR contact management
- **Smart Notifications**: Email and WhatsApp alerts for new jobs and interviews

## Tech Stack

- **Framework**: LangGraph for multi-agent orchestration
- **UI**: Streamlit
- **LLM**: Ollama (open-source models)
- **Database**: SQLite
- **Scraping**: Selenium + BeautifulSoup4
- **Notifications**: SMTP (email) + Twilio (WhatsApp)

## Project Structure

```
genai-job-assistant/
├── agents/          # Specialized agents (job search, resume optimizer, etc.)
├── models/          # Data models and validation
├── database/        # Database schema and repositories
├── scrapers/        # Web scraping logic
├── ui/              # Streamlit pages and components
├── utils/           # Helper functions and utilities
├── config/          # Configuration files
├── tests/           # Unit and integration tests
├── logs/            # Application logs
├── data/            # Database and cached data
└── scripts/         # Setup and maintenance scripts
```

## Installation

### Prerequisites

- Python 3.10+
- Ollama (for LLM)
- Chrome/Chromium (for web scraping)

### Quick Setup (Automated)

**Linux/Mac:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

The setup script will:
- Create virtual environment
- Install all dependencies
- Download Ollama model (llama3)
- Initialize database
- Validate all components

### Manual Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd genai-job-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama and download model**
   ```bash 
   # Install Ollama from https://ollama.ai
   ollama serve  # Start Ollama service
   ollama pull llama3  # Download model
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Generate encryption key**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   # Add the output to .env as ENCRYPTION_KEY
   ```

7. **Initialize database**
   ```bash
   python scripts/init_app.py
   ```

8. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Docker Setup (Optional)

For containerized deployment:

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **Access the application**
   - Streamlit UI: http://localhost:8501
   - Ollama API: http://localhost:11434

3. **View logs**
   ```bash
   docker-compose logs -f job-assistant
   docker-compose logs -f scheduler
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

**Docker Features:**
- Isolated environment with all dependencies
- Automatic Ollama model download
- Persistent data volumes
- Separate scheduler service
- Easy scaling and deployment

## Configuration

Edit `config/config.yaml` to customize:
- Job search criteria (keywords, salary, locations)
- LLM settings (model, temperature)
- Notification preferences (email, WhatsApp)
- Scraping behavior (rate limits, retries)
- Match scoring weights

## Usage

### Daily Automated Search

The system can run autonomous daily job searches using the built-in task scheduler.

**Start the scheduler service:**
```bash
python scripts/run_scheduler.py
```

This will:
- Run daily job searches at 9:00 AM (configurable in `config/config.yaml`)
- Score and rank discovered jobs
- Send notifications via email/WhatsApp
- Run independently of the Streamlit UI

**Scheduler Features:**
- Cron-based scheduling for flexible timing
- Graceful shutdown handling (Ctrl+C)
- Job execution logging and error notifications
- Background service that runs continuously

For more details, see [Scheduler Documentation](utils/SCHEDULER_README.md)

**Quick Example:**
```bash
# Run a simple scheduler example
python scripts/scheduler_example.py

# Validate scheduler installation
python tests/validate_scheduler.py
```

### Interactive Mode

Access the Streamlit dashboard at `http://localhost:8501` to:
- Search for jobs manually
- Optimize your resume for specific roles
- Generate cover letters
- Prepare for interviews with custom Q&A
- Track applications and HR contacts
- Research companies

## Notifications

### Email Setup (Gmail)

1. Enable 2-factor authentication
2. Generate app-specific password
3. Add credentials to `.env` or `config.yaml`

### WhatsApp Setup (Twilio)

1. Sign up for Twilio free trial
2. Get WhatsApp sandbox number
3. Add credentials to `.env` or `config.yaml`

## Security

- All credentials are encrypted using Fernet encryption
- Data stored locally (no cloud uploads)
- Encryption key stored in environment variable
- No telemetry or analytics collection

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- Each agent is independent and communicates via LangGraph
- Database operations use repository pattern
- All external API calls have retry logic and error handling

## Database Management

### Backup Database

**Create backup:**
```bash
python scripts/backup_db.py backup
```

**Create uncompressed backup:**
```bash
python scripts/backup_db.py backup --no-compress
```

**List available backups:**
```bash
python scripts/backup_db.py list
```

**Restore from backup:**
```bash
python scripts/backup_db.py restore
# Or specify backup file:
python scripts/backup_db.py restore --backup-file data/backups/job_assistant_backup_20241020_120000.db.gz
```

**Cleanup old backups:**
```bash
python scripts/backup_db.py cleanup
```

### Automated Backups

**Linux/Mac (cron):**
```bash
# Add to crontab (daily backup at 2 AM)
0 2 * * * cd /path/to/genai-job-assistant && /path/to/venv/bin/python scripts/backup_db.py backup
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `scripts\backup_db.py backup`
7. Start in: `C:\path\to\genai-job-assistant`

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Scraping Issues

- Check if Chrome/Chromium is installed
- Verify Selenium WebDriver is compatible
- Increase rate limit delays in config
- Check for CAPTCHA detection

### Database Issues

```bash
# Backup current database
python scripts/backup_db.py backup

# Reinitialize database
python scripts/init_app.py

# Restore from backup if needed
python scripts/backup_db.py restore
```

### Scheduler Issues

```bash
# Check scheduler logs
tail -f logs/scheduler.log

# Test scheduler with example
python scripts/scheduler_example.py

# Validate scheduler setup
python tests/validate_scheduler.py
```

### Permission Issues (Linux/Mac)

```bash
# Make scripts executable
chmod +x scripts/setup.sh
chmod +x scripts/*.py
```

## Deployment

### Local Deployment

**Run as background service (Linux/Mac):**

1. Create systemd service file: `/etc/systemd/system/job-assistant-scheduler.service`
   ```ini
   [Unit]
   Description=GenAI Job Assistant Scheduler
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/genai-job-assistant
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python scripts/run_scheduler.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable job-assistant-scheduler
   sudo systemctl start job-assistant-scheduler
   sudo systemctl status job-assistant-scheduler
   ```

**Run as background service (Windows):**

Use NSSM (Non-Sucking Service Manager):
```cmd
nssm install JobAssistantScheduler "C:\path\to\venv\Scripts\python.exe" "scripts\run_scheduler.py"
nssm set JobAssistantScheduler AppDirectory "C:\path\to\genai-job-assistant"
nssm start JobAssistantScheduler
```

### Cloud Deployment

**AWS EC2:**
1. Launch EC2 instance (t2.medium or larger)
2. Install dependencies and setup application
3. Configure security groups (port 8501 for Streamlit)
4. Use systemd for service management
5. Set up CloudWatch for monitoring

**Google Cloud Platform:**
1. Create Compute Engine instance
2. Follow local deployment steps
3. Configure firewall rules
4. Use Cloud Logging for logs

**Docker Deployment:**
```bash
# Build and push to registry
docker build -t genai-job-assistant:latest .
docker tag genai-job-assistant:latest your-registry/genai-job-assistant:latest
docker push your-registry/genai-job-assistant:latest

# Deploy on server
docker-compose up -d
```

### Environment Variables

Required environment variables for deployment:

```bash
# Encryption
ENCRYPTION_KEY=your-generated-key

# Ollama (if external)
OLLAMA_HOST=http://localhost:11434

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# WhatsApp (optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

## Monitoring

### Logs

Application logs are stored in `logs/` directory:
- `job_assistant.log` - Main application logs
- `scheduler.log` - Scheduler service logs

**View logs:**
```bash
# Tail main logs
tail -f logs/job_assistant.log

# Tail scheduler logs
tail -f logs/scheduler.log

# Search for errors
grep ERROR logs/job_assistant.log
```

### Health Checks

**Check application health:**
```bash
python scripts/init_app.py
```

**Check scheduler status:**
```bash
# If running as systemd service
sudo systemctl status job-assistant-scheduler

# Check process
ps aux | grep run_scheduler.py
```

## Performance Optimization

### Database Optimization

```bash
# Vacuum database to reclaim space
sqlite3 data/job_assistant.db "VACUUM;"

# Analyze for query optimization
sqlite3 data/job_assistant.db "ANALYZE;"
```

### LLM Optimization

- Use smaller models for faster responses (e.g., `llama3:8b` instead of `llama3:70b`)
- Adjust temperature and max_tokens in config
- Enable response caching for repeated queries

### Scraping Optimization

- Increase delays between requests to avoid rate limiting
- Use headless browser mode
- Implement request caching

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License

## Disclaimer

This tool is for personal use only. Respect job portal terms of service and rate limits. Use responsibly.
