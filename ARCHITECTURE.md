# DPAssist Architecture

## Overview

DPAssist is an AI-powered portfolio evaluation system designed to automate the assessment of student engineering and STEM portfolios while preserving teacher oversight and instructional decision-making.

The system consists of three major components:

1. Student Submission System (Google Forms + Google Sheets)
2. Background Evaluation Worker (Render)
3. Teacher Dashboard (Streamlit)

---

## System Architecture

```text
Student
   │
   ▼
Google Form Submission
   │
   ▼
Google Sheet
   │
   ▼
Render Background Worker
   │
   ├── Retrieve Rubric
   ├── Download Portfolio
   ├── Evaluate with Gemini
   ├── Generate Feedback
   ├── Send Email
   └── Update Submission Status
   │
   ▼
Google Sheet Results
   │
   ▼
Teacher Dashboard
```

---

## Component 1: Student Submission System

Students submit portfolio URLs through a Google Form.

The form records:

* Student name
* Student email
* Unit name
* Portfolio URL
* Submission timestamp

All submissions are stored automatically in Google Sheets, which serves as the central data store for the system.

---

## Component 2: Background Evaluation Worker

The Render-hosted background worker continuously monitors the Google Sheet for new submissions.

### Processing Cycle

Every 60 seconds the worker:

1. Checks for new submissions
2. Determines the correct rubric
3. Downloads and validates the portfolio
4. Sends portfolio content to Gemini
5. Generates evaluation feedback
6. Emails results to students
7. Updates submission status in Google Sheets

The worker operates independently from the teacher dashboard and continues processing even when no teacher is logged in.

---

## Component 3: Rubric Management

Rubrics are stored in a dedicated worksheet within the Google Sheet.

Each rubric contains:

* Unit name
* Due date
* Evaluation criteria
* Teacher comments
* Scoring requirements

This allows teachers to update rubrics without modifying source code.

---

## Component 4: AI Evaluation Engine

The evaluation engine uses Google's Gemini model to assess student portfolios.

The AI:

* Compares portfolio evidence against rubric requirements
* Identifies strengths
* Identifies missing artifacts
* Suggests improvements
* Generates teacher-facing comments
* Generates student-facing feedback

Teacher oversight remains central to the evaluation process.

---

## Component 5: Email Delivery System

After evaluation, the system automatically sends feedback emails to students.

Possible outcomes include:

### Successful Evaluation

The student receives:

* Portfolio feedback
* Strengths identified
* Missing requirements
* Suggested improvements

### Portfolio Access Problem

If the portfolio cannot be accessed:

* The student receives instructions to correct permissions
* The submission is flagged for review

### Teacher Draft Creation

When configured, the system can generate teacher-facing draft comments for manual review before release.

---

## Component 6: Teacher Dashboard

The Streamlit dashboard provides visibility into system activity.

### Rubrics Page

Teachers can:

* Create rubrics
* Edit rubrics
* View due dates

### Submissions Page

Teachers can:

* View recent submissions
* Monitor processing status
* Review submission history

### System Status Page

Teachers can verify:

* Google Sheets connectivity
* Gemini API availability
* Gmail configuration
* Background worker operation

---

## Data Storage

DPAssist uses Google Sheets as the primary data store.

Stored data includes:

* Student submissions
* Rubrics
* Processing status
* Evaluation results

No database server is required.

---

## Cloud Deployment

### Streamlit Cloud

Hosts:

* Teacher Dashboard

### Render

Hosts:

* Background evaluation worker

### Google Services

Provide:

* Forms
* Sheets
* Authentication
* Email delivery

### Gemini API

Provides:

* Portfolio evaluation
* Feedback generation
* Teacher comment generation

---

## Design Goals

The system was designed to:

* Reduce teacher grading workload
* Provide timely student feedback
* Preserve teacher oversight
* Scale to multiple classes
* Require minimal technical setup
* Operate using low-cost cloud infrastructure

---

## Current Production Status

Production deployment includes:

* Streamlit Cloud teacher dashboard
* Render-hosted background worker
* Google Sheets rubric storage
* Automated email delivery
* Gemini-powered portfolio evaluation

Verified capabilities include:

* Automated submission detection
* Rubric retrieval
* Portfolio evaluation
* Student feedback delivery
* Teacher draft generation
* Cloud-hosted dashboard
* Render-based background processing
* Processing of real student submissions

```
```
