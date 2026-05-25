# DPAssist – Setup Guide

Complete setup instructions for teachers. No programming experience required.


## Before You Begin

You will need:
- A Mac or Windows computer
- A Gmail account (this will be the "teacher" email that sends and receives feedback)
- A Google Form already set up to collect student portfolio submissions
- The Google Sheet linked to that form (Google Forms creates this automatically)
- Your rubric as a PDF file

The setup takes about 45–60 minutes the first time. Once it's done, you won't need to repeat it.


## Step 1: Install Python

Python is the programming language this app runs on. Think of it like installing a language your computer needs to understand the app.

### On a Mac:
1. Press **Command + Space** to open Spotlight Search
2. Type **Terminal** and press Enter — a black window will open
3. Type the following and press Enter:
   ```
   python3 --version
   ```
4. If you see something like `Python 3.11.2`, you already have it — skip to Step 2
5. If you get an error, go to **https://www.python.org/downloads/** and click the big yellow Download button
6. Open the downloaded file and follow the installer — all default options are fine

### On Windows:
1. Go to **https://www.python.org/downloads/** and click the big yellow Download button
2. Open the downloaded file
3. **Important:** On the first screen, check the box that says **"Add Python to PATH"** before clicking anything else
4. Click **Install Now**
5. When it finishes, click **Close**


## Step 2: Download DPAssist

1. Go to the DPAssist GitHub page
2. Click the green **Code** button
3. Click **Download ZIP**
4. Find the downloaded ZIP file (usually in your Downloads folder)
5. Double-click it to unzip
6. Move the unzipped folder to your Desktop and rename it **DPAssist**


## Step 3: Install the App's Dependencies

Dependencies are small software packages the app needs to run — like ingredients for a recipe.

### On a Mac:
1. Open Terminal (Command + Space, type Terminal)
2. Type the following and press Enter:
   ```
   cd Desktop/DPAssist/portfolio_reviewer
   ```
3. Then type this and press Enter:
   ```
   pip3 install -r requirements.txt
   ```
4. Wait for it to finish — this takes 2–5 minutes. You'll see a lot of text scrolling by — that's normal.

### On Windows:
1. Click the Start menu and search for **Command Prompt**
2. Type the following and press Enter:
   ```
   cd Desktop\DPAssist\portfolio_reviewer
   ```
3. Then type this and press Enter:
   ```
   pip install -r requirements.txt
   ```
4. Wait for it to finish.


## Step 4: Set Up Google Access

DPAssist needs permission to read your Google Sheet and send emails through Gmail. This section walks you through both.

### Part A: Create a Google Cloud Project

This gives DPAssist a secure way to read your Google Sheet.

1. Go to **https://console.cloud.google.com/**
2. Sign in with your Google account
3. At the top of the page, click **Select a project** → **New Project**
4. Name it **DPAssist** and click **Create**
5. Make sure your new project is selected at the top of the page

### Part B: Enable the Google Sheets API

1. In the left menu, click **APIs & Services** → **Library**
2. Search for **Google Sheets API**
3. Click on it and click **Enable**
4. Go back to the Library, search for **Google Drive API**, and enable that too

### Part C: Create a Service Account

A service account is like a special robot helper that has permission to read your sheet.

1. In the left menu, click **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **Service Account**
3. Name it **dpassist-reader** and click **Create and Continue**
4. Skip the optional steps and click **Done**
5. You'll see your new service account listed — click on it
6. Click the **Keys** tab
7. Click **Add Key** → **Create New Key**
8. Choose **JSON** and click **Create**
9. A file will download automatically — this is your credentials file
10. Rename it to exactly: `service-account-credentials.json`
11. Move it into the `DPAssist/portfolio_reviewer/` folder on your Desktop

### Part D: Share Your Google Sheet with the Service Account

1. Open the `service-account-credentials.json` file in a text editor (TextEdit on Mac, Notepad on Windows)
2. Find the line that says `"client_email"` — copy the email address next to it (it looks like `dpassist-reader@something.iam.gserviceaccount.com`)
3. Open your Google Sheet (the one connected to your Google Form)
4. Click the **Share** button in the top right
5. Paste the service account email address
6. Set the permission to **Editor**
7. Uncheck "Notify people" and click **Share**


## Step 5: Set Up Gmail for Sending Emails

DPAssist sends feedback emails to students and creates draft emails for you using your Gmail. To do this safely, you need to create a special one-time password called an **App Password**.

> **Note:** App Passwords only work if you have 2-Step Verification turned on in your Google account. If you don't have it on, Google will prompt you to enable it during this process.

1. Go to **https://myaccount.google.com/**
2. Click **Security** in the left menu
3. Under "How you sign in to Google", click **2-Step Verification** and make sure it's on
4. Go back to Security and scroll down to find **App passwords** (you may need to search for it in the search bar at the top)
5. Click **App passwords**
6. Under "Select app" choose **Mail**
7. Under "Select device" choose **Other** and type **DPAssist**
8. Click **Generate**
9. Google will show you a 16-character password like `abcd efgh ijkl mnop`
10. **Copy this password and save it somewhere safe** — you'll need it in the next step and Google will not show it again


## Step 6: Get a Gemini API Key

This is what gives DPAssist its AI brain for evaluating portfolios.

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key — it starts with `AIza` and is about 40 characters long
5. Save it somewhere safe

The free tier is sufficient for most classroom sizes.

## Step 7: Configure DPAssist

Now you'll connect everything together.

1. Open the `DPAssist/portfolio_reviewer/` folder on your Desktop
2. Find the file called `.env.example`
3. Make a copy of it and rename the copy to `.env` (just `.env` — delete the word "example")
4. Open the `.env` file in a text editor
5. Fill in each line with your information:

```
GOOGLE_CREDENTIALS_PATH=service-account-credentials.json
GOOGLE_SHEET_ID=paste-your-sheet-id-here
GEMINI_API_KEY=paste-your-gemini-key-here
TEACHER_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=paste-your-16-character-app-password-here
CHECK_INTERVAL_SECONDS=60
```

**How to find your Google Sheet ID:**
- Open your Google Sheet
- Look at the web address at the top of your browser
- It will look like: `https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXXXXXXXXX/edit`
- The Sheet ID is the long string of letters and numbers between `/d/` and `/edit`
- Copy just that part and paste it into your `.env` file

6. Save the `.env` file


## Step 8: Start DPAssist

### On a Mac:
1. Open Terminal
2. Type:
   ```
   cd Desktop/DPAssist/portfolio_reviewer
   ```
3. Then:
   ```
   python3 launcher.py
   ```

### On Windows:
1. Open Command Prompt
2. Type:
   ```
   cd Desktop\DPAssist\portfolio_reviewer
   ```
3. Then:
   ```
   python launcher.py
   ```

A window called **DPAssist Control Panel** will open.

## Step 9: Daily Use

### Starting up each day:
1. Run `python3 launcher.py` (or `python launcher.py` on Windows)
2. Click **Start Background Service** — the dot next to it will turn green
3. Click **Open Teacher Dashboard** — this opens in your web browser
4. Leave the Control Panel window open in the background while you work

### Adding a rubric (do this once per assignment):
1. In the Teacher Dashboard, click **Rubrics** in the left menu
2. Click **Upload Rubric PDF** and choose your rubric file
3. In the **Unit Name** field, type the unit name **exactly** as it appears in your Google Form dropdown — capitalization matters
4. If you teach multiple classes with the same unit, add the class name in the **Class/Course** field
5. Set the **Due Date**
6. Click **Parse and Add Rubric**
7. The system will read your rubric and confirm the criteria it found

### Monitoring submissions:
- Click **Submissions** in the left menu to see all student submissions and their status
- Before the due date: students receive feedback emails automatically
- After the due date: scored draft emails appear in your Gmail Drafts folder for you to review and send

### Shutting down:
1. Click **Stop Background Service**
2. Close the Control Panel window


## Important Notes

**The unit name must match exactly.**
When you upload a rubric, the Unit Name you type must be identical to what appears in your Google Form. If the form says "Milling About", type exactly "Milling About" — not "milling about" or "Milling About!".

**Keep the Control Panel open.**
The background service only runs while the Control Panel window is open. If you close it, processing stops.

**Gmail drafts appear after the deadline.**
Before the due date, feedback emails go directly to students (without scores). After the due date, DPAssist creates a draft in your Gmail for each student — with full scores — for you to review before sending.

**Your credentials are private.**
The `.env` file and `service-account-credentials.json` are never uploaded to GitHub. They stay on your computer only.


## Troubleshooting

**"Configuration Issues" appears when opening the dashboard**
- Check that your `.env` file exists in the `portfolio_reviewer` folder
- Make sure every line in `.env` is filled in with no blank values
- Make sure `service-account-credentials.json` is in the same folder

**"Failed to connect to Google Sheets"**
- Double-check that you shared the Google Sheet with the service account email address
- Make sure the Sheet ID in your `.env` file is correct (no extra spaces)

**Students are not receiving emails**
- Check that your Gmail App Password is correct in the `.env` file
- Make sure 2-Step Verification is enabled on your Google account
- Look at the log output in the Control Panel for specific error messages

**Rubric parsing fails**
- Make sure your PDF rubric has clear section titles and point values
- Try re-saving the PDF from its original source
- If your rubric is in a table format, try exporting it as a plain PDF

**The background service stops unexpectedly**
- Check the log in the Control Panel for error messages
- Make sure your computer hasn't gone to sleep — adjust your energy settings to prevent sleep while the service is running


## Google Sheet Column Requirements

DPAssist expects your Google Form responses sheet to have columns with these names (Google Forms creates most of these automatically):

- Timestamp
- What is your class section?
- What is your last name?
- What is your first name?
- Select the unit
- A column with "PUBLISHED" in the name (for the portfolio URL)
- What is your email address?

DPAssist will automatically add three columns if they don't exist yet:
- Status
- Feedback Sent
- Last Processed