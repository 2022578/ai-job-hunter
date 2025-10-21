# Resume Optimizer Page

## Overview

The Resume Optimizer page provides AI-powered resume analysis and optimization for GenAI/LLM roles. It helps users improve their resumes by identifying missing keywords, suggesting improvements, and providing targeted optimization for specific job postings.

## Features

### 1. Resume Input
- **File Upload**: Support for PDF, DOCX, and TXT formats
- **Manual Text Input**: Text area for pasting resume content directly
- Automatic text extraction from uploaded files

### 2. Job Selection
- Optional dropdown to select a target job for optimization
- Displays job details (company, location, salary, skills)
- Enables targeted optimization based on job requirements

### 3. Analysis Modes

#### General Analysis
- Overall resume strength score (0-10)
- Present keywords identification
- Missing critical keywords
- Keyword density score
- Strengths and weaknesses
- General recommendations

#### Targeted Optimization (with job selection)
- All general analysis features
- ATS keywords specific to the job
- Before/after improvement suggestions
- GenAI experience highlights
- Section-specific rewrites

### 4. Results Display

#### Analysis Results
- **Overall Score**: Visual score display with color coding
- **Keyword Analysis**: 
  - Present keywords (what's already in resume)
  - Missing keywords (what should be added)
  - Keyword density score with progress bar
- **Strengths**: Positive aspects of the resume
- **Areas for Improvement**: Weaknesses to address
- **Recommendations**: Actionable suggestions

#### Optimization Results
- **ATS Keywords**: Critical keywords to include for applicant tracking systems
- **GenAI Highlights**: Suggestions for emphasizing GenAI/LLM experience
- **Improvement Suggestions**: 
  - Section name
  - Before/after comparison
  - Reason for the change
  - Copy button for optimized text

## Usage Flow

1. **Upload or Paste Resume**
   - Upload a file (PDF, DOCX, TXT) or paste text directly
   - Resume content is stored in session state

2. **Select Target Job (Optional)**
   - Choose a job from the dropdown for targeted optimization
   - View job details to confirm selection

3. **Analyze or Optimize**
   - Click "Analyze Resume" for general analysis
   - Click "Optimize for Job" for targeted optimization (requires job selection)

4. **Review Results**
   - Check overall score and keyword analysis
   - Review strengths and weaknesses
   - Read improvement suggestions
   - Copy optimized text sections

5. **Apply Improvements**
   - Use the before/after comparisons to update resume
   - Copy optimized sections using copy buttons
   - Re-analyze to see improvements

## Technical Implementation

### Components

#### `initialize_session_state()`
Initializes session state variables:
- `resume_text`: Current resume content
- `selected_job_for_optimization`: Selected job for optimization
- `optimization_result`: Optimization results
- `analysis_result`: Analysis results

#### `read_resume_file(uploaded_file)`
Reads resume content from uploaded files:
- Supports TXT, PDF (via PyPDF2), and DOCX (via python-docx)
- Returns extracted text or None on failure

#### `render_resume_input()`
Renders resume input section:
- File uploader component
- Text area for manual input
- Updates session state with resume content

#### `render_job_selection(job_repo)`
Renders job selection dropdown:
- Fetches all jobs from database
- Displays job options with company names
- Shows job details in expander

#### `render_analysis_button(optimizer)`
Renders analysis/optimization buttons:
- "Analyze Resume" button for general analysis
- "Optimize for Job" button for targeted optimization
- Handles button clicks and triggers analysis

#### `render_analysis_results(analysis)`
Displays analysis results:
- Overall score with color coding
- Keyword analysis (present/missing)
- Strengths and weaknesses
- Recommendations

#### `render_optimization_results(optimized)`
Displays optimization results:
- ATS keywords
- GenAI highlights
- Before/after improvements with copy buttons

### Dependencies

- `streamlit`: UI framework
- `agents.resume_optimizer`: Resume analysis and optimization logic
- `utils.llm_client`: LLM integration for AI-powered analysis
- `database.repositories.job_repository`: Job data access
- `PyPDF2`: PDF file reading (optional)
- `python-docx`: DOCX file reading (optional)

### Error Handling

- File reading errors are caught and displayed to user
- LLM failures return empty results with error messages
- Database errors are logged and displayed
- Missing dependencies (PyPDF2, python-docx) show installation instructions

## Requirements Coverage

This implementation covers the following requirements:

- **2.1**: Resume analysis using open-source LLM ✅
- **2.2**: ATS keyword identification ✅
- **2.3**: Targeted optimization for specific jobs ✅
- **2.4**: Improvement recommendations with emphasis on GenAI experience ✅
- **2.5**: Before/after comparisons in Streamlit interface ✅

## Future Enhancements

1. **Resume Version History**: View and compare previous resume versions
2. **Export Optimized Resume**: Download optimized resume as PDF/DOCX
3. **Batch Optimization**: Optimize for multiple jobs at once
4. **Custom Keyword Lists**: Add custom keywords to target
5. **Resume Templates**: Apply professional templates to optimized content
6. **A/B Testing**: Compare different resume versions
7. **Industry-Specific Analysis**: Tailor analysis for different industries

## Notes

- LLM must be running (Ollama) for analysis to work
- File upload requires PyPDF2 for PDF and python-docx for DOCX support
- Resume versions are automatically stored in database when optimizing for a job
- Analysis results are cached in session state for quick access
- Copy buttons provide easy way to extract optimized text

