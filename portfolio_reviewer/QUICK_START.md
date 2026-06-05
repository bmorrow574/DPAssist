# DPAssist — Quick Start Guide

## Welcome to DPAssist

DPAssist automatically evaluates student engineering portfolios, provides AI-generated feedback, and helps teachers manage portfolio-based assessment with minimal manual grading.

Most teachers can be up and running in less than five minutes.

---

# Step 1 — Open the Teacher Dashboard

Open the DPAssist Teacher Dashboard in your web browser.

Example:

```text
https://your-school-dpassist.streamlit.app
```

No software installation is required.

---

# Step 2 — Upload a Rubric

Before students submit portfolios, create a rubric.

1. Click **Rubrics**
2. Upload a rubric PDF
3. Enter the Unit Name
4. Set the Due Date
5. Click **Parse and Add Rubric**

The rubric is automatically stored in the cloud.

---

# Step 3 — Verify the Unit Name

The Unit Name entered in DPAssist must exactly match the Unit Name used in the student Google Form.

Example:

```text
Milling About
```

must match

```text
Milling About
```

and not:

```text
milling about
MillingAbout
Milling About!
```

Exact matches prevent processing errors.

---

# Step 4 — Students Submit Portfolios

Students complete the Google Form and submit:

* Name
* Email
* Unit Name
* Portfolio URL

Submissions are automatically recorded in Google Sheets.

---

# Step 5 — Automatic Processing

Once submitted, DPAssist automatically:

1. Detects new submissions
2. Retrieves the correct rubric
3. Downloads portfolio content
4. Evaluates the portfolio using Gemini AI
5. Generates feedback
6. Sends feedback email to the student
7. Updates submission status

No teacher action is required.

---

# Monitoring Progress

Open the **Submissions** page to monitor activity.

The dashboard displays:

* Student name
* Submission date
* Unit name
* Due date
* Processing status

Common statuses include:

| Status                         | Meaning                                  |
| ------------------------------ | ---------------------------------------- |
| Feedback sent                  | Student feedback email delivered         |
| Teacher draft created          | Draft created for teacher review         |
| Portfolio access issue emailed | Student must correct sharing permissions |
| Pending                        | Waiting to be processed                  |

---

# System Status

Open **System Status** to verify connections.

All items should display a green check mark.

Expected services:

* Google Sheets
* Gemini API
* Gmail
* Credentials

---

# Typical Teacher Workflow

### Beginning of Unit

1. Create rubric
2. Upload rubric
3. Verify due date

### During Unit

1. Monitor submissions page
2. Review any access issues

### After Due Date

1. Review generated feedback
2. Make any desired instructional adjustments
3. Release final grades

---

# Common Issues

## Submission Not Processing

Check:

* Unit name matches rubric exactly
* Background worker is running
* Submission appears in Google Sheets

---

## Portfolio Access Issue

Students must ensure:

* Portfolio is published
* Portfolio link is accessible without login

---

## Rubric Not Found

Verify:

* Rubric exists
* Unit name matches exactly
* Due date is correctly configured

---

# What DPAssist Does Not Do

DPAssist assists the evaluation process but does not replace teacher judgment.

Teachers remain responsible for:

* Reviewing student work
* Assigning final grades
* Making instructional decisions
* Communicating with students and families

---

# Need Additional Help?

See:

* README.md
* ARCHITECTURE.md
* CLOUD_DEPLOY.md

for additional documentation and deployment details.
