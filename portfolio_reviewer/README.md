# Portfolio Reviewer

Automated portfolio evaluation system using Google Gemini AI with strict grading rules.

## Overview

This system automatically:
- Reads student portfolio submissions from Google Forms/Sheets
- Scrapes portfolio content from Google Sites and GitHub Pages
- Evaluates portfolios against uploaded rubrics using AI
- Sends feedback (no scores) before due dates
- Creates scored draft emails in Gmail after due dates
- Runs automatically every 60 seconds

## Features

### For Teachers
- **Upload Rubrics**: PDF rubrics are automatically parsed
- **Set Due Dates**: Associate each rubric with a due date
- **Monitor Submissions**: Web dashboard shows all submissions and their status
- **Automatic Grading**: AI evaluates portfolios with strict evidence-based rules
- **Draft Emails**: Scored feedback appears as Gmail drafts after deadline

### For Students
- **Continuous Feedback**: Get feedback on portfolios as you update them
- **Evidence-Based**: All feedback cites specific evidence from your portfolio
- **Clear Guidance**: Detailed "what to add" lists help improve work

## Technology Stack

- **Backend**: Python 3.9+
- **AI**: Google Gemini 1.5 Pro
- **Web Scraping**: BeautifulSoup4, Requests
- **Google APIs**: Sheets API, Gmail API
- **UI**: Streamlit (teacher dashboard)
- **Launcher**: Tkinter (cross-platform GUI)

## Key Components

### 1. Background Service (`background_service.py`)
- Runs every 60 seconds
- Checks Google Sheets for new submissions
- Scrapes portfolio content
- Evaluates with AI
- Sends feedback or creates drafts

### 2. Teacher Dashboard (`teacher_ui.py`)
- Streamlit web interface
- Upload and manage rubrics
- Set due dates
- Monitor submission status

### 3. GUI Launcher (`launcher.py`)
- Cross-platform (Mac/Windows)
- One-click start/stop
- Log viewing
- No terminal knowledge required

### 4. Strict AI Evaluation (`evaluator.py`)
- Evidence-based grading
- No hallucinations allowed
- Objective feedback only
- Validates against rubric

## Project Structure

```
PortfolioReviewer/
├── launcher.py              # GUI launcher
├── background_service.py    # Main processing loop
├── teacher_ui.py           # Streamlit dashboard
├── config.py               # Configuration management
├── google_sheets.py        # Google Sheets integration
├── scraper.py              # Portfolio content scraping
├── evaluator.py            # AI evaluation with strict rules
├── gmail_drafts.py         # Gmail draft creation
├── rubric_manager.py       # Rubric storage and due dates
├── rubric_parser.py        # PDF rubric parsing
├── schemas/                # Data schemas
│   ├── artifact.py
│   ├── output.py
│   ├── rubric.py
│   └── run.py
├── orchestrator/           # Validation and pipeline
│   ├── pipeline.py
│   ├── service.py
│   ├── storage.py
│   └── validators.py
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── SETUP_GUIDE.md        # Complete setup instructions
└── README.md             # This file
```

## Security

- Service account credentials for Google APIs
- API keys stored in `.env` file (not committed to Git)
- All sensitive files protected by `.gitignore`

## Architecture

### Data Flow

1. **Student submits** → Google Form → Google Sheets
2. **Background service checks** every 60s for new rows
3. **Scraper extracts** portfolio content from URL
4. **AI evaluates** content against rubric criteria
5. **Validator ensures** strict evidence rules are followed
6. **Output created**:
   - Before deadline: Send feedback (no scores)
   - After deadline: Create Gmail draft (with scores)
7. **Sheet updated** with processing status

### Validation Rules (Strict Mode)

From `agent.py` requirements:

1. **Evidence Requirements**:
   - MEETS/PARTIALLY_MEETS must have evidence quotes
   - NOT_YET must have zero evidence
   - Evidence must be exact quotes (10-50 words)
   - Each quote must reference location

2. **Confidence Rules**:
   - MEETS + LOW confidence is forbidden
   - HIGH only when evidence is complete
   - MEDIUM when evidence is present but brief
   - LOW only for PARTIALLY_MEETS or NOT_YET

3. **Objectivity**:
   - No encouraging language
   - No subjective opinions
   - No assumptions beyond visible evidence
   - Professional tone only

4. **Completeness**:
   - All rubric criteria must be evaluated
   - Each criterion exactly once
   - Each criterion must have feedback

## Setup

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete installation and configuration instructions.

Quick start:
1. Install Python 3.9+
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Google service account credentials
4. Configure `.env` file
5. Run launcher: `python launcher.py`

## Usage

### Starting the System

**Mac:**
```bash
python3 launcher.py
```

**Windows:**
```
python launcher.py
```

### Teacher Workflow

1. Open launcher
2. Click "Start Background Service"
3. Click "Open Teacher Dashboard"
4. Upload rubrics and set due dates
5. Monitor submissions
6. Review Gmail drafts after deadlines

### Student Workflow

1. Complete digital portfolio (Google Sites or GitHub Pages)
2. Submit URL via Google Form
3. Receive automated feedback
4. Update portfolio
5. After deadline: Teacher reviews scored draft and sends

## License

Proprietary - Educational use only

## Support

See SETUP_GUIDE.md for troubleshooting and common issues.
