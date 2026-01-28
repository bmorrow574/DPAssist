# PortfoliOS Setup Guide
## For Non-Technical Teachers

This guide will walk you through setting up PortfoliOS step-by-step. **No prior programming experience needed!**

---

## Table of Contents

1. [What You'll Need](#what-youll-need)
2. [Step 1: Install Python](#step-1-install-python)
3. [Step 2: Download PortfoliOS](#step-2-download-portfolios)
4. [Step 3: Get Google Cloud Credentials](#step-3-get-google-cloud-credentials)
5. [Step 4: Get Gemini AI API Key](#step-4-get-gemini-ai-api-key)
6. [Step 5: Setup Email Access](#step-5-setup-email-access)
7. [Step 6: Create Your Configuration File](#step-6-create-your-configuration-file)
8. [Step 7: Install Required Software](#step-7-install-required-software)
9. [Step 8: Run PortfoliOS](#step-8-run-portfolios)
10. [Troubleshooting](#troubleshooting)

---

## What You'll Need

Before starting, gather:
- A computer (Windows, Mac, or Linux)
- A Google account (for Google Sheets access)
- A Gmail or Outlook account (for sending emails)
- About 30-60 minutes to complete setup
- A portfolio assignment Google Sheet with student submissions

---

## Step 1: Install Python

Python is the programming language PortfoliOS is written in.

### Windows:

1. Go to https://www.python.org/downloads/
2. Click the yellow "Download Python" button (get version 3.9 or newer)
3. Run the downloaded installer
4. **IMPORTANT**: Check the box "Add Python to PATH" at the bottom of the installer
5. Click "Install Now"
6. Wait for installation to complete

### Mac:

1. Open Terminal (press Command + Space, type "Terminal", press Enter)
2. Copy and paste this command and press Enter:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. After Homebrew installs, type:
   ```
   brew install python3
   ```

### Verify Installation:

Open a terminal/command prompt and type:
```bash
python --version
```

You should see something like "Python 3.9.x" or newer.

---

## Step 2: Download PortfoliOS

### If you're comfortable with GitHub:

1. Go to the PortfoliOS GitHub repository
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to a folder on your computer (e.g., `Documents/PortfoliOS`)

### If GitHub is confusing:

1. Your colleague can send you a ZIP file with all the code
2. Extract it to a folder on your computer

---

## Step 3: Get Google Cloud Credentials

This allows PortfoliOS to read and write to your Google Sheet.

### Step 3.1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Sign in with your Google account
3. Click the project dropdown at the top (next to "Google Cloud")
4. Click "NEW PROJECT"
5. Name it "PortfoliOS" (or anything you like)
6. Click "CREATE"
7. Wait a few seconds, then select your new project from the dropdown

### Step 3.2: Enable Google Sheets API

1. In the search bar at the top, type "Google Sheets API"
2. Click on "Google Sheets API" in the results
3. Click the blue "ENABLE" button
4. Wait for it to enable

### Step 3.3: Enable Google Drive API

1. In the search bar at the top, type "Google Drive API"
2. Click on "Google Drive API" in the results
3. Click the blue "ENABLE" button

### Step 3.4: Create Service Account

1. In the left sidebar, click "Credentials"
2. At the top, click "+ CREATE CREDENTIALS"
3. Select "Service Account"
4. Give it a name like "PortfoliOS Bot"
5. Click "CREATE AND CONTINUE"
6. For role, select "Editor" (you can search for it)
7. Click "CONTINUE"
8. Click "DONE"

### Step 3.5: Download Credentials File

1. You'll see your service account in the list
2. Click on the service account email (looks like portfolios-bot@...)
3. Go to the "KEYS" tab
4. Click "ADD KEY" → "Create new key"
5. Choose "JSON" format
6. Click "CREATE"
7. A file will download - **THIS IS IMPORTANT!**
8. Rename the file to `service-account-credentials.json`
9. Move it to your PortfoliOS folder

### Step 3.6: Share Your Google Sheet

1. Open the JSON file you just downloaded in a text editor
2. Find the line with "client_email" - it looks like:
   `"client_email": "portfolios-bot@your-project.iam.gserviceaccount.com"`
3. Copy that email address
4. Open your Google Sheet with student submissions
5. Click the "Share" button (top right)
6. Paste the service account email
7. Make sure it has "Editor" permissions
8. Click "Share"

---

## Step 4: Get Gemini AI API Key

Gemini is Google's AI that analyzes the portfolios.

1. Go to https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Choose your Google Cloud project (PortfoliOS)
5. Click "Create API Key in Existing Project"
6. **Copy the API key and save it somewhere safe** (you'll need it soon)

**Note**: Gemini API has a free tier that should be sufficient for most classrooms. Check current limits at https://ai.google.dev/pricing

---

## Step 5: Setup Email Access

PortfoliOS needs to send emails on your behalf.

### Option A: Gmail (Recommended)

#### Step 5.1: Enable 2-Factor Authentication

1. Go to https://myaccount.google.com/security
2. Under "Signing in to Google", click "2-Step Verification"
3. Follow the prompts to set it up (you'll need your phone)

#### Step 5.2: Create App Password

1. Go to https://myaccount.google.com/apppasswords
2. In the "Select app" dropdown, choose "Mail"
3. In the "Select device" dropdown, choose "Other" and type "PortfoliOS"
4. Click "Generate"
5. **Copy the 16-character password (no spaces)** - you'll need this!

### Option B: Outlook

1. Go to https://account.microsoft.com/security
2. Sign in with your Microsoft account
3. Under "Advanced security options", click "App passwords"
4. Click "Create a new app password"
5. Copy the generated password

### Option C: Other Email Provider

You'll need to find your email provider's SMTP settings:
- SMTP server address (e.g., smtp.example.com)
- SMTP port (usually 587)
- Your email password (or app-specific password)

---

## Step 6: Create Your Configuration File

1. In your PortfoliOS folder, find the file `config.example.yaml`
2. Make a copy of it and rename the copy to `config.yaml`
3. Open `config.yaml` in a text editor (Notepad, TextEdit, VS Code, etc.)
4. Fill in the following sections:

### Google Sheets Settings:

```yaml
google_sheets:
  spreadsheet_name: "Your Exact Sheet Name Here"
  service_account_file: "service-account-credentials.json"
  check_interval: 300  # Check every 5 minutes
```

### Deadline Settings:

```yaml
deadline:
  datetime: "2026-02-15 23:59"  # Use your actual deadline
  timezone: "America/New_York"   # Use your timezone
```

**Common US Timezones:**
- Eastern: `America/New_York`
- Central: `America/Chicago`
- Mountain: `America/Denver`
- Pacific: `America/Los_Angeles`

### Gemini AI Settings:

```yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY_HERE"  # Paste the key from Step 4
  model: "gemini-2.0-flash-exp"
  temperature: 0.7
```

### Email Settings (Gmail Example):

```yaml
email:
  provider: "gmail"
  teacher_email: "your.email@gmail.com"  # Your email
  
  gmail:
    app_password: "abcdabcdabcdabcd"  # Your app password from Step 5
```

### Rubric (Optional):

If you have a rubric document:
```yaml
rubric:
  file_path: "my_rubric.pdf"  # Put rubric file in PortfoliOS folder
```

Or paste rubric text directly:
```yaml
rubric:
  text: |
    Your rubric text here
    Can span multiple lines
```

**Save the file when done!**

---

## Step 7: Install Required Software

### Step 7.1: Open Terminal/Command Prompt

**Windows**: Press Windows Key + R, type `cmd`, press Enter

**Mac**: Press Command + Space, type "Terminal", press Enter

### Step 7.2: Navigate to PortfoliOS Folder

Type this command (adjust the path to where you put PortfoliOS):

**Windows**:
```bash
cd C:\Users\YourName\Documents\PortfoliOS
```

**Mac**:
```bash
cd ~/Documents/PortfoliOS
```

### Step 7.3: Install Requirements

Copy this command and press Enter:

```bash
pip install -r requirements.txt
```

This will download and install all the software PortfoliOS needs. It may take a few minutes.

**If you see errors**, try:
```bash
pip3 install -r requirements.txt
```

---

## Step 8: Run PortfoliOS

You're ready to run PortfoliOS!

### First Time Testing:

In your terminal (still in the PortfoliOS folder), type:

```bash
python main.py
```

Or:
```bash
python3 main.py
```

You should see:
```
======================================================================
PortfoliOS - Multi-Agent Portfolio Feedback System
======================================================================

Initializing...
✓ System initialized successfully

The system is now running continuously.
It will automatically process new submissions as they arrive.

Press Ctrl+C to stop.
======================================================================
```

### Let it Run:

- PortfoliOS will now check your Google Sheet every 5 minutes (or whatever you set)
- When students submit portfolios, it will automatically process them
- Before the deadline: students get immediate feedback via email
- After the deadline: you get draft emails to review

### To Stop:

Press `Ctrl+C` (or Command+C on Mac)

---

## Running PortfoliOS Continuously

### Option 1: Keep Computer Awake (Simplest)

1. Leave PortfoliOS running
2. Adjust your computer's power settings so it doesn't sleep
3. The program will keep running until you stop it

**Windows**: Settings → System → Power & Sleep → "Never"
**Mac**: System Preferences → Energy Saver → Uncheck "Put hard disks to sleep"

### Option 2: Run in Background (Advanced)

**Windows** (using Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task
3. Set it to run `python main.py` in your PortfoliOS folder
4. Set trigger (e.g., "At startup")

**Mac** (using launchd):
1. More complex - consider Option 1 or ask for help

### Option 3: Cloud Server (Most Reliable, Costs Money)

Deploy to:
- Google Cloud Run
- Amazon AWS
- Microsoft Azure

(This requires technical knowledge - consider hiring someone to help)

---

## Troubleshooting

### "Config file not found"

- Make sure you created `config.yaml` (not `config.example.yaml`)
- Make sure it's in the same folder as `main.py`

### "Invalid API key"

- Double-check your Gemini API key in `config.yaml`
- Make sure there are no extra spaces or quotes

### "Could not connect to Google Sheets"

- Make sure you shared the sheet with the service account email
- Check that the spreadsheet name in `config.yaml` matches exactly (including capitals)

### "Authentication failed" (Email)

- For Gmail: Make sure you created an App Password, not using your regular password
- Make sure 2-Factor Authentication is enabled
- Check there are no spaces in the app password

### "Module not found"

- Make sure you ran `pip install -r requirements.txt`
- Try `pip3` instead of `pip`

### Chrome/Selenium Errors

PortfoliOS needs Chrome to view portfolios. Make sure:
- Google Chrome is installed on your computer
- If errors persist, the program will try to download ChromeDriver automatically

### Still Having Issues?

1. Check the log files in the `logs` folder for detailed error messages
2. Post the error message in the GitHub Issues section
3. Include:
   - Your operating system (Windows/Mac/Linux)
   - The error message
   - What you were trying to do

---

## Understanding What PortfoliOS Does

When a student submits their portfolio:

1. **Before Deadline**:
   - ✓ Checks if link works
   - ✓ Checks if media loads
   - ✓ Uses AI to analyze captions
   - ✓ Generates feedback
   - ✓ **Sends feedback directly to student's email**
   - ✓ Students can resubmit as many times as they want

2. **After Deadline**:
   - ✓ Does all the same checks
   - ✓ Generates comprehensive feedback
   - ✓ **Creates DRAFT email for you to review**
   - ✓ You review, edit if needed, and send manually

---

## Privacy & Security Notes

- Your API keys and passwords are stored locally in `config.yaml`
- **Never share your config.yaml file with anyone**
- Never commit config.yaml to GitHub (it's in .gitignore already)
- The service account only has access to sheets you explicitly share with it
- Student data is processed locally and via Google's APIs (subject to Google's privacy policy)

---

## Getting Help

- **GitHub Issues**: Post questions at [GitHub repo]/issues
- **Documentation**: Check README.md for more details
- **Community**: Look for other teachers using PortfoliOS

---

## Next Steps

Once PortfoliOS is running:

1. Test with a dummy submission first
2. Adjust the AI feedback parameters in `config.yaml` if needed
3. Customize email templates if desired
4. Set up automated backups of your Google Sheet

**Congratulations! You're all set up!** 🎉
