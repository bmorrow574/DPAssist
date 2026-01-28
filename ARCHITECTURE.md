# PortfoliOS Multi-Agent Architecture

## System Overview

PortfoliOS is redesigned as a **continuous background service** with **6 specialized AI agents** working together to provide automated portfolio feedback.

## Agent Architecture

### 1. Submission Monitor Agent (`agent_submission_monitor.py`)
- **Purpose**: Continuously watches Google Sheet for new submissions
- **Triggers**: Runs every 5 minutes (configurable)
- **Actions**: 
  - Detects new or updated portfolio submissions
  - Adds submissions to processing queue
  - Marks submission timestamp

### 2. Timeliness Agent (`agent_timeliness.py`)
- **Purpose**: Checks if submissions are on time
- **Inputs**: Submission timestamp, deadline from config
- **Outputs**: 
  - `is_late: True/False`
  - `late_by: duration` (if late)
- **Updates**: Sheet column "Timeliness Status"

### 3. Link Validation Agent (`agent_link_validator.py`)
- **Purpose**: Validates portfolio links are accessible
- **Checks**:
  - URL is valid and reachable
  - No 404 errors
  - No Google permission walls
  - Proper sharing settings for Google Sites
- **Outputs**: 
  - `link_status: "Valid" | "Broken" | "Permission Denied"`
  - Error messages for students
- **Actions**: If link invalid, emails student immediately

### 4. Media Accessibility Agent (`agent_media_checker.py`)
- **Purpose**: Ensures all media on page is accessible
- **Process**:
  - Takes screenshot of portfolio page
  - Uses Selenium to find all images/videos
  - Checks each media element loads properly
  - Detects broken embeds, missing images
- **Outputs**:
  - List of broken media URLs
  - Count of accessible vs. broken media
- **Actions**: If media issues found, emails student with specifics

### 5. Caption Analysis Agent (`agent_caption_analyzer.py`)
- **Purpose**: Analyzes quality and relevance of media captions
- **Uses**: Gemini Vision API
- **Process**:
  - Sends screenshot + portfolio description to Gemini
  - AI evaluates:
    - Are captions present on all media?
    - Are captions descriptive and thorough?
    - Are media relevant to portfolio content?
- **Outputs**:
  - Caption quality score
  - List of media missing/poor captions
  - Relevance assessment
- **Actions**: If issues found, emails student with improvement suggestions

### 6. Feedback Generator Agent (`agent_feedback_generator.py`)
- **Purpose**: Creates personalized feedback
- **Two Modes**:
  
  **Before Deadline (Student Mode)**:
  - Generates constructive feedback
  - Sends directly to student
  - Allows multiple resubmissions
  - Updates on each new submission
  
  **After Deadline (Teacher Mode)**:
  - Compiles comprehensive feedback
  - Reads teacher-uploaded rubric
  - Incorporates all agent findings
  - Creates email DRAFT (not sent)
  - Saves to teacher's email drafts folder

### 7. Email Draft Agent (`agent_email_drafter.py`)
- **Purpose**: Manages email composition and sending
- **Supports**: Gmail, Outlook, Generic SMTP
- **Functions**:
  - Send immediate feedback to students
  - Create drafts for teacher review
  - Track sent emails
  - Sync sent emails back to sheet

## Data Flow

```
New Submission
    ↓
[Submission Monitor] → Adds to queue
    ↓
[Timeliness Agent] → Checks deadline
    ↓
[Link Validator] → Validates URL
    ↓  (if valid)
[Media Checker] → Tests all media
    ↓  (if accessible)
[Caption Analyzer] → AI reviews captions
    ↓
[Feedback Generator] → Creates feedback
    ↓
BEFORE deadline: [Email Draft Agent] → Sends to STUDENT
AFTER deadline: [Email Draft Agent] → Creates DRAFT for TEACHER
    ↓
Updates Google Sheet with results
```

## Background Processing

The system runs as a **daemon/service** that:
- Monitors submissions every 5 minutes
- Processes one submission at a time (queue-based)
- Handles errors gracefully
- Logs all activities
- Can be stopped/started easily

## Key Improvements Over Original

1. **Automatic vs Manual**: Runs continuously, not on button click
2. **Modular Design**: Each agent is independent and testable
3. **Student Self-Service**: Students get immediate feedback before deadline
4. **Multiple Submissions**: Students can resubmit; system processes each time
5. **Platform Agnostic**: Works with Gmail, Outlook, any SMTP server
6. **Better Error Handling**: Each agent handles its own errors
7. **Scalable**: Can process multiple students simultaneously (future enhancement)

## Configuration

All settings in `config.yaml`:
- API keys (Gemini, email credentials)
- Google Sheet details
- Deadline date/time
- Email templates
- Agent settings (timing, retries, etc.)

## Deployment Options

1. **Local Computer**: Run on teacher's laptop (simple setup)
2. **Cloud VM**: Run on Google Cloud, AWS, etc. (always on)
3. **Docker Container**: Portable, easy deployment (intermediate)
4. **Serverless**: Google Cloud Run, AWS Lambda (advanced)

For non-technical teachers, **Option 1 (Local)** is recommended with detailed setup guide.
