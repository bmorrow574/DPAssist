# DPAssist — Cloud Deployment Guide

## Overview

DPAssist is designed so that teachers can use the system entirely from a web browser without installing Python or running any local services.

Production deployment consists of:

| Component         | Platform                         | Purpose                                                   |
| ----------------- | -------------------------------- | --------------------------------------------------------- |
| Teacher Dashboard | Streamlit Cloud                  | Rubric management, submission monitoring, system status   |
| Background Worker | Render Starter Worker ($7/month) | Portfolio evaluation, feedback generation, email delivery |
| Data Storage      | Google Sheets                    | Submission records and rubric storage                     |
| AI Engine         | Gemini API                       | Portfolio evaluation and feedback generation              |

---

## Prerequisites

Before deployment, gather the following:

* GitHub repository
* Google Service Account credentials JSON
* Google Sheet ID
* Gemini API key
* Gmail App Password
* Teacher email address

---

# Step 1 — Deploy the Teacher Dashboard

## Create a Streamlit Cloud Account

1. Visit https://share.streamlit.io
2. Sign in with GitHub

---

## Deploy the Dashboard

Create a new application using:

| Setting        | Value                            |
| -------------- | -------------------------------- |
| Repository     | bmorrow574/DPAssist              |
| Branch         | main                             |
| Main file path | portfolio_reviewer/teacher_ui.py |

---

## Configure Secrets

Open **Advanced Settings → Secrets**.

Paste the contents of:

```toml
.streamlit/secrets.toml.example
```

using your production values.

Required values include:

```toml
GOOGLE_SHEET_ID
GOOGLE_CREDENTIALS_JSON
GEMINI_API_KEY
TEACHER_EMAIL
GMAIL_APP_PASSWORD
```

Deploy the application.

The dashboard will be available at a URL similar to:

```text
https://your-app-name.streamlit.app
```

---

# Step 2 — Deploy the Background Worker

DPAssist uses a Render Starter Worker.

Current cost:

```text
$7/month
```

The worker runs continuously and processes student submissions automatically.

---

## Create a Render Account

1. Visit https://render.com
2. Sign in with GitHub

---

## Deploy from Blueprint

1. Select:

```text
New → Blueprint
```

2. Connect the GitHub repository.

3. Render automatically detects:

```text
render.yaml
```

4. Create a Blueprint instance.

---

## Configure Environment Variables

Provide the following values:

| Variable                | Description                                         |
| ----------------------- | --------------------------------------------------- |
| GOOGLE_CREDENTIALS_JSON | Entire contents of service-account-credentials.json |
| GOOGLE_SHEET_ID         | Google Sheet ID                                     |
| GEMINI_API_KEY          | Gemini API key                                      |
| TEACHER_EMAIL           | Teacher email address                               |
| GMAIL_APP_PASSWORD      | Gmail App Password                                  |

The following values are already defined in `render.yaml`:

```text
RUBRIC_STORAGE=sheets
CHECK_INTERVAL_SECONDS=60
```

---

## Deploy

Click Deploy.

Render will:

1. Build the Python environment
2. Install dependencies
3. Start the worker
4. Begin monitoring submissions every 60 seconds

Successful startup should show:

```text
Your service is live
Running 'python portfolio_reviewer/background_service.py'
```

in the Render logs.

---

# Rubric Storage

DPAssist stores rubrics directly in Google Sheets.

When the first rubric is uploaded:

```text
DPAssist_Rubrics
```

is automatically created as a new worksheet.

Benefits:

* No local files required
* Shared between dashboard and worker
* Cloud-backed persistence
* Accessible from anywhere

---

# Data Flow

```text
Student
   │
   ▼
Google Form
   │
   ▼
Google Sheet
   │
   ▼
Render Worker
   │
   ├─ Portfolio Download
   ├─ Rubric Retrieval
   ├─ Gemini Evaluation
   ├─ Feedback Generation
   ├─ Email Delivery
   └─ Status Update
   │
   ▼
Teacher Dashboard
```

---

# Security

Never commit:

```text
.env
service-account-credentials.json
```

to GitHub.

Store all credentials in:

* Streamlit Secrets
* Render Environment Variables

The Google credentials should be pasted as the complete JSON document.

---

# Updating Production

Deployment updates are simple:

```bash
git add .
git commit -m "Update production"
git push
```

Both services automatically redeploy.

---

# Verified Production Deployment

The production deployment has been verified using real student submissions.

Verified functionality includes:

* Submission detection
* Rubric retrieval
* Portfolio evaluation
* Gemini feedback generation
* Email delivery
* Google Sheets integration
* Streamlit dashboard updates
* Render background processing

No local worker is required once deployment is complete.
