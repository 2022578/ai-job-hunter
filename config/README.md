# Configuration Management

This directory contains the configuration management system for the GenAI Job Assistant.

## Files

- `config.yaml` - Main configuration file with all application settings
- `config_manager.py` - Configuration manager module for loading, validating, and managing configuration
- `__init__.py` - Package initialization file

## Configuration Structure

The configuration is organized into the following sections:

### LLM Settings
- Provider (ollama/llamacpp)
- Model name
- Temperature, max tokens, timeout

### Job Search Settings
- Keywords to search for
- Minimum salary threshold
- Preferred locations
- Remote preference
- Search schedule (cron format)

### Scraping Settings
- Naukri.com configuration
- Rate limiting
- User agents for rotation

### Database Settings
- Database type and path
- Backup configuration
- Retention policies

### Notification Settings
- Email configuration (SMTP)
- WhatsApp configuration (Twilio)
- Notification preferences

### User Profile
- Name, email, experience
- Skills and desired tech stack
- Target salary

### Scoring Weights
- Weights for match score calculation
- Skills, salary, tech stack, remote, company profile

### Company Profiling
- Cache duration
- External API enablement

### Security
- Encryption key configuration
- Credential storage method

### Logging
- Log level and file path
- File rotation settings

### UI Settings
- Theme, page title, icon
- Layout preferences

## Usage

### Loading Configuration

```python
from config import load_config

# Load configuration
config = load_config()

# Access configuration values
print(config.llm.model_name)
print(config.job_search.min_salary)
```

### Using Configuration Manager

```python
from config import ConfigManager

# Create manager
manager = ConfigManager("config/config.yaml")

# Load configuration
config = manager.load_config()

# Update configuration
manager.update_config({
    'llm': {
        'model_name': 'mistral'
    }
})

# Save configuration
manager.save_config()
```

### Generating Default Configuration

```python
from config import ConfigManager

manager = ConfigManager("new_config.yaml")
manager.generate_default_config()
```

## Configuration Validation

The configuration manager automatically validates all settings when loading:

- LLM provider must be 'ollama' or 'llamacpp'
- Salary values must be non-negative
- Scoring weights should sum to 1.0
- Log level must be valid (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Email/WhatsApp settings validated if enabled

Validation errors will raise a `ConfigurationError` with detailed messages.

## Environment Variables

Some sensitive configuration values can be overridden with environment variables:

- `ENCRYPTION_KEY` - Encryption key for credentials
- `OLLAMA_HOST` - Ollama server URL
- `DATABASE_PATH` - Database file path
- `LOG_LEVEL` - Logging level

See `.env.example` for a complete list of supported environment variables.

## First-Time Setup

1. Run the initialization script:
   ```bash
   python scripts/init_app.py
   ```

2. Edit `config/config.yaml` with your preferences:
   - Update user profile information
   - Configure notification settings (email/WhatsApp)
   - Adjust job search criteria
   - Set LLM model preferences

3. Configure credentials in the UI or via environment variables

## Configuration Best Practices

1. **Keep sensitive data in environment variables** - Don't commit credentials to version control
2. **Use meaningful keywords** - Add specific GenAI-related terms to improve job matching
3. **Adjust scoring weights** - Customize based on your priorities (skills vs salary vs remote)
4. **Enable notifications gradually** - Start with email, then add WhatsApp if needed
5. **Review logs regularly** - Set appropriate log level (INFO for production, DEBUG for troubleshooting)

## Troubleshooting

### Configuration file not found
- Run `python scripts/init_app.py` to generate default configuration

### Validation errors
- Check error messages for specific issues
- Ensure all required fields are filled
- Verify scoring weights sum to 1.0

### Environment variables not loading
- Ensure `.env` file exists in project root
- Check file permissions
- Verify variable names match expected format

## Advanced Configuration

### Custom Scoring Algorithm

Modify scoring weights in `config.yaml`:

```yaml
scoring:
  skills_match_weight: 0.40      # Increase skills importance
  salary_match_weight: 0.20      # Decrease salary importance
  tech_stack_match_weight: 0.25
  remote_flexibility_weight: 0.10
  company_profile_weight: 0.05
```

### Multiple Search Schedules

While the configuration supports one schedule, you can run multiple searches manually or create custom scripts with different criteria.

### Custom LLM Models

To use a different model:

1. Pull the model: `ollama pull <model-name>`
2. Update `config.yaml`:
   ```yaml
   llm:
     model_name: "mistral"  # or any other model
   ```

## API Reference

See `config_manager.py` for detailed API documentation of all configuration classes and methods.
