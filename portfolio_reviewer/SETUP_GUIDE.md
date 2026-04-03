# DPAssist - Setup Guide

Complete setup instructions for teachers (no programming experience required).

## What This System Does

1. **Reads student portfolio submissions** from your Google Form responses
2. **Scrapes portfolio content** from Google Sites or GitHub Pages
3. **Evaluates using AI** (Gemini) against your uploaded rubrics
4. **Sends feedback** (no scores) before the due date
5. **Creates draft emails** (with scores) in your Gmail after the due date
6. **Runs automatically** every 60 seconds in the background

---

## Step 1: Install Python

### Mac:
1. Open Terminal (search for "Terminal" in Spotlight)
2. Type: `python3 --version`
3. If you see a version number (like 3.9.x or higher), skip to Step 2
4. If not, download Python from: https://www.python.org/downloads/
5. Install Python, making sure to check "Add Python to PATH"

### Windows:
1. Download Python from: https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check the box "Add Python to PATH" at the bottom
4. Click "Install Now"
5. Open Command Prompt and type: `python --version`
6. You should see a version number (3.9.x or higher)

---

## Step 2: Download the Project

1. Download all project files to a folder on your computer (e.g., `Desktop/PortfolioReviewer`)
2. Make sure you have these files:
   - `launcher.py`
   - `background_service.py`
   - `teacher_ui.py`
   - `config.py`
   - `requirements.txt`
   - `.env.example`
   - All the other `.py` files

---

## Step 3: Install Required Software

### Mac:
1. Open Terminal
2. Navigate to your project folder:
   ```bash
   cd Desktop/PortfolioReviewer
   ```
3. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

### Windows:
1. Open Command Prompt
2. Navigate to your project folder:
   ```
   cd Desktop\PortfolioReviewer
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

**Wait for installation to complete** (this may take a few minutes).

---

## Step 4: Setup Google Credentials

### A. Get Service Account Credentials

1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing one)
3. Enable these APIs:
   - Google Sheets API
   - Gmail API
   - Google Drive API
4. Go to "IAM & Admin" → "Service Accounts"
5. Click "Create Service Account"
6. Name it: `portfolio-grader`
7. Click "Create and Continue"
8. Skip granting roles (click "Continue")
9. Click "Done"
10. Click on the service account you just created
11. Go to "Keys" tab
12. Click "Add Key" → "Create New Key"
13. Choose "JSON"
14. Download the file
15. **Rename it to:** `service-account-credentials.json`
16. **Move it to your project folder**

### B. Share Your Google Sheet

1. Open the downloaded `service-account-credentials.json` file
2. Find the `client_email` field (looks like: `portfolio-grader@xxx.iam.gserviceaccount.com`)
3. Copy this email address
4. Open your Google Sheet with form responses
5. Click "Share" button
6. Paste the service account email
7. Give it "Editor" permissions
8. Click "Send"

### C. Enable Gmail Domain Delegation (for draft emails)

**NOTE:** This requires Google Workspace admin access. If you don't have admin access, you'll need to ask your IT department for help.

1. Go to: https://admin.google.com/
2. Navigate to: Security → API Controls → Domain-wide Delegation
3. Click "Add new"
4. Paste the service account's "Client ID" (from the JSON file)
5. Add this scope: `https://www.googleapis.com/auth/gmail.compose`
6. Click "Authorize"

---

## Step 5: Get Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. Keep it somewhere safe (you'll need it in the next step)

---

## Step 6: Configure the System

1. In your project folder, find `.env.example`
2. **Copy it** and rename the copy to `.env` (just `.env`, no `.example`)
3. Open `.env` in a text editor (TextEdit on Mac, Notepad on Windows)
4. Fill in your information:

```
GOOGLE_CREDENTIALS_PATH=service-account-credentials.json
GOOGLE_SHEET_ID=1bHU943lMaKwU0HjjwFoO0Dqcc1CB64-bZ5vuKhvWFbw
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXX
TEACHER_EMAIL=your.email@gmail.com
CHECK_INTERVAL_SECONDS=60
```

**How to find your Sheet ID:**
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/1bHU943lMaKwU0HjjwFoO0Dqcc1CB64-bZ5vuKhvWFbw/edit`
- The Sheet ID is the long string between `/d/` and `/edit`

5. Save the `.env` file

---

## Step 7: Start the System

### Mac:
1. Open Terminal
2. Navigate to project folder: `cd Desktop/PortfolioReviewer`
3. Run: `python3 launcher.py`

### Windows:
1. Open Command Prompt
2. Navigate to project folder: `cd Desktop\PortfolioReviewer`
3. Run: `python launcher.py`

**OR - Create a shortcut (easier):**

### Mac:
1. Right-click `launcher.py`
2. Select "Open With" → "Python Launcher"
3. Double-click `launcher.py` to start

### Windows:
1. Create a new text file called `Start DPAssist.bat`
2. Add this line:
   ```
   python launcher.py
   pause
   ```
3. Save it
4. Double-click the `.bat` file to start

---

## Step 8: Use the System

### A. Launch Window

When you run the launcher, you'll see:
- **Start Background Service** button - starts automatic processing
- **Open Teacher Dashboard** button - opens web interface for managing rubrics

### B. Add Rubrics

1. Click "Open Teacher Dashboard"
2. Go to "Rubrics" page
3. Upload your rubric PDF
4. Enter the **exact unit name** from your Google Form
5. Set the due date
6. Click "Parse and Add Rubric"

### C. Monitor Submissions

1. In the Teacher Dashboard, go to "Submissions" page
2. See all student submissions and their processing status
3. Check if drafts were created

### D. Background Processing

- The background service runs **every 60 seconds**
- It checks for new submissions
- Evaluates portfolios automatically
- Creates feedback/drafts based on due date
- **Keep the launcher window open** while it's running

---

## Important Notes

### Security
- **NEVER** commit `.env` or `service-account-credentials.json` to GitHub
- These files are already in `.gitignore` to protect you
- Keep your API keys private

### Google Sheet Headers
The system expects these columns in your Google Sheet:
- Timestamp
- What is your class section?
- What is your LAST name?
- What is your first name?
- Select the unit
- Portfolio URL (with "PUBLISHED" in the column name)
- What is your email address?
- Status
- Feedback Sent
- Last Processed

The system will auto-create the last 3 columns if they don't exist.

### Rubric Matching
- The "Unit Name" you enter when uploading a rubric **must exactly match** the unit name from the Google Form dropdown
- Example: If form says "Plane and Simple", use exactly "Plane and Simple" (not "plane and simple" or "Plane & Simple")

### Gmail Drafts
- Drafts will appear in **your** Gmail drafts folder (the teacher email you specified)
- You can review and edit them before sending
- This happens only AFTER the due date

---

## Troubleshooting

### "Configuration Issues" error
- Check that your `.env` file exists and has all fields filled in
- Make sure `service-account-credentials.json` is in the project folder
- Verify the Sheet ID is correct

### "Failed to connect to Google Sheets"
- Make sure you shared the Google Sheet with the service account email
- Check that the service account has "Editor" permissions
- Verify the Sheet ID in `.env` is correct

### "Gmail API connection error"
- Make sure you enabled Gmail API in Google Cloud Console
- Verify domain-wide delegation is set up correctly
- Check that the teacher email in `.env` matches your actual email

### Rubric parsing fails
- Make sure the PDF has clear section headers with point values
- Try a different PDF format
- Contact support if rubrics consistently fail to parse

### Background service not processing
- Check that the launcher shows "Background Service: 🟢 Running"
- Look at the log output for error messages
- Verify your Google Sheet has new submissions
- Make sure rubrics are configured for the units students submitted

---

## Getting Help

If you encounter issues:
1. Check the log output in the launcher window
2. Look for error messages in red
3. Verify all setup steps were completed
4. Check that all API credentials are correct

---

## Updating the System

When updates are available:
1. Download new files
2. Replace old files in your folder
3. Run: `pip install -r requirements.txt --upgrade`
4. Restart the launcher

---

## Daily Use

**To start grading:**
1. Double-click launcher (or run `python launcher.py`)
2. Click "Start Background Service"
3. Leave the window open
4. Check "Open Teacher Dashboard" to manage rubrics or view submissions

**When finished:**
- Click "Stop Background Service"
- Close the launcher window

**That's it! The system will automatically grade portfolios every 60 seconds while running.**
