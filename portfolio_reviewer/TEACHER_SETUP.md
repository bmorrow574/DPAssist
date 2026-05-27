# DPAssist — Teacher Setup Guide

Complete setup instructions for teachers. No programming experience required.

**Total time:** About 60 minutes, one time only. After that, daily use takes 2 minutes.

---

## What you will need before starting

- A Gmail account — this will send and receive all feedback emails
- A Google Form already set up to collect student portfolio submissions
- The Google Sheet linked to that form (Google Forms creates this automatically)
- Your rubric as a PDF file

---

## Step 1 — Create a Google Cloud Project

*About 10 minutes*

Google Cloud is where you give DPAssist permission to read your Google Sheet. Think of it as creating a secure key that only your app can use.

1. Open your browser and go to **https://console.cloud.google.com**
2. Sign in with your Google account
3. At the top of the page, click where it says **"Select a project"**
4. Click **"New Project"** in the top right of the popup
5. Type **DPAssist** as the project name and click **"Create"**
6. Wait a few seconds, then confirm **"DPAssist"** is showing as the selected project at the top

---

## Step 2 — Enable the Google Sheets API

*About 3 minutes*

This gives your project permission to read and write to Google Sheets.

1. In the left menu, click **"APIs & Services"** then **"Library"**
2. Search for **Google Sheets API**, click on it, then click the blue **"Enable"** button
3. Go back to the Library, search for **Google Drive API**, click it, and click **"Enable"**

---

## Step 3 — Create a Service Account

*About 10 minutes*

A service account is like a robot assistant with its own email address. You give it permission to access your sheet, and DPAssist uses it to read your student submissions.

1. In the left menu, click **"APIs & Services"** then **"Credentials"**
2. Click **"+ Create Credentials"** at the top, then choose **"Service Account"**
3. Type **dpassist-reader** as the name
4. Click **"Create and Continue"**, skip the optional steps, and click **"Done"**
5. Click on the service account you just created in the list
6. Click the **"Keys"** tab
7. Click **"Add Key"** → **"Create New Key"**
8. Choose **"JSON"** and click **"Create"**
9. A file downloads automatically — this is your credentials file. **Keep it safe.**

> ⚠️ **Important:** This file contains your private credentials. Never share it with anyone or post it online.

**Find your service account email — you will need this in Step 4:**
Open the downloaded JSON file in a text editor (TextEdit on Mac, Notepad on Windows). Find the line that says `"client_email"` and copy the email address next to it. It looks like:
`dpassist-reader@your-project.iam.gserviceaccount.com`

---

## Step 4 — Share your Google Sheet

*About 2 minutes*

Give your service account access to the sheet where your form responses are collected.

1. Open your Google Sheet (the one connected to your Google Form)
2. Click the **"Share"** button in the top right
3. Paste the service account email address from Step 3
4. Set the permission to **"Editor"**
5. Uncheck **"Notify people"** and click **"Share"**

**Find your Sheet ID — you will need this in Step 7:**

Look at the web address of your Google Sheet:
```
https://docs.google.com/spreadsheets/d/THIS-PART-IS-YOUR-ID/edit
```
Copy the long string of letters and numbers between `/d/` and `/edit`. Save it somewhere.

---

## Step 5 — Create a Gmail App Password

*About 5 minutes*

DPAssist sends feedback emails to students using your Gmail. An App Password is a special one-time password that lets it do this safely — without using your real password.

1. Go to **https://myaccount.google.com** and click **"Security"** in the left menu
2. Under "How you sign in to Google", click **"2-Step Verification"** and make sure it is turned on
3. Search for **"App passwords"** in the search bar at the top of your Google Account page
4. Click on it, then type **DPAssist** in the app name box and click **"Generate"**
5. Google shows you a 16-character password — **copy it immediately and save it**

> ⚠️ **Google shows this password only once.** Copy it before closing the window. Remove any spaces when saving it.

---

## Step 6 — Get a Gemini API Key

*About 3 minutes*

The Gemini API is the AI brain of DPAssist. It reads student portfolios and evaluates them against your rubric. The free tier handles most classroom sizes.

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key — it starts with `AIza` and is about 40 characters long
5. Save it somewhere safe — treat it like a password

---

## Step 7 — Deploy to Streamlit Cloud

*About 20 minutes*

This is the final step — putting your own copy of DPAssist on the internet so any teacher can use it from a browser.

### Fork the repository

1. Go to **https://github.com/bmorrow574/DPAssist**
2. Click the **"Fork"** button in the top right — this creates your own copy of the code
3. Keep all the default settings and click **"Create fork"**

### Create your Streamlit app

1. Go to **https://share.streamlit.io** and sign in with your GitHub account
2. Click **"New app"**
3. Fill in these fields exactly:

| Field | Value |
|-------|-------|
| Repository | `your-github-username/DPAssist` |
| Branch | `main` |
| Main file path | `portfolio_reviewer/teacher_ui.py` |

4. Click **"Advanced settings"** — do not click Deploy yet
5. Click **"Secrets"**

### Paste your secrets

In the Secrets box, type the following — replacing each value with your own. **Type the apostrophes manually on your keyboard.**

```
GOOGLE_SHEET_ID = "paste-your-sheet-id-here"
GEMINI_API_KEY = "paste-your-gemini-key-here"
TEACHER_EMAIL = "your.email@gmail.com"
GMAIL_APP_PASSWORD = "your16charpassword"
RUBRIC_STORAGE = "sheets"
CHECK_INTERVAL_SECONDS = "60"
GOOGLE_CREDENTIALS_JSON = '''
paste entire contents of your service-account-credentials.json file here
'''
```

> ⚠️ **The triple quotes are critical.** The last entry uses three apostrophe characters `'''` on each side of the JSON. Type these manually — do not copy them from a document, as some apps replace them with curved quotes that will not work.

**To paste the JSON file:** Open `service-account-credentials.json` in a text editor. Press Command+A (Mac) or Ctrl+A (Windows) to select everything, then copy and paste it between the triple quotes.

### Deploy

1. Click **"Save"** to save your secrets
2. Click **"Deploy"**
3. Streamlit builds and launches your app — this takes about 2 minutes
4. Once live, click the three-dot menu ⋮ → **Settings** → **App URL**
5. Type a name like `dpassist-yourschool` and save — your app will be at `dpassist-yourschool.streamlit.app`

> ✅ **Setup complete!** Bookmark your Streamlit URL — this is all you need to open every day.

---

## Step 8 — Daily Use

### Adding a rubric (once per assignment)

1. Open your Streamlit URL in any browser
2. Click **"Rubrics"** in the left menu
3. Upload your rubric PDF
4. Type the unit name **exactly** as it appears in your Google Form dropdown — capitalization matters
5. Set the due date and click **"Parse and Add Rubric"**

### What happens automatically

Every 60 seconds, DPAssist:
- Checks your Google Sheet for new student submissions
- Scrapes the student's portfolio website
- Evaluates it against your rubric using AI
- **Before the deadline** → emails feedback directly to the student (no scores)
- **After the deadline** → creates a scored draft in your Gmail for you to review

### Reviewing scored drafts (after the deadline)

1. Open Gmail and go to your **Drafts** folder
2. You will see one draft per student submission
3. Read the AI evaluation — edit anything you want to change
4. Click **Send** when you are happy with it

> **Remember:** No scores are ever sent automatically. You review and send every final email yourself.

---

## Troubleshooting

**"Configuration Issues" appears on the dashboard**
Check the System Status page — it will show exactly which connection is failing. Make sure all your secrets are filled in correctly in Streamlit.

**Students are not receiving feedback emails**
Check that your Gmail App Password has no spaces. Make sure 2-Step Verification is still enabled on your Google account.

**Rubric upload failed**
Make sure your PDF has clear section titles and point values. Try re-exporting it from its original source.

**The unit name must match exactly**
If your Google Form says "Milling About" the rubric must say exactly "Milling About" — not "milling about" or "Milling About!". This is the most common reason submissions don't get processed.

---

## Google Sheet column requirements

DPAssist expects your Google Form responses sheet to have columns with these names (Google Forms creates most automatically):

- Timestamp
- What is your class section?
- What is your last name?
- What is your first name?
- Select the unit
- A column with "PUBLISHED" in the name (for the portfolio URL)
- What is your email address?

DPAssist automatically adds three columns if they don't exist: Status, Feedback Sent, Last Processed.
