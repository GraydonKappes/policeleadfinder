# Crash Report Analysis UI

*A Streamlit interface for analyzing and managing crash reports*

## Overview

This is the frontend application that makes PDF analysis accessible to users. The interface is designed to be user-friendly and efficient.

## Directory Structure

```
client_ui/
├── pages/                # Additional UI pages
│   ├── case_management.py   # For managing cases
│   └── view_reports.py      # For viewing reports
├── app.py               # Main Streamlit application
├── database.py         # Database models
└── db_operations.py    # Database operations
```

## Prerequisites

Before running this UI, make sure you have:
- Python 3.11+ installed
- PostgreSQL database set up
- PDF Analyzer Service running
- Proper environment variables set

## Configuration

Create a `.env` file with:
```env
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
PDF_ANALYZER_URL=http://localhost:8000
```

## Running the Application

```bash
streamlit run app.py
```

The UI will be available at `http://localhost:8501`

## Features

### PDF Analysis
- Upload single or multiple PDFs
- Get AI-powered analysis
- View structured results

### Case Management
- Create cases from analysis results
- Track case status
- Add notes and updates

### Report Viewing
- Browse all analyzed reports
- Filter by date and vehicle year
- Export results as JSON

## Important Note

This UI is the frontend interface for the system. The PDF analyzer service must be running for the interface to function properly. Keep the UI clean and organized for the best user experience.

## Troubleshooting

If the UI isn't working:

1. Check if the PDF analyzer service is running
2. Verify database connection
3. Look for error messages in the Streamlit output
4. Make sure your environment variables are set

If issues persist, consult the documentation or contact support.

---
A+ Collision App - PDF Analysis Interface 