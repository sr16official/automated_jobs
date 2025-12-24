# 🤖 AI Job Agent

An intelligent, automated job application assistant that discovers, ranks, and helps you apply to relevant job opportunities across multiple platforms.

![Dashboard Preview](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🔍 Multi-Source Job Discovery
- **RSS Feed Integration**: Parse LinkedIn job feeds directly
- **Firecrawl v1 Web Scraping**: Advanced scraping with anti-bot bypass for Greenhouse, Naukri, Wellfound, and more
- **Modular Scraper Architecture**: Easy to add new job boards

### 🎯 AI-Powered Job Ranking
- **Smart Matching**: Uses LLM to score jobs based on your profile
- **Personalized Scoring**: Matches against your skills, experience, and preferences
- **Detailed Explanations**: Get reasons why each job is a good fit

### 📧 Automated Email Outreach
- **Smart Contact Extraction**: Uses Firecrawl to bypass anti-bot measures and find recruiter emails
- **Fallback Email Generation**: Automatically generates likely HR emails (careers@, jobs@, etc.) when contacts aren't found
- **AI-Generated Emails**: Personalized cover letters for each application
- **Gmail Integration**: Creates drafts directly in your Gmail account
- **Resume Attachment**: Automatically attaches your resume to emails


### 📊 Real-Time Dashboard
- **Live Monitoring**: Track agent progress in real-time
- **Job Pipeline**: View all discovered jobs with scores and status
- **Statistics**: See jobs found, contacts scraped, and emails drafted
- **Beautiful UI**: Dark-themed, animated interface with cyan accents

## 🏗️ Architecture

```
ai-job-agent/
├── agents/              # Core agent modules
│   ├── job_search_agent.py
│   ├── job_ranking_agent.py
│   ├── contact_extraction_agent.py
│   ├── email_automation_agent.py
│   └── scrapers/        # Modular job board scrapers
│       ├── rss_scraper.py
│       ├── greenhouse_scraper.py
│       ├── linkedin_scraper.py
│       ├── naukri_scraper.py
│       └── wellfound_scraper.py
├── api/                 # FastAPI backend
│   └── main.py
├── frontend/            # Web dashboard
│   ├── index.html
│   └── app.js
├── utils/               # Helper utilities
│   ├── firecrawl_client.py
│   ├── gmail_client.py
│   ├── llm_client.py
│   └── helpers.py
└── config/              # Configuration files
    ├── llm_config.py
    └── user_profile.json
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Cloud account (for Gmail API)
- Firecrawl API key (for web scraping with anti-bot bypass)
- OpenRouter API key (for LLM)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sr16official/automated_jobs.git
cd automated_jobs/ai-job-agent
```

2. **Install dependencies**
```bash
python3 -m pip install -r requirements.txt
```

This will install:
- `firecrawl-py` - Official Firecrawl v1 SDK for web scraping
- `beautifulsoup4` - HTML parsing
- `openai` - LLM client
- `google-api-python-client` - Gmail integration
- `fastapi` & `uvicorn` - Web dashboard backend

3. **Set up environment variables**

Create a `.env` file in the `ai-job-agent` directory:
```bash
# Firecrawl Configuration (optional)
FIRECRAWL_API_KEY=your_firecrawl_api_key

# LLM Configuration (required)
XIAOMI_API_KEY=your_openrouter_api_key
XIAOMI_BASE_URL=https://openrouter.ai/api/v1

# Optional
PYTHONPATH=.
```

4. **Configure your profile**

Edit `config/user_profile.json` with your information:
```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "skills": ["Python", "JavaScript", "React"],
  "experience_years": 3,
  "preferred_roles": ["Software Engineer", "Full Stack Developer"],
  "preferred_locations": ["Remote", "San Francisco"],
  "resume_path": "path/to/your/resume.pdf"
}
```

5. **Set up Gmail API** (for email automation)

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable Gmail API
- Create OAuth 2.0 credentials (Desktop App)
- Download `credentials.json` and place it in `config/`
- Run the setup script:
```bash
python3 scripts/setup_gmail.py
```

### Running the Agent

**Start the dashboard:**
```bash
python3 api/main.py
```

**Open your browser:**
```
http://localhost:8000
```

## 📖 Usage Guide

### 1. Launch a Job Search

1. Enter your desired **Role** (e.g., "Software Engineer")
2. Enter your **Location** (e.g., "Remote", "Bangalore")
3. (Optional) Paste a **LinkedIn RSS Feed URL**
4. (Optional) Upload your **Resume**
5. Click **"🚀 Run Agent"**

### 2. Monitor Progress

Watch the **Agent Monitoring** panel for real-time updates:
- Initializing Database
- Searching for jobs
- Ranking jobs
- Extracting contacts
- Drafting emails

### 3. Review Results

The **Job Pipeline** shows all discovered jobs with:
- **Match Score** (color-coded: green = excellent, yellow = good, red = poor)
- **Status** (New, Shortlisted, Email Drafted)
- **Contact Found** badge if recruiter email was extracted
- **Match Reasons** explaining why the job fits your profile

### 4. Check Your Gmail

Email drafts are automatically created in your Gmail account. Review and send them manually!

## 🔧 Configuration

### Supported Job Boards

- **LinkedIn** (via RSS feed)
- **Greenhouse.io**
- **Naukri.com**
- **Wellfound** (formerly AngelList)
- Easy to add more via modular scrapers

### LLM Models

The agent uses OpenRouter for AI features. Supported models:
- `google/gemini-2.0-flash-exp:free` (default)
- Any OpenAI-compatible model

Configure in `config/llm_config.py`

## 📊 Dashboard Features

### Statistics Cards
- **Jobs Found**: Total jobs discovered
- **Contacts Scraped**: Recruiter emails extracted
- **Emails Drafted**: Gmail drafts created

### Job Pipeline
- Filter by status (All, Shortlisted, Email Drafted, Unscored)
- Color-coded match scores
- Direct links to job postings
- AI-generated match explanations

### Agent Monitoring
- Real-time progress bar
- Activity log with timestamps
- Current step indicator

## 🔐 Security & Privacy

- **No Auto-Sending**: Emails are created as drafts, never sent automatically
- **Local Storage**: All data stored in local SQLite database
- **Secure Credentials**: API keys and tokens excluded from Git via `.gitignore`
- **OAuth2**: Secure Gmail authentication via Google

## 🛠️ Development

### Adding a New Job Board Scraper

1. Create a new scraper in `agents/scrapers/`:
```python
from agents.scrapers.base_scraper import BaseScraper

class MyJobBoardScraper(BaseScraper):
    def can_handle(self, url: str) -> bool:
        return "myjobboard.com" in url
    
    def parse(self, html: str, source_url: str) -> list:
        # Parse jobs from HTML
        return jobs
```

2. Register it in `agents/scrapers/__init__.py`
3. Add to `JobSearchAgent` scrapers list

### Running Tests

```bash
python3 test_ranking_llm.py
python3 test_gmail_client.py
```

## 📝 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions for:
- Local setup
- Cloud hosting (Render, Railway)
- Docker deployment
- Production environment variables

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Firecrawl** for web scraping capabilities
- **OpenRouter** for LLM API access
- **Google** for Gmail API
- **FastAPI** for the backend framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for job seekers everywhere**
