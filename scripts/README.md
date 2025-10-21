# Scripts Directory

This directory contains utility scripts for setup, maintenance, and deployment of the GenAI Job Assistant.

## Scripts Overview

### Setup Scripts

#### `setup.sh` (Linux/Mac)
Automated installation and setup script for Unix-based systems.

**Usage:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**What it does:**
- Checks Python version
- Creates virtual environment
- Installs dependencies
- Checks Ollama installation
- Downloads llama3 model
- Verifies Chrome/Chromium
- Initializes application

#### `setup.bat` (Windows)
Windows equivalent of setup.sh.

**Usage:**
```cmd
scripts\setup.bat
```

### Application Scripts

#### `init_app.py`
Initializes the application, database, and validates dependencies.

**Usage:**
```bash
python scripts/init_app.py
```

**Features:**
- Creates directory structure
- Sets up environment variables
- Generates encryption key
- Initializes database
- Runs health checks
- Validates configuration

#### `run_scheduler.py`
Runs the background scheduler service for automated job searches.

**Usage:**
```bash
python scripts/run_scheduler.py
```

**Features:**
- Loads configuration
- Initializes all agents
- Starts scheduled tasks
- Handles graceful shutdown
- Logs execution

#### `scheduler_example.py`
Simple example demonstrating scheduler usage.

**Usage:**
```bash
python scripts/scheduler_example.py
```

### Maintenance Scripts

#### `backup_db.py`
Database backup and restore utility.

**Usage:**
```bash
# Create backup
python scripts/backup_db.py backup

# Create uncompressed backup
python scripts/backup_db.py backup --no-compress

# List all backups
python scripts/backup_db.py list

# Restore from backup (interactive)
python scripts/backup_db.py restore

# Restore specific backup
python scripts/backup_db.py restore --backup-file path/to/backup.db.gz

# Cleanup old backups
python scripts/backup_db.py cleanup

# Force restore without confirmation
python scripts/backup_db.py restore --force

# Use custom config
python scripts/backup_db.py backup --config path/to/config.yaml
```

**Features:**
- Compressed backups (gzip)
- Automatic rotation
- Safe restore with pre-restore backup
- Configurable retention policy
- Detailed backup information

## Common Workflows

### Initial Setup

```bash
# 1. Run setup script
./scripts/setup.sh  # or setup.bat on Windows

# 2. Configure application
# Edit config/config.yaml with your preferences

# 3. Start application
streamlit run app.py
```

### Daily Operations

```bash
# Start UI
streamlit run app.py

# Start scheduler (in separate terminal)
python scripts/run_scheduler.py

# Create backup
python scripts/backup_db.py backup
```

### Maintenance

```bash
# Check application health
python scripts/init_app.py

# List backups
python scripts/backup_db.py list

# Cleanup old backups
python scripts/backup_db.py cleanup

# View logs
tail -f logs/job_assistant.log
tail -f logs/scheduler.log
```

### Troubleshooting

```bash
# Reinitialize application
python scripts/init_app.py

# Check scheduler
python scripts/scheduler_example.py

# Restore from backup
python scripts/backup_db.py restore
```

## Automated Backups

### Linux/Mac (cron)

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/genai-job-assistant && /path/to/venv/bin/python scripts/backup_db.py backup
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Job Assistant Backup"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `scripts\backup_db.py backup`
   - Start in: `C:\path\to\genai-job-assistant`

## Environment Variables

Scripts use the following environment variables:

```bash
# Required
ENCRYPTION_KEY=your-generated-key

# Optional
OLLAMA_HOST=http://localhost:11434
PYTHONUNBUFFERED=1
```

## Configuration

Scripts read from `config/config.yaml`:

```yaml
database:
  path: "data/job_assistant.db"
  backup_directory: "data/backups"
  max_backups: 7

scheduler:
  daily_search_time: "09:00"

logging:
  file_path: "logs/job_assistant.log"
  level: "INFO"
```

## Exit Codes

- `0`: Success
- `1`: Error occurred

## Logging

Scripts log to:
- Console (stdout/stderr)
- `logs/job_assistant.log` (application logs)
- `logs/scheduler.log` (scheduler logs)

## Dependencies

All scripts require:
- Python 3.10+
- Virtual environment activated
- Dependencies installed (`pip install -r requirements.txt`)

## Support

For issues:
1. Check logs in `logs/` directory
2. Run `python scripts/init_app.py` for diagnostics
3. Review configuration in `config/config.yaml`

## See Also

- [README.md](../README.md) - Main documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment guide
