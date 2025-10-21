# Notification Manager

The Notification Manager provides email and WhatsApp notification capabilities for the GenAI Job Assistant. It supports daily job digests, interview reminders, and application status updates.

## Components

### 1. NotificationManager (Email)
Handles email notifications using SMTP.

**Features:**
- Daily job digest emails with HTML formatting
- Interview reminder emails
- Application status update emails
- Support for Gmail and Outlook SMTP servers

**Configuration:**
```python
from utils.notification_manager import NotificationManager

email_manager = NotificationManager(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",  # Use app-specific password
    from_address="your-email@gmail.com"
)
```

### 2. WhatsAppNotificationManager
Handles WhatsApp notifications using Twilio API.

**Features:**
- New jobs alert messages
- Interview reminder messages
- Formatted text messages with job details

**Configuration:**
```python
from utils.notification_manager import WhatsAppNotificationManager

whatsapp_manager = WhatsAppNotificationManager(
    account_sid="your-twilio-account-sid",
    auth_token="your-twilio-auth-token",
    from_number="whatsapp:+14155238886"  # Twilio sandbox number
)
```

**Note:** Requires `twilio` package: `pip install twilio`

### 3. UnifiedNotificationService
Combines email and WhatsApp notifications with user preference management.

**Features:**
- Unified interface for all notification types
- User preference checking before sending
- Support for multiple notification channels
- Automated interview reminder scheduling

**Configuration:**
```python
from utils.notification_manager import UnifiedNotificationService
from database.repositories.notification_preferences_repository import NotificationPreferencesRepository

unified_service = UnifiedNotificationService(
    email_manager=email_manager,
    whatsapp_manager=whatsapp_manager,
    preferences_repository=prefs_repo
)
```

## Usage Examples

### Send Daily Digest

```python
from models.job import JobListing

jobs = [
    JobListing(
        id="job-1",
        title="Senior GenAI Engineer",
        company="Tech Corp",
        salary_min=4000000,
        location="Bangalore",
        remote_type="hybrid",
        # ... other fields
    )
]

# Via email only
email_manager.send_daily_digest_email("user@example.com", jobs)

# Via unified service (respects user preferences)
unified_service.send_daily_digest("user-123", jobs)
```

### Send Interview Reminder

```python
from models.application import Application
from datetime import datetime, timedelta

application = Application(
    id="app-1",
    job_id="job-1",
    user_id="user-123",
    status="interview",
    interview_date=datetime.now() + timedelta(days=1),
    # ... other fields
)

# Via unified service
unified_service.send_interview_reminder("user-123", application, job)
```

### Send Status Update

```python
# Via unified service
unified_service.send_status_update(
    user_id="user-123",
    application=application,
    job=job,
    old_status="applied",
    new_status="interview"
)
```

### Configure User Preferences

```python
from models.notification import NotificationPreferences

preferences = NotificationPreferences(
    user_id="user-123",
    email_address="user@example.com",
    email_enabled=True,
    whatsapp_enabled=True,
    whatsapp_number="whatsapp:+919876543210",
    daily_digest=True,
    interview_reminders=True,
    status_updates=True,
    digest_time="09:00"
)

unified_service.configure_preferences("user-123", preferences)
```

### Automated Interview Reminders

```python
# Check all applications and send reminders for interviews within 24 hours
applications_with_jobs = [
    (user_id, application, job),
    # ... more tuples
]

reminders_sent = unified_service.check_and_send_interview_reminders(
    applications_with_jobs
)
print(f"Sent {reminders_sent} interview reminders")
```

## Email Templates

### Daily Digest
- Professional HTML layout
- Job cards with match scores
- Salary information
- Skills and location
- Direct links to job postings

### Interview Reminder
- Interview details (date, time, location)
- Company and position information
- Preparation tips
- Link to job details

### Status Update
- Visual status transition (old → new)
- Job details
- Timestamp of update

## WhatsApp Templates

### New Jobs Alert
- Concise job summaries
- Top 3 jobs with match scores
- Company and location info
- Direct links

### Interview Reminder
- Interview date and time
- Company and position
- Good luck message
- Link to job details

## Configuration (config.yaml)

```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    smtp_username: "your-email@gmail.com"
    smtp_password: "your-app-password"
    from_address: "your-email@gmail.com"
    to_address: "your-email@gmail.com"
  
  whatsapp:
    enabled: true
    twilio_account_sid: "your-twilio-account-sid"
    twilio_auth_token: "your-twilio-auth-token"
    twilio_whatsapp_number: "whatsapp:+14155238886"
    user_whatsapp_number: "whatsapp:+919876543210"
  
  preferences:
    daily_digest: true
    digest_time: "09:00"
    interview_reminders: true
    status_updates: true
```

## SMTP Setup

### Gmail
1. Enable 2-factor authentication
2. Generate app-specific password: https://myaccount.google.com/apppasswords
3. Use app password in configuration

### Outlook
1. Use your Microsoft account email
2. Use your account password
3. SMTP server: `smtp.office365.com`
4. Port: 587

## Twilio Setup

1. Sign up for Twilio: https://www.twilio.com/try-twilio
2. Get Account SID and Auth Token from console
3. Use Twilio sandbox number for testing: `whatsapp:+14155238886`
4. For production, apply for WhatsApp Business API approval

## Database Schema

The notification preferences are stored in the `notification_preferences` table:

```sql
CREATE TABLE notification_preferences (
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
```

## Error Handling

All notification methods return boolean success status:
- `True`: Notification sent successfully
- `False`: Notification failed (logged with details)

The unified service returns a dictionary with status for each channel:
```python
{
    'email': True,
    'whatsapp': False
}
```

## Logging

All notification activities are logged:
- Successful sends
- Failed sends with error details
- Preference updates
- Reminder scheduling

Check logs at: `logs/job_assistant.log`

## Testing

Run validation tests:
```bash
python tests/validate_notification_manager.py
```

Run usage examples:
```bash
python tests/example_notification_usage.py
```

## Requirements

### Email Notifications
- Python standard library (smtplib, email)
- Valid SMTP credentials

### WhatsApp Notifications
- `twilio` package: `pip install twilio`
- Twilio account with WhatsApp enabled

## Integration with Job Assistant

The notification manager integrates with:
1. **Job Search Agent**: Send daily digests of new jobs
2. **Job Tracker**: Send status update notifications
3. **Interview Prep Agent**: Send interview reminders
4. **Scheduler**: Automated daily digests and reminder checks

## Best Practices

1. **Use app-specific passwords** for email (not your main password)
2. **Test with sandbox** before using production WhatsApp numbers
3. **Respect user preferences** - always check before sending
4. **Rate limiting** - avoid sending too many notifications
5. **Error handling** - log failures but don't crash the application
6. **HTML emails** - ensure fallback for plain text clients
7. **Time zones** - consider user time zones for digest scheduling

## Troubleshooting

### Email not sending
- Check SMTP credentials
- Verify app-specific password (for Gmail)
- Check firewall/antivirus blocking port 587
- Enable "Less secure app access" if needed

### WhatsApp not sending
- Verify Twilio credentials
- Check account balance
- Ensure WhatsApp number format: `whatsapp:+[country][number]`
- Join Twilio sandbox if using test number

### Preferences not saving
- Ensure user exists in database
- Check foreign key constraints
- Verify database permissions

## Future Enhancements

- SMS notifications (via Twilio)
- Slack integration
- Discord webhooks
- Push notifications (mobile app)
- Notification templates customization
- A/B testing for notification content
- Delivery tracking and analytics
