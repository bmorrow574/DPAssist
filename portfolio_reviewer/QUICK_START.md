# DPAssist — Quick Start

Two ways to run DPAssist. Choose the one that works best for you.

---

## Path A: Cloud (Recommended)

No installation required. Works in any browser on any computer.

### Step 1 — Open the Teacher Dashboard
Go to your Streamlit URL (example: `https://your-app-name.streamlit.app`)

Bookmark this link — it's all you need every day.

### Step 2 — Add Your Rubric (First time only, once per assignment)
1. Click **Rubrics** in the left menu
2. Click **Upload Rubric PDF** and choose your rubric file
3. Type the **Unit Name** exactly as it appears in your Google Form
4. Set the **Due Date**
5. Click **Parse and Add Rubric**

### Step 3 — That's It
The background processor runs 24/7 automatically. Every 60 seconds it:
- ✅ Checks your Google Sheet for new submissions
- ✅ Scrapes the student's portfolio
- ✅ Evaluates it against your rubric using AI
- ✅ Before deadline → emails feedback directly to student (no scores)
- ✅ After deadline → creates a scored draft in your Gmail for review

Check the **Submissions** page anytime to see status.

---

## Path B: Local (If cloud is unavailable)

Runs on your own computer. Requires one-time setup (see SETUP_GUIDE.md).

### Step 1 — Start the App
**Mac:** Double-click `START.command`
**Windows:** Double-click `START.bat`

The DPAssist Control Panel window will open.

### Step 2 — Start the Services
1. Click **Start Background Service** — dot turns green 🟢
2. Click **Open Teacher Dashboard** — opens in your browser

### Step 3 — Add Your Rubric (First time only, once per assignment)
1. Click **Rubrics** in the left menu
2. Click **Upload Rubric PDF** and choose your rubric file
3. Type the **Unit Name** exactly as it appears in your Google Form
4. Set the **Due Date**
5. Click **Parse and Add Rubric**

### Step 4 — Leave It Running
Keep the Control Panel window open while you work. The system processes submissions automatically every 60 seconds.

**End of day:** Click **Stop Background Service**, then close the window.

---

## What the Dashboard Shows You

| Page | What It Does |
|------|-------------|
| Rubrics | Upload and manage rubrics for each assignment |
| Submissions | See every student submission and its processing status |
| System Status | Confirm all connections are working (all should show ✅) |

---

## The One Rule That Matters Most

**The Unit Name must match your Google Form exactly.**
If your form says "Milling About" the rubric must say "Milling About" — not "milling about" or "Milling About!". Capitalization and punctuation matter.

---

## Common Issues

**"Configuration Issues" on the dashboard**
→ Check System Status page — it will show exactly which connection is failing

**Nothing is processing**
→ Cloud: Check that your Render background worker is running
→ Local: Make sure the Control Panel shows Background Service 🟢 Running

**Rubric upload failed**
→ Make sure the PDF has clear section titles and point values
→ Try re-exporting the PDF from its original source

**Student didn't receive feedback**
→ Check the Submissions page — look at the Status column for that student
→ Verify their portfolio URL is publicly accessible

---

## Need More Help?

- **Full setup instructions:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Technical details:** [README.md](README.md)
- **What went wrong and how we fixed it:** [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)