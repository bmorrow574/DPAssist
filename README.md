# DPAssist

**AI-Powered Digital Portfolio Feedback System for Educators**

DPAssist is an intelligent, multi-agent system that automatically evaluates student digital portfolios (Google Sites, GitHub Pages, etc.) and provides immediate, personalized feedback. Perfect for STEM and Computer Science teachers managing large classes.

---

## Key Features

### Automated Evaluation
- **Link Validation**: Ensures portfolio URLs are accessible
- **Media Checking**: Verifies all images and videos load correctly
- **Caption Analysis**: AI evaluates caption quality and relevance
- **Timeliness Tracking**: Automatically detects late submissions

### Smart Feedback System
- **Before Deadline**: Students receive immediate feedback and can resubmit unlimited times
- **After Deadline**: Creates draft emails for teacher review before final grading
- **AI-Powered**: Uses Google's Gemini AI to generate personalized, constructive feedback
- **Rubric-Based**: Incorporates your custom rubric into evaluations

### Continuous Operation
- **Always Running**: Monitors submissions 24/7 (configurable interval)
- **Automatic Processing**: No manual "Run" button needed
- **Error Handling**: Gracefully handles failures and retries
- **Scalable**: Processes multiple students efficiently

### Multi-Platform Support
- **Email Providers**: Gmail, Outlook, or any SMTP server
- **Flexible Deployment**: Run locally, on a server, or in the cloud
- **Universal Format**: Works with Google Sites, GitHub Pages, or any web-based portfolio

---

## Architecture

DPAssist uses a **multi-agent architecture** where specialized AI agents work together:

```
┌─────────────────────────────────────────────────────────┐
│                 SUBMISSION MONITOR AGENT                 │
│           (Watches Google Sheet for new work)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   TIMELINESS AGENT         │
        │   (Checks deadline)        │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   LINK VALIDATOR AGENT     │
        │   (Tests portfolio access) │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   MEDIA CHECKER AGENT      │
        │   (Verifies media loads)   │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   CAPTION ANALYZER AGENT   │
        │   (AI evaluates captions)  │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  FEEDBACK GENERATOR AGENT  │
        │  (Creates personalized     │
        │   feedback with AI)        │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   EMAIL DRAFTER AGENT      │
        │   (Sends or drafts email)  │
        └────────────────────────────┘
```

Each agent is independent, testable, and can be configured separately.

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Cloud account (for Sheets access)
- Gemini API key (free tier available)
- Gmail/Outlook account for emails

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bmorrow574/DPAssist.git
   cd DPAssist
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your credentials
   ```

4. **Run DPAssist**
   ```bash
   python main.py
   ```

**That's it!** The system will now continuously monitor your Google Sheet and process submissions automatically.

**For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

---

## Configuration

All settings are in `config.yaml`:

```yaml
google_sheets:
  spreadsheet_name: "Student Portfolio Submissions"
  service_account_file: "service-account-credentials.json"
  check_interval: 300  # Check every 5 minutes

deadline:
  datetime: "2026-02-15 23:59"
  timezone: "America/New_York"

gemini:
  api_key: "YOUR_API_KEY_HERE"
  model: "gemini-2.0-flash-exp"

email:
  provider: "gmail"  # or "outlook", "smtp"
  teacher_email: "teacher@school.edu"
  gmail:
    app_password: "YOUR_APP_PASSWORD"

rubric:
  file_path: "rubric.pdf"  # Optional
```

See `config.example.yaml` for all available options.

---

## Google Sheet Format

Your Google Sheet should have these columns (names detected automatically):

| Timestamp | Email | First Name | Last Name | Portfolio Link | Unit/Project |
|-----------|-------|------------|-----------|----------------|--------------|
| 2/1/2026 10:30 | student@email.com | Jane | Doe | https://sites.google.com/... | Unit 3 |

DPAssist automatically adds these columns:
- **Status**: Current processing status
- **Timeliness**: On time or late
- **Link Status**: Link validation result
- **Media Status**: Media check result
- **Caption Status**: AI caption analysis
- **Feedback Sent**: When feedback was sent/drafted
- **Last Processed**: Timestamp of last processing

---

## How It Works

### Before the Deadline

1. Student submits portfolio via Google Form
2. DPAssist detects new submission (within 5 minutes)
3. All agents evaluate the portfolio
4. Student receives immediate feedback via email
5. Student can fix issues and resubmit
6. Process repeats for each resubmission

### After the Deadline

1. Same evaluation process occurs
2. Instead of sending to student, creates **draft email** for teacher
3. Teacher reviews draft in their email client
4. Teacher can edit, then send manually
5. Final grade and feedback are recorded

---

## For Teachers

### What Teachers Need to Know

- **No coding required** - Just configure `config.yaml`
- **Runs automatically** - Set it and forget it
- **Students get instant feedback** - Encourages iteration
- **You maintain control** - Review all final grades
- **Scales easily** - Handles classes of any size

### Common Use Cases

- **Digital Portfolios**: Google Sites, Wix, WordPress
- **GitHub Projects**: GitHub Pages websites
- **Web Development**: HTML/CSS/JS projects
- **Multimedia Projects**: Video, image, and text portfolios

### Customization

- Adjust AI feedback tone in prompts
- Modify email templates
- Change evaluation strictness
- Add custom rubric criteria
- Set specific caption requirements

---

## Project Structure

```
DPAssist/
├── main.py                      # Main orchestrator
├── utils.py                     # Shared utilities
├── config.yaml                  # Your configuration (don't commit!)
├── config.example.yaml          # Template configuration
├── requirements.txt             # Python dependencies
├── service-account-credentials.json  # Google Cloud key (don't commit!)
│
├── agent_submission_monitor.py  # Monitors Google Sheet
├── agent_timeliness.py          # Checks submission timing
├── agent_link_validator.py      # Validates portfolio URLs
├── agent_media_checker.py       # Checks media accessibility
├── agent_caption_analyzer.py    # AI caption analysis
├── agent_feedback_generator.py  # Generates feedback
├── agent_email_drafter.py       # Handles email operations
│
├── logs/                        # Application logs
├── email_drafts/                # Saved drafts (SMTP mode)
│
├── README.md                    # This file
├── SETUP_GUIDE.md              # Detailed setup instructions
├── ARCHITECTURE.md             # Technical architecture
└── .gitignore                  # Git ignore file
```

---

## Advanced Features

### Running as a Service

**Linux (systemd)**:
```bash
# See deployment/dpassist.service
sudo systemctl enable dpassist
sudo systemctl start dpassist
```

**Windows**:
Use Task Scheduler to run on startup

**Docker**:
```bash
docker build -t dpassist .
docker run -d --name dpassist dpassist
```

### Cloud Deployment

- **Google Cloud Run**: Serverless, scales automatically
- **AWS EC2**: Traditional VM
- **Heroku**: Simple deployment
- **Railway**: Modern platform

### Monitoring

- Logs stored in `logs/` directory
- Check status: `tail -f logs/dpassist_YYYYMMDD.log`
- Email notifications on critical errors (configurable)

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/bmorrow574/DPAssist.git
cd DPAssist

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black flake8  # Testing and linting

# Run tests
pytest

# Format code
black .
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with Google's Gemini AI for intelligent feedback
- Uses Selenium for web automation
- Inspired by the need for scalable, personalized education

---

## Support

- **Documentation**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/bmorrow574/DPAssist/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bmorrow574/DPAssist/discussions)

---

## Roadmap

- [ ] Web-based dashboard for monitoring
- [ ] Support for more portfolio platforms (Notion, Behance)
- [ ] Integration with Learning Management Systems (Canvas, Schoology)
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app for teachers
- [ ] Plagiarism detection
- [ ] Peer review workflows

---

## Star History

If you find DPAssist useful, please star the repository! It helps other educators discover the project.

---

**Made with care by teachers, for teachers**

*DPAssist: Because every student deserves timely, personalized feedback.*
