# Working with PortfoliOS: Development & GitHub Guide

## About Iterative Development with AI

You mentioned hearing about "a feature of Claude that will constantly work on code until it works." Let me clarify what's available:

### Claude Code

**Claude Code** is Anthropic's command-line tool that allows you to delegate coding tasks to Claude AI directly from your terminal. Here's what it can do:

- **Iterative problem solving**: Claude Code can work through problems step-by-step
- **Autonomous agent**: It can run tests, fix errors, and iterate on solutions
- **Terminal integration**: Works directly in your development environment
- **File editing**: Can read and modify files as needed

However, it's important to understand:
- It's not "constantly running" in the background - you initiate tasks
- It's designed for developers with some coding experience
- It requires you to guide it and verify changes
- Best used for specific tasks, not full application monitoring

### Using Claude Code with PortfoliOS

If you want to use Claude Code to help develop PortfoliOS:

```bash
# Install Claude Code (requires Anthropic API access)
npm install -g @anthropic-ai/claude-code

# Use it to help with development tasks
claude-code "Fix the email sending function to handle timeouts better"
claude-code "Add a new configuration option for custom email templates"
```

**However**, for non-programmers, the regular chat interface with Claude (like this one) is actually better suited for getting help and understanding code.

---

## Connecting VS Code to GitHub

Here's how to set up VS Code with GitHub for sharing PortfoliOS:

### Step 1: Install VS Code

1. Download from https://code.visualstudio.com/
2. Install it on your computer
3. Open VS Code

### Step 2: Install Git

**Windows:**
1. Download Git from https://git-scm.com/download/win
2. Run the installer (keep default settings)
3. Restart VS Code

**Mac:**
- Git is usually pre-installed
- If not: Install via Homebrew: `brew install git`

**Linux:**
```bash
sudo apt-get install git  # Ubuntu/Debian
```

### Step 3: Configure Git

Open VS Code Terminal (View → Terminal) and run:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 4: Create GitHub Account

1. Go to https://github.com
2. Sign up for a free account
3. Verify your email

### Step 5: Connect VS Code to GitHub

1. In VS Code, click the Account icon (bottom left)
2. Click "Sign in to Sync Settings"
3. Choose "Sign in with GitHub"
4. Follow the browser prompts
5. Authorize VS Code

### Step 6: Create a GitHub Repository

**Option A: Via GitHub Website** (Easier)

1. Go to https://github.com
2. Click the "+" icon (top right) → "New repository"
3. Name it "PortfoliOS"
4. **IMPORTANT**: Check "Add a README file"
5. **IMPORTANT**: Add .gitignore template → Choose "Python"
6. Choose a license (MIT License is good for education)
7. Click "Create repository"

**Option B: Via VS Code**

1. Open your PortfoliOS folder in VS Code (File → Open Folder)
2. Click Source Control icon (left sidebar, looks like branches)
3. Click "Publish to GitHub"
4. Choose "Publish to GitHub public repository" or private
5. Select which files to include
6. Click "OK"

### Step 7: Initial Commit

1. In VS Code, open your PortfoliOS folder
2. Open Source Control (Ctrl+Shift+G or Cmd+Shift+G)
3. You'll see all changed files
4. **IMPORTANT**: Make sure `config.yaml` and `service-account-credentials.json` are NOT listed
   - If they are, they should be grayed out (due to .gitignore)
   - If not grayed out, add them to .gitignore NOW
5. Type a commit message: "Initial commit of PortfoliOS"
6. Click the checkmark (✓) to commit
7. Click "..." → "Push" to send to GitHub

---

## What to Commit vs What to Keep Private

### ✅ DO Commit (Safe to share):

- All `.py` files (your code)
- `requirements.txt`
- `config.example.yaml` (the template)
- `README.md`
- `SETUP_GUIDE.md`
- `.gitignore`
- Documentation files
- Empty `logs/` folder structure

### ❌ DON'T Commit (Keep Private):

- `config.yaml` (has your secrets!)
- `service-account-credentials.json` (Google Cloud key)
- `*.json` (any JSON files with credentials)
- `logs/*.log` (may contain student data)
- `email_drafts/` (contains draft emails)
- Screenshots (may contain student info)

**The `.gitignore` file already handles this**, but double-check!

---

## Sharing Your Repository

### Making it Public

1. Go to your GitHub repository
2. Click "Settings"
3. Scroll down to "Danger Zone"
4. Click "Change visibility"
5. Choose "Make public"
6. Confirm

### Writing a Good README for Others

Your README should include:

1. **What it does**: Brief description
2. **Who it's for**: "For educators managing digital portfolios"
3. **What you need**: Prerequisites
4. **How to set up**: Link to SETUP_GUIDE.md
5. **How to use**: Basic usage
6. **How to get help**: Where to ask questions
7. **License**: So others know they can use it

The README.md I created covers all of this!

### Helping Others Use It

1. **Releases**: Create releases for stable versions
   - Go to repository → Releases → "Create a new release"
   - Tag version (e.g., v1.0.0)
   - Add release notes (what changed)

2. **Issues**: Enable GitHub Issues
   - Others can report bugs or ask questions
   - You can respond when you have time

3. **Discussions**: Enable GitHub Discussions
   - Better for general questions
   - Community can help each other

---

## Keeping Your Version Updated

### Pulling Changes from GitHub

If you work on multiple computers:

```bash
git pull origin main
```

This downloads the latest version.

### Making Changes

1. Edit files in VS Code
2. Save changes
3. Open Source Control (Ctrl+Shift+G)
4. Review changes
5. Type commit message
6. Click checkmark to commit
7. Click "..." → "Push" to upload

### Creating Branches (Advanced)

For experimental features:

```bash
git checkout -b new-feature
# Make changes
git commit -m "Add new feature"
git push origin new-feature
```

Then create a Pull Request on GitHub to merge.

---

## Collaborating with Others

### Allowing Contributors

1. Go to repository → Settings → Collaborators
2. Click "Add people"
3. Enter their GitHub username
4. They can now contribute directly

### Accepting Contributions

When someone submits improvements:

1. They fork your repository
2. Make changes in their fork
3. Submit a "Pull Request"
4. You review the changes
5. If good, click "Merge"

---

## Version Control Best Practices

### Commit Often

- Commit after each working feature
- Use clear commit messages:
  - ✓ "Add email validation to link checker"
  - ✓ "Fix crash when portfolio has no images"
  - ✗ "update stuff"
  - ✗ "fixed it"

### Use Meaningful Branch Names

- `main` - stable, working code
- `develop` - next version in progress
- `feature/deadline-warnings` - specific features
- `bugfix/email-timeout` - bug fixes

### Tag Releases

```bash
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

Users can then download specific versions.

---

## Continuous Integration (Advanced)

You can set up GitHub Actions to:
- Run tests automatically
- Check code quality
- Deploy to a server

Example `.github/workflows/test.yml`:

```yaml
name: Test PortfoliOS

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run validator
      run: |
        python validate_setup.py
```

---

## Getting Help with Git/GitHub

### Common Git Commands

```bash
# Check status
git status

# See what changed
git diff

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD
```

### GUI Tools (Easier than Command Line)

- **GitHub Desktop**: https://desktop.github.com/
- **GitKraken**: https://www.gitkraken.com/
- **VS Code**: Built-in Git support is excellent

### Learning Resources

- **GitHub Guides**: https://guides.github.com/
- **Git Basics**: https://git-scm.com/book/en/v2/Getting-Started-Git-Basics
- **VS Code Git**: https://code.visualstudio.com/docs/editor/versioncontrol

---

## For Non-Programmers: Simplified Workflow

If Git seems overwhelming, here's the absolute minimum:

1. **Make changes** in VS Code
2. **Source Control panel** → See what changed
3. **Type a message** describing what you did
4. **Click checkmark** (commits)
5. **Click sync icon** (pushes to GitHub)

That's it! You're now backing up your work and sharing with others.

---

## About "Constantly Working" Systems

You asked about having this "constantly work." Here's what that means:

### What We Built

PortfoliOS IS designed to run constantly:
- Checks for submissions every 5 minutes
- Processes them automatically
- Sends feedback without human intervention
- Runs 24/7 if you keep it running

### What You Control

- When to start/stop the program
- Configuration changes (edit config.yaml, restart)
- Reviewing teacher drafts before sending
- Handling errors if they occur

### Monitoring

To check if it's working:

1. **Logs**: Check `logs/` folder regularly
2. **Google Sheet**: Status column shows progress
3. **Email**: You'll see drafts being created
4. **Terminal**: Keeps printing status messages

---

## Summary

1. **VS Code + GitHub**: Great for version control and sharing
2. **Claude Code**: For developers, not needed for basic use
3. **Continuous operation**: PortfoliOS already does this!
4. **Not fully autonomous**: You still monitor and configure

The system you have is actually MORE automated than what most "constantly working" tools provide, because it:
- Monitors submissions automatically
- Processes without human trigger
- Sends feedback automatically (before deadline)
- Runs indefinitely once started

The only things you do manually:
- Start/stop the program
- Review final grades (after deadline)
- Fix configuration issues if they arise

**This is the right level of automation for education!** You maintain oversight while saving enormous amounts of time.
