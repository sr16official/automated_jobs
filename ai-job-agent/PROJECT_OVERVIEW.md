# Project Overview: AI Job Agent (v2)

The AI Job Agent is an automated system for searching, ranking, and applying for jobs. It now supports multiple job boards and uses Firecrawl for intelligent job discovery.

## Project Structure

```text
ai-job-agent/
├── agents/                 
│   ├── scrapers/           # Board-specific parsers [NEW]
│   │   ├── base_scraper.py
│   │   ├── greenhouse_scraper.py
│   │   ├── linkedin_scraper.py
│   │   ├── naukri_scraper.py
│   │   ├── wellfound_scraper.py
│   │   └── rss_scraper.py      # RSS feed parser [NEW]
│   ├── contact_extraction_agent.py
│   ├── email_automation_agent.py
│   ├── job_ranking_agent.py
│   └── job_search_agent.py # Refactored for modular search
├── config/                 
│   ├── llm_config.py
│   └── user_profile.json
├── db/                     
│   └── jobs.db             
├── scripts/                # Helper scripts [NEW]
│   └── setup_gmail.py      # Initialize Google Auth
├── utils/                  
│   ├── firecrawl_client.py # Discovery & scraping engine [NEW]
│   ├── gmail_client.py
│   ├── helpers.py
│   └── llm_client.py
├── main.py                 
└── PROJECT_OVERVIEW.md     
```

---

## Component Breakdown

### 1. Unified Search Architecture
- **Firecrawl Client**: The core engine for discovering job URLs and bypass anti-bot gates on sites like LinkedIn and Wellfound.
- **Modular Scrapers**: A set of specialized parsers that handle the unique HTML/JSON structures of different job boards:
  - `GreenhouseScraper`, `NaukriScraper`, `LinkedInScraper`, `WellfoundScraper`.
- **Job Search Agent**: Coordinates the discovery process using Firecrawl and routes results to the correct scraper. Now supports filtering by `role` and `location`.

### 2. Agents & Intelligence
- **Job Ranking Agent**: Scores matches using the Xiaomi MiMo-V2-Flash LLM based on `user_profile.json`.
- **Contact Extraction Agent**: Extracts recruiter emails from job pages.
- **Email Automation Agent**: Drafts personalized cold emails in Gmail.

### 3. Utilities & Config
- **Gmail Client**: Handles OAuth2 and draft creation.
- **LLM Client**: OpenAI-compatible client for Xiaomi API.
- **Helpers**: Manages SQLite database and initialization.

---

## Getting Started

1. **Setup Credentials**:
   - Place `credentials.json` from Google Cloud Console in the `config/` directory.
   - Set `FIRECRAWL_API_KEY` and `XIAOMI_API_KEY` in your environment.
2. **Initialize Auth**:
   - Run `python scripts/setup_gmail.py` to generate `token.json`.
3. **Run Search**:
   - Edit `main.py` with your desired `role` and `location`.
   - Run `python main.py`.

---

## How to Suggest Structural Changes

We've moved to a modular scraper pattern. To add a new board:
1. Create a new scraper class in `agents/scrapers/`.
2. Inherit from `BaseScraper`.
3. Update `JobSearchAgent` to include the new scraper.
