# DPAssist — Cloud Deployment Guide

This guide deploys DPAssist so that **any teacher anywhere can use it from a browser** with no local Python installation needed.

Two services run in the cloud:
| Service | Platform | Purpose |
|---------|----------|---------|
| Teacher Dashboard | **Streamlit Cloud** (free) | Web UI — upload rubrics, view submissions |
| Background Processor | **Render** (free) | Checks Google Sheets every 60 s, evaluates portfolios, sends feedback |

---

## Prerequisites

Before deploying, make sure you have:
- [ ] Your GitHub repo is public (or Streamlit Cloud has access to a private repo)
- [ ] `service-account-credentials.json` contents ready to paste
- [ ] Gemini API key from [Google AI Studio](https://aistudio.google.com)
- [ ] Gmail App Password from [Google Account Security](https://myaccount.google.com/apppasswords)
- [ ] Google Sheet ID (the long string in your form-responses sheet URL)

---

## Step 1 — Deploy the Teacher Dashboard to Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. Click **New app**.
3. Set:
   - **Repository**: `bmorrow574/DPAssist_Final` (or your fork)
   - **Branch**: `main`
   - **Main file path**: `portfolio_reviewer/teacher_ui.py`
4. Click **Advanced settings** → **Secrets**, then paste the contents of
   `.streamlit/secrets.toml.example` with your real values filled in.
5. Click **Deploy**.

Your Teacher Dashboard will be live at a URL like  
`https://your-app-name.streamlit.app`

Share this URL with any teacher — no installation needed.

---

## Step 2 — Deploy the Background Processor to Render

1. Go to **[render.com](https://render.com)** and sign in with GitHub.
2. Click **New → Background Worker**.
3. Connect your GitHub repo.
4. Render will auto-detect `render.yaml` in the root of the repo.
5. In the Render dashboard, set the following **Environment Variables**:

| Key | Value |
|-----|-------|
| `GOOGLE_CREDENTIALS_JSON` | Paste entire contents of `service-account-credentials.json` |
| `GOOGLE_SHEET_ID` | Your sheet ID |
| `GEMINI_API_KEY` | Your Gemini key |
| `TEACHER_EMAIL` | Teacher's Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password |
| `RUBRIC_STORAGE` | `sheets` |
| `CHECK_INTERVAL_SECONDS` | `60` |

6. Click **Create Background Worker**.

The processor will start immediately and run 24/7.

---

## How rubrics work in cloud mode

When `RUBRIC_STORAGE=sheets` is set:
- Rubrics are stored in a dedicated tab called **DPAssist_Rubrics** inside your existing Google Sheet
- The tab is created automatically on first use — no manual setup needed
- The teacher uploads the PDF from the Streamlit UI; the parsed criteria are saved to the sheet
- Both the Dashboard and the Background Processor read rubrics from the same sheet tab
- **No files are stored locally** — everything persists in Google Sheets

---

## Keeping credentials safe

- Never commit `.env` or `service-account-credentials.json` to GitHub (`.gitignore` already excludes them)
- Store all secrets in the Streamlit Cloud Secrets panel and Render environment variables
- The `GOOGLE_CREDENTIALS_JSON` variable holds the entire JSON as one string (paste it all on one line)

---

## Updating the deployment

Push to `main` → both services redeploy automatically.
