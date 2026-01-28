# DPAssist Troubleshooting Guide

## Common Issues and Solutions

---

### Installation Issues

#### "pip: command not found"

**Problem**: Python's package manager isn't recognized.

**Solutions**:
1. Try `pip3` instead of `pip`
2. On Windows: Make sure Python is added to PATH (reinstall Python and check "Add to PATH")
3. On Mac: Install Python via Homebrew: `brew install python3`

#### "Permission denied" when installing packages

**Problem**: You don't have permissions to install system-wide.

**Solutions**:
1. Use `pip install --user -r requirements.txt`
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

---

### Configuration Issues

#### "Config file not found"

**Problem**: DPAssist can't find `config.yaml`.

**Solutions**:
1. Make sure you're in the DPAssist directory when running `python main.py`
2. Check that you created `config.yaml` (not still using `config.example.yaml`)
3. Run: `pwd` (Mac/Linux) or `cd` (Windows) to verify your location

#### "Missing required config field"

**Problem**: Something is blank in your config file.

**Solutions**:
1. Open `config.yaml` in a text editor
2. Look for any fields that say `YOUR_XXX_HERE` and fill them in
3. Make sure you didn't accidentally delete any fields
4. Compare with `config.example.yaml` to see what's missing

#### "Invalid YAML format"

**Problem**: Syntax error in config file.

**Solutions**:
1. YAML is picky about indentation - use spaces, not tabs
2. Make sure colons have a space after them: `key: value` not `key:value`
3. Check for stray quotes or special characters
4. Use a YAML validator online: https://www.yamllint.com/

---

### Google Cloud Issues

#### "Could not connect to Google Sheets"

**Symptoms**: Error when trying to access your spreadsheet.

**Solutions**:

1. **Check the spreadsheet name**:
   - Open your Google Sheet
   - Copy the exact name (case-sensitive!)
   - Paste it into `config.yaml` under `spreadsheet_name`

2. **Verify service account sharing**:
   - Open `service-account-credentials.json`
   - Find the `client_email` (looks like `xxx@project-name.iam.gserviceaccount.com`)
   - Go to your Google Sheet → Share
   - Make sure that email has "Editor" access
   - Click "Share" (don't just add it without clicking)

3. **Check API enablement**:
   - Go to https://console.cloud.google.com/
   - Search for "Google Sheets API" → Make sure it's ENABLED
   - Search for "Google Drive API" → Make sure it's ENABLED

4. **Verify credentials file**:
   - Make sure `service-account-credentials.json` is in your DPAssist folder
   - Check that the path in `config.yaml` matches the actual filename
   - The file should start with `{` and contain JSON data

#### "Authentication failed" or "Invalid credentials"

**Solutions**:
1. Download a fresh service account key from Google Cloud Console
2. Make sure you're using a service account key (not an API key)
3. Check that the service account has the right permissions

---

### Gemini AI Issues

#### "Invalid API key"

**Symptoms**: Can't connect to Gemini API.

**Solutions**:
1. Go to https://aistudio.google.com/apikey
2. Generate a new API key
3. Copy it **exactly** (no extra spaces)
4. Paste into `config.yaml` under `gemini.api_key`
5. Make sure there are no quotes around it unless they were there originally

#### "Quota exceeded" or "Rate limit"

**Symptoms**: Error about too many requests.

**Solutions**:
1. Check your Gemini API limits at https://ai.google.dev/pricing
2. Reduce `check_interval` in config to process submissions less frequently
3. Consider upgrading to a paid tier if needed
4. Wait a few minutes and try again

#### "Model not found"

**Solutions**:
1. Check available models at https://ai.google.dev/models
2. Update `config.yaml` with a valid model name
3. Try `gemini-2.0-flash-exp` as a default

---

### Email Issues

#### Gmail "Authentication failed"

**Symptoms**: Can't send emails via Gmail.

**Solutions**:

1. **Make sure 2-Factor Authentication is ON**:
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google" → "2-Step Verification"
   - Turn it on if it's off

2. **Create an App Password (NOT your regular password)**:
   - Go to https://myaccount.google.com/apppasswords
   - Create a new app password for "Mail" / "Other"
   - Copy the 16-character code
   - Use THIS in config.yaml, not your regular Gmail password

3. **Check for typos**:
   - App password should be exactly 16 characters
   - No spaces (some guides show spaces, remove them)
   - Format: `abcdabcdabcdabcd`

4. **"Less secure app access"**:
   - Google is phasing this out - you MUST use an App Password now
   - If you see this error, you're using your regular password (wrong!)

#### Outlook "Authentication failed"

**Solutions**:
1. Check that your Outlook password is correct
2. For Microsoft 365, you may need an app password
3. Try setting `smtp_server: smtp-mail.outlook.com` and `smtp_port: 587`

#### "Could not create draft"

**Symptoms**: Email sends but can't create drafts.

**Solutions**:
1. For Gmail: Check IMAP is enabled in Gmail settings
2. For Outlook: Similar IMAP check
3. For generic SMTP: Drafts will be saved as files in `email_drafts/` folder

---

### Selenium / Chrome Issues

#### "ChromeDriver not found"

**Symptoms**: Error about Chrome or ChromeDriver.

**Solutions**:
1. Make sure Google Chrome is installed on your computer
2. The program should auto-download ChromeDriver
3. If it doesn't work, manually download from https://chromedriver.chromium.org/
4. Put it in your DPAssist folder or system PATH

#### "Timeout" or "Page took too long to load"

**Solutions**:
1. Increase timeout in `config.yaml`: `agents.link_validator.timeout: 60`
2. Check your internet connection
3. Try the portfolio URL in your own browser to verify it works
4. Some digital portfolios are just slow - this is normal

#### "Permission denied" on Chrome binary

**Solutions**:
- Mac: `chmod +x /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome`
- Linux: Install Chrome via package manager: `sudo apt install google-chrome-stable`

---

### Runtime Issues

#### "No pending submissions found" but there ARE submissions

**Problem**: System isn't detecting new submissions.

**Solutions**:
1. Check the "Status" column in your sheet
2. Clear any old statuses for rows you want to reprocess
3. Make sure timestamp is newer than last processing
4. Try setting Status to "Pending" manually
5. Restart the program: Ctrl+C, then `python main.py` again

#### Program stops with no error

**Solutions**:
1. Check the log files in the `logs/` folder
2. Look for the most recent `.log` file
3. Find the last few lines for the actual error
4. Look up that specific error in this guide

#### "Processed too many times" or loop

**Problem**: Same submission keeps processing.

**Solutions**:
1. Check your deadline settings
2. Make sure submissions aren't being resubmitted continuously
3. Check the Google Form isn't set to allow multiple submissions per person unexpectedly

---

### Performance Issues

#### System is very slow

**Solutions**:
1. Increase `check_interval` to check less frequently
2. Reduce `max_submissions_per_run`
3. Consider running on a more powerful computer or server
4. Check if Gemini API is slow (try a different model)

#### Taking up too much disk space

**Solutions**:
1. Log files can get big - delete old logs in `logs/`
2. Set `logging.retention_days` in config
3. Screenshots aren't saved by default, but check anyway

---

### Permission / Access Issues

#### "Permission denied" reading files

**Solutions**:
1. Check file permissions: `ls -la` (Mac/Linux)
2. Make sure files aren't locked/in use by another program
3. On Windows: Run Command Prompt as Administrator

#### Student can't access their feedback

**Solutions**:
1. Check spam/junk folder
2. Verify student email is correct in sheet
3. Check email was actually sent (look in your Sent folder)
4. Try a test email to yourself

---

### Sheet Column Issues

#### "Could not auto-detect required columns"

**Problem**: Your sheet column names don't match expected patterns.

**Solutions**:
1. Required columns must contain these keywords:
   - Timestamp: "timestamp", "date", "time", or "submitted"
   - Email: "email", "e-mail", or "mail"  
   - Portfolio Link: "portfolio", "link", "url", "site", or "website"

2. Rename your columns to include these words
3. Example good names:
   - "Submission Timestamp" ✓
   - "Student Email" ✓
   - "Portfolio URL" ✓

---

### Other Issues

#### "Import error" or "Module not found"

**Solutions**:
1. Run: `pip install -r requirements.txt` again
2. Make sure you're in the right directory
3. Check you're using the same Python that has the packages:
   ```bash
   which python  # or 'where python' on Windows
   python -m pip install -r requirements.txt
   ```

#### Program won't stop with Ctrl+C

**Solutions**:
1. Press Ctrl+C multiple times
2. Force quit: Ctrl+Z then `kill %1` (Mac/Linux)
3. Close terminal window
4. Worst case: Restart computer

---

## Getting More Help

### Check the Logs

Always look at the log files first:

```bash
cd logs
ls -lt  # Shows newest first
tail -100 dpassist_YYYYMMDD.log  # Last 100 lines
```

### Enable Debug Logging

In `config.yaml`:
```yaml
logging:
  level: "DEBUG"  # Change from INFO to DEBUG
```

This gives much more detailed information.

### Run the Validator

```bash
python validate_setup.py
```

This checks your setup and identifies problems.

### Test Individual Agents

You can test each agent separately:

```bash
python agent_timeliness.py      # Test timeliness checking
python agent_link_validator.py  # Test link validation
python agent_caption_analyzer.py  # Test AI caption analysis
```

### Still Stuck?

1. **GitHub Issues**: Post your problem with:
   - Error message (full text)
   - What you were trying to do
   - Your operating system
   - Python version (`python --version`)
   - Relevant parts of config (WITHOUT secrets!)

2. **Include logs**: Copy the last 50 lines from your log file

3. **Be patient**: Volunteers help when they can!

---

## Prevention Tips

### Before First Run

1. ✓ Run `python validate_setup.py`
2. ✓ Test with one dummy submission first
3. ✓ Check all emails are working
4. ✓ Verify Google Sheet access

### Regular Maintenance

1. Check logs weekly for errors
2. Keep Python and packages updated
3. Rotate/clear old logs monthly
4. Back up your Google Sheet
5. Keep API keys secure

### When Making Changes

1. Stop the program first (Ctrl+C)
2. Edit configuration
3. Test new settings
4. Restart program

---

## Emergency: Need to Stop Everything

If something goes wrong and you need to stop immediately:

1. **Press Ctrl+C** in the terminal
2. If that doesn't work, **close the terminal window**
3. Check running processes:
   - Mac/Linux: `ps aux | grep main.py` then `kill <pid>`
   - Windows: Open Task Manager, find Python, End Task

4. **Pause processing**: In Google Sheet, add a column "Status" and set all to "Complete" temporarily

---

**Remember**: When in doubt, check the logs! They usually tell you exactly what went wrong.
