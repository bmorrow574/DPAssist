# DPAssist - Quick Start

## Fastest Way to Get Started

### 1. Double-Click to Start

**Mac:** Double-click `START.command`  
**Windows:** Double-click `START.bat`

This will open the launcher window.

---

### 2. In the Launcher Window

1. Click **"Start Background Service"** ← This starts automatic grading
2. Click **"Open Teacher Dashboard"** ← This opens the web interface

---

### 3. In the Teacher Dashboard (Browser)

#### First Time Setup:
1. Go to **"Rubrics"** page
2. Click **"Upload Rubric PDF"**
3. Enter the **unit name** (must match your Google Form exactly!)
4. Select the **due date**
5. Click **"Parse and Add Rubric"**

#### Monitor Submissions:
1. Go to **"Submissions"** page
2. See all student work being processed automatically

---

## What Happens Automatically

Every 60 seconds, the system:
1. ✅ Checks Google Sheet for new submissions
2. ✅ Scrapes the student's portfolio
3. ✅ Evaluates against the rubric using AI
4. ✅ Either:
   - **Before deadline:** Sends feedback (no scores)
   - **After deadline:** Creates Gmail draft with scores

---

## Important Files

### DO NOT SHARE (Keep Private):
- ❌ `.env` - Your API keys
- ❌ `service-account-credentials.json` - Google credentials

### Safe to Edit:
- ✅ `.env` - Update your settings here
- ✅ Rubric PDFs - Upload via dashboard

---

## Common Issues

### "Configuration Issues" Error
→ Make sure `.env` file exists with all fields filled in

### Nothing is Processing
→ Make sure Background Service shows "🟢 Running"  
→ Check that rubrics are uploaded for the student's unit

### Rubric Upload Failed
→ Make sure unit name EXACTLY matches Google Form  
→ Check PDF is a standard format

---

## Need Help?

1. Check the log in the launcher window (shows what's happening)
2. Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
3. Look at [README.md](README.md) for technical details

---

## Daily Workflow

**Morning:**
1. Double-click `START.command` (Mac) or `START.bat` (Windows)
2. Click "Start Background Service"
3. Leave window open

**Anytime:**
- Check "Teacher Dashboard" to see progress
- Upload new rubrics as needed

**End of Day:**
- Click "Stop Background Service"
- Close launcher window

---

**That's it! The system runs automatically once started.**
