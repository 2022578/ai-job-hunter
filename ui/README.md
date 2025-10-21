# GenAI Job Assistant - UI Documentation

## Overview

The UI is built using Streamlit and provides an intuitive interface for managing your job search, applications, and interview preparation.

## Structure

```
ui/
├── __init__.py
├── pages/
│   ├── __init__.py
│   └── dashboard.py      # Dashboard with metrics and insights
└── README.md
```

## Main Application (app.py)

The main entry point for the Streamlit application with the following features:

### Key Components

1. **Page Configuration**
   - Loads settings from `config/config.yaml`
   - Configures page title, icon, and layout
   - Sets up wide layout for better data visualization

2. **Session State Management**
   - Manages user session data
   - Initializes database connections
   - Stores current page navigation state

3. **Navigation Sidebar**
   - Quick navigation between pages
   - Quick stats display (jobs, applications, interviews)
   - Clean, icon-based menu

4. **Page Routing**
   - Routes to appropriate page based on user selection
   - Currently implemented: Dashboard
   - Coming soon: Job Search, Applications, Interview Prep, Settings

## Dashboard Page

The dashboard provides a comprehensive overview of your job search progress.

### Features

#### 1. Overview Metrics
- **Total Jobs Found**: All jobs discovered by the system
- **Applications Submitted**: Total number of applications
- **Interviews Scheduled**: Upcoming interview count
- **Average Match Score**: Average relevance score across all jobs

#### 2. Application Funnel
- Visual representation of application stages
- Shows progression from Saved → Applied → Interview → Offered
- Displays interview rate and offer rate percentages

#### 3. Match Score Distribution
- Bar chart showing distribution of job match scores
- Buckets: 90-100, 80-89, 70-79, 60-69, Below 60
- Helps identify high-quality opportunities

#### 4. Application Timeline
- Line chart showing application activity over time
- Tracks daily application submissions
- Visualizes job search momentum

#### 5. Top Companies
- Table of companies with most job listings
- Shows top 10 companies by job count
- Helps identify active hirers

#### 6. Upcoming Interviews
- List of scheduled interviews
- Shows job title, company, date/time
- Color-coded urgency indicators:
  - 🔴 Today
  - 🟡 Tomorrow
  - 🟢 In X days

#### 7. Actionable Insights
- Smart recommendations based on your data:
  - High-scoring unapplied jobs
  - Upcoming interviews requiring preparation
  - Stale applications needing follow-up
  - New jobs discovered this week

#### 8. Quick Actions
- **Search Jobs**: Navigate to job search page
- **Optimize Resume**: Access resume optimizer
- **Prepare Interview**: Go to interview prep page

## Running the Application

### Prerequisites

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Start the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Configuration

Edit `config/config.yaml` to customize:
- UI theme (light/dark)
- Page title and icon
- Layout preferences

## Navigation

Use the sidebar to navigate between pages:
- 📊 Dashboard - Overview and insights
- 🔍 Job Search - Find and filter jobs
- 📝 Applications - Track application status
- 💼 Interview Prep - Prepare for interviews
- ⚙️ Settings - Configure preferences

## Data Flow

1. **Database Connection**: Initialized in session state
2. **Data Fetching**: Repositories fetch data from SQLite
3. **Data Processing**: Dashboard aggregates and analyzes data
4. **Visualization**: Streamlit renders charts and metrics
5. **User Actions**: Button clicks trigger page navigation or actions

## Error Handling

- All database operations wrapped in try-catch blocks
- User-friendly error messages displayed
- Detailed errors logged for debugging
- Graceful degradation when data unavailable

## Future Enhancements

### Planned Pages

1. **Job Search Page**
   - Manual job search with filters
   - Job listing cards with match scores
   - Quick apply actions

2. **Applications Page**
   - Application management table
   - Status updates
   - HR contact management
   - Export functionality

3. **Interview Prep Page**
   - Question generation
   - Mock interview mode
   - Custom Q&A library

4. **Settings Page**
   - User profile management
   - Notification preferences
   - Credential management
   - Search criteria configuration

### Planned Features

- Real-time notifications
- Dark mode toggle
- Export dashboard as PDF
- Advanced filtering and search
- Customizable dashboard widgets
- Mobile-responsive design

## Development

### Adding a New Page

1. Create a new file in `ui/pages/`:
```python
# ui/pages/my_page.py
import streamlit as st

def render_my_page():
    st.title("My Page")
    # Your page content here
```

2. Add navigation in `app.py`:
```python
# In render_sidebar()
pages = {
    "Dashboard": "📊",
    "My Page": "🎯",  # Add your page
    # ...
}

# In route_to_page()
elif current_page == "My Page":
    from ui.pages.my_page import render_my_page
    render_my_page()
```

### Testing

Run the validation script to check structure:
```bash
python tests/validate_ui_structure.py
```

## Troubleshooting

### Database Not Found
- Ensure database is initialized: `python scripts/init_app.py`
- Check database path in `config/config.yaml`

### Import Errors
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python path includes project root

### Streamlit Not Starting
- Check if port 8501 is available
- Try alternative port: `streamlit run app.py --server.port 8502`

### Data Not Displaying
- Verify database has data
- Check logs in `logs/job_assistant.log`
- Ensure user_id in session state matches database records

## Best Practices

1. **Session State**: Always check if variables exist before accessing
2. **Error Handling**: Wrap database operations in try-catch
3. **Performance**: Use `@st.cache_data` for expensive operations
4. **UX**: Show loading spinners for long operations
5. **Logging**: Log errors for debugging without exposing to users

## Support

For issues or questions:
1. Check logs in `logs/job_assistant.log`
2. Review configuration in `config/config.yaml`
3. Validate database with `python tests/validate_ui_structure.py`
