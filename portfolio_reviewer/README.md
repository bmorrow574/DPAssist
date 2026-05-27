# DPAssist
### AI-Powered Portfolio Evaluation for Teachers

> **Built for educators who shouldn't have to choose between giving great feedback and having time to teach.**

## 📺 Demo Video

[![Watch DPAssist in action](https://img.youtube.com/vi/u0C-5i633i0/0.jpg)](https://youtu.be/u0C-5i633i0?si=MShwbzpioF1n3N7k)

## 🚀 Try It Live &nbsp;&nbsp;|&nbsp;&nbsp; 📖 [Teacher Setup Guide](https://bmorrow574.github.io/DPAssist/portfolio_reviewer/DPAssist_Teacher_Setup.html)

👉 **[dpassist-edu.streamlit.app](https://dpassist-edu.streamlit.app)** — opens in any browser, no installation required
### AI-Powered Portfolio Evaluation for Teachers

> **Built for educators who shouldn't have to choose between giving great feedback and having time to teach.**

---

## The Problem

Digital portfolio assignments are among the most valuable — and most time-consuming — assignments a teacher can give. A single class of 25 students, each submitting a multi-page portfolio, can easily require 10–15 hours of reading, grading, and writing individual feedback. Teachers who want to give students the chance to revise and improve before a deadline face an impossible tradeoff: either spend weekends grading drafts, or give no feedback at all.

DPAssist solves this by automating the feedback loop entirely — while keeping the teacher in control of every final grade.

---

## What It Does

DPAssist is a background service that runs on a teacher's computer (or in the cloud). From the moment a student submits a portfolio link via Google Forms, the system takes over:

1. **Detects the new submission** from Google Sheets (updated automatically by Google Forms)
2. **Scrapes the portfolio** — works with Google Sites, GitHub Pages, and GitHub repositories
3. **Evaluates it against the teacher's rubric** using Google Gemini AI, with strict evidence-based rules
4. **Emails the student feedback** before the deadline — specific, actionable, and tied to exact quotes from their work
5. **Creates a scored Gmail draft** for the teacher after the deadline — ready to review, edit, and send

The teacher uploads a rubric PDF once. After that, everything runs automatically.

---

## Key Design Decisions

### Evidence-First AI Evaluation

Most AI grading tools produce vague, encouraging language that doesn't actually help students improve. DPAssist enforces strict evaluation rules at the prompt level:

- A criterion rated **Meets** must include an exact quote (10–50 words) from the student's portfolio as evidence
- A criterion rated **Not Yet** must have **zero** evidence quotes — the AI cannot make something up
- **MEETS + low confidence is forbidden** — the model must be sure before awarding credit
- No encouraging language, no assumptions, no hallucinations

This is not just a prompt instruction — the output is validated against a structured schema before any email is sent. If the validation fails, the submission is flagged rather than silently producing bad feedback.

### Two-Phase Feedback Model

| Phase | Timing | Recipient | Contains |
|-------|--------|-----------|----------|
| Student feedback | Before deadline | Student | Criterion-by-criterion feedback, evidence quotes, specific "what to add" lists — **no scores** |
| Teacher draft | After deadline | Teacher's Gmail Drafts | Full scores, rubric breakdown, AI-drafted teacher comment — **awaiting teacher review** |

Withholding scores before the deadline encourages students to engage with the feedback rather than fixate on a number. After the deadline, the teacher receives a complete draft that takes 2 minutes to review instead of 30.

### Rubric Parsing

Teachers upload their existing PDF rubrics — no reformatting required. The parser uses Gemini AI to extract criteria, point values, and performance level descriptors from any rubric layout. A regex fallback handles cases where the AI is unavailable.

### School Network Compatibility

Many school Google Workspace accounts disable IMAP access. The Gmail integration automatically falls back from IMAP draft creation to sending a direct review email to the teacher, so the system never silently fails.

---

## Architecture

```
Student submits Google Form
        │
        ▼
┌─────────────────────┐
│   Google Sheets     │  ◄── Populated automatically by Google Forms
└────────┬────────────┘
         │  (polled every 60s)
         ▼
┌─────────────────────┐
│  Background Service │  background_service.py
│  (processing loop)  │
└────────┬────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐ ┌──────────┐
│Scraper │ │  Rubric  │
│        │ │ Manager  │
└───┬────┘ └────┬─────┘
    │           │
    └─────┬─────┘
          ▼
┌─────────────────────┐
│  Gemini Evaluator   │  Strict evidence-based grading
│  + Validator        │  Schema validation before output
└────────┬────────────┘
         │
    ┌────┴──────────┐
    │               │
    ▼               ▼
Before deadline: After deadline:
Email to student  Draft in teacher's Gmail
```

### Components

| File | Role |
|------|------|
| `background_service.py` | Main processing loop — runs every 60 seconds |
| `teacher_ui.py` | Streamlit dashboard — rubric upload, submission monitoring |
| `evaluator.py` | Gemini AI evaluation with strict validation rules |
| `rubric_parser.py` | PDF → structured rubric using Gemini + regex fallback |
| `rubric_manager.py` | Rubric storage (local files or Google Sheets tab) |
| `scraper.py` | Portfolio content extraction (Google Sites, GitHub Pages, GitHub repos) |
| `gmail_drafts.py` | Gmail draft creation via IMAP, with SMTP fallback |
| `email_service.py` | Student feedback emails via Gmail SMTP |
| `google_sheets.py` | Google Sheets read/write for submissions and status |
| `config.py` | Unified config from `.env` (local) or Streamlit secrets (cloud) |
| `launcher.py` | Tkinter GUI — one-click start/stop, no terminal required |
| `orchestrator/` | Pipeline assembly and schema validation |
| `schemas/` | Pydantic-style data models for rubrics, artifacts, and outputs |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| AI Evaluation | Google Gemini 2.5 Pro / 1.5 Pro (with automatic fallback) |
| Web Scraping | BeautifulSoup4, Requests, GitHub REST API |
| Google Integration | gspread, Gmail IMAP/SMTP, Google Sheets API v4 |
| Teacher Dashboard | Streamlit |
| Desktop Launcher | Tkinter (cross-platform, no install required) |
| Runtime | Python 3.9+ |

---

## Deployment Options

**Local (recommended for non-technical teachers)**
Run on the teacher's laptop. The Tkinter launcher provides a one-click interface — no terminal knowledge required. A LaunchAgent (Mac) or Task Scheduler entry (Windows) can keep the service running automatically.

**Cloud**
The system supports Streamlit Cloud for the teacher dashboard and a separate cloud service (Railway, Render, etc.) for the background worker. Rubric storage switches automatically to Google Sheets when `RUBRIC_STORAGE=sheets` is set, removing the need for a shared filesystem.

---

## Setup

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete step-by-step instructions written for non-technical users.

**Requirements:**
- Python 3.9+
- A Google account (Gmail + Google Sheets)
- A Google Cloud service account (for Sheets/Gmail API access)
- A Google Gemini API key (free tier is sufficient for most classrooms)

**Quick start (for developers):**
```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your credentials
python launcher.py          # opens the GUI
```

---

## Real-World Usage

This system has been tested with actual student portfolio submissions at Charlotte Latin School. The `processing_state.json` tracks which submissions have been processed to avoid duplicate emails across service restarts.

Sample units processed: *Milling About*, *Data Movement and Types of Networks*

---

## Evaluation Rules (Technical Detail)

The AI evaluation enforces the following constraints at inference time, validated post-generation:

```
MEETS / PARTIALLY_MEETS  →  must have ≥1 evidence quote (10–50 words, exact)
NOT_YET                  →  must have zero evidence quotes
MEETS + LOW confidence   →  forbidden (rejected by validator)
HIGH confidence          →  only when evidence is complete
```

All rubric criteria must be evaluated exactly once. Missing criteria cause the run to fail validation rather than producing incomplete output.

---

## License

Proprietary — Educational use only.

---

*DPAssist — because teachers' time is better spent teaching.*

