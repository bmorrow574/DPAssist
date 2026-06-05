# DPAssist – Teacher Setup Guide

## Overview

This guide walks teachers through the one-time setup required to use DPAssist.

Once setup is complete, DPAssist automatically:

* Monitors student submissions
* Evaluates portfolios using AI
* Sends feedback to students
* Tracks submission status
* Stores rubrics in the cloud

Most teachers complete setup in approximately 15–20 minutes.

---

# What You Need Before Starting

You will need:

* A Google account
* A Gmail account
* A Google Form for portfolio submissions
* The Google Sheet connected to that form
* Rubrics saved as PDF files
* Access to the DPAssist Teacher Dashboard

---

# Step 1 — Open the Teacher Dashboard

Open the DPAssist dashboard in your web browser.

Example:

```text
https://your-school-dpassist.streamlit.app
```

No software installation is required.

---

# Step 2 — Verify System Status

Open **System Status**.

You should see green check marks for:

* Google Sheets
* Gemini API
* Gmail
* Credentials

If all four are green, the system is ready.

---

# Step 3 — Upload Your First Rubric

Select **Rubrics** from the navigation menu.

For each assignment:

1. Upload the rubric PDF
2. Enter the Unit Name
3. Set the Due Date
4. Click **Parse and Add Rubric**

DPAssist automatically stores the rubric in Google Sheets.

---

# Step 4 — Verify the Unit Name

The Unit Name must exactly match the Unit Name used in the student submission form.

Correct:

```text
Milling About
```

Incorrect:

```text
milling about
MillingAbout
Milling About!
```

Exact matching ensures the correct rubric is used.

---

# Step 5 — Students Submit Portfolios

Students submit:

* Name
* Email
* Unit Name
* Portfolio URL

through the Google Form.

Submissions automatically appear in Google Sheets.

---

# Step 6 — Automatic Evaluation

Every 60 seconds the background worker:

1. Checks for new submissions
2. Retrieves the correct rubric
3. Downloads portfolio content
4. Evaluates the portfolio
5. Generates feedback
6. Sends student feedback emails
7. Updates processing status

No teacher action is required.

---

# Monitoring Submissions

Open **Submissions** to monitor activity.

Possible statuses include:

| Status                         | Meaning                           |
| ------------------------------ | --------------------------------- |
| Feedback sent                  | Feedback delivered successfully   |
| Teacher draft created          | Draft prepared for teacher review |
| Portfolio access issue emailed | Student must correct permissions  |
| Pending                        | Waiting to be processed           |

---

# Before the Due Date

Students receive formative feedback intended to improve their portfolios.

The feedback:

* Identifies strengths
* Highlights missing requirements
* Suggests improvements

No scores are sent.

---

# After the Due Date

Teachers review portfolio performance and assign final grades.

DPAssist assists the evaluation process but does not replace teacher judgment.

Teachers remain responsible for:

* Final grading
* Instructional decisions
* Student communication

---

# Common Issues

## Submission Not Processing

Check:

* Unit Name matches exactly
* Submission appears in Google Sheets
* Worker is running

---

## Portfolio Access Issue

Students must:

* Publish their portfolio
* Allow public access

---

## Rubric Not Found

Verify:

* Rubric exists
* Unit Name matches
* Due date is configured correctly

---

## Configuration Problem

Open **System Status**.

Any failed service will be identified there.

---

# Best Practices

* Upload rubrics before students begin work.
* Use consistent Unit Names.
* Review the Submissions page periodically.
* Verify portfolio publishing requirements with students.
* Keep rubric language clear and specific.

---

# Need Additional Help?

See:

* QUICK_START.md
* README.md
* CLOUD_DEPLOY.md
* ARCHITECTURE.md

for additional documentation and deployment details.

---

# Administrator Notes

The production deployment consists of:

* Streamlit Cloud dashboard
* Render Starter Worker
* Google Sheets storage
* Gemini AI evaluation

Teachers do not need to install Python, configure local services, or run background processes on their computers.
