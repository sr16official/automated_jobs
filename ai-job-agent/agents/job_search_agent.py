import requests
from bs4 import BeautifulSoup
import logging
from utils.helpers import get_db_connection

import logging
from utils.helpers import get_db_connection
from utils.firecrawl_client import FirecrawlClient
from agents.scrapers import GreenhouseScraper, NaukriScraper, LinkedInScraper, WellfoundScraper, RSSScraper
import requests

class JobSearchAgent:
    """
    Agent responsible for finding jobs across multiple platforms.
    Uses Firecrawl for discovery and modular scrapers for parsing.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("JobSearchAgent")
        self.firecrawl = FirecrawlClient()
        self.scrapers = [
            GreenhouseScraper(),
            NaukriScraper(),
            LinkedInScraper(),
            WellfoundScraper(),
            RSSScraper()
        ]

    def fetch_from_rss(self, rss_url: str):
        """
        Fetches jobs directly from an RSS feed URL.
        """
        self.logger.info(f"Fetching jobs from RSS feed: {rss_url}")
        try:
            response = requests.get(rss_url, timeout=15)
            response.raise_for_status()
            
            scraper = RSSScraper()
            jobs = scraper.parse(response.text, rss_url)
            
            self.logger.info(f"Found {len(jobs)} jobs in RSS feed.")
            self.save_jobs(jobs)
            return jobs
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS: {e}")
            return []

    def search_and_scrape(self, role: str, location: str, rss_url: str = None):
        """
        Orchestrates discovery and scraping of jobs.
        """
        all_jobs = []
        
        # Priority 1: RSS Feed (most reliable)
        if rss_url:
            self.logger.info("Using RSS feed as primary source")
            rss_jobs = self.fetch_from_rss(rss_url)
            all_jobs.extend(rss_jobs)
            
            # If RSS feed worked, we might not need Firecrawl
            if len(all_jobs) > 0:
                self.logger.info(f"Found {len(all_jobs)} jobs from RSS feed. Skipping Firecrawl search.")
                return
        
        # Priority 2: Try Firecrawl search
        platforms = ["greenhouse.io", "naukri.com", "linkedin.com/jobs", "wellfound.com"]
        self.logger.info(f"Starting Firecrawl search for '{role}' in '{location}'...")
        
        urls = self.firecrawl.search_jobs(role, location, platforms)
        
        if urls and len(urls) > 0:
            self.logger.info(f"Firecrawl found {len(urls)} URLs")
            for url in urls:
                scraper = next((s for s in self.scrapers if s.can_handle(url)), None)
                
                if scraper:
                    html = self.firecrawl.scrape_url(url)
                    if html:
                        jobs = scraper.parse(html, url)
                        for job in jobs:
                            job['source_platform'] = scraper.__class__.__name__.replace("Scraper", "")
                            all_jobs.append(job)
                else:
                    self.logger.info(f"No specific scraper for {url}, skipping.")
            
            self.save_jobs(all_jobs)
        else:
            # Priority 3: Fallback to direct URLs if Firecrawl fails
            self.logger.warning("Firecrawl search returned no results. Using fallback direct URLs...")
            
            # Common job board URLs for direct scraping
            fallback_urls = [
                f"https://www.naukri.com/{role.replace(' ', '-').lower()}-jobs-in-{location.replace(' ', '-').lower()}",
                f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')}&location={location.replace(' ', '%20')}",
            ]
            
            for url in fallback_urls:
                self.logger.info(f"Trying fallback URL: {url}")
                scraper = next((s for s in self.scrapers if s.can_handle(url)), None)
                
                if scraper:
                    html = self.firecrawl.scrape_url(url)
                    if html:
                        jobs = scraper.parse(html, url)
                        for job in jobs:
                            job['source_platform'] = scraper.__class__.__name__.replace("Scraper", "")
                            all_jobs.append(job)
                        self.logger.info(f"Found {len(jobs)} jobs from {url}")
            
            if len(all_jobs) == 0:
                self.logger.error("No jobs found from any source. Please provide an RSS feed URL for better results.")
            else:
                self.save_jobs(all_jobs)

    def fetch_jobs(self, url):
        """Legacy method for backward compatibility."""
        html = self.firecrawl.scrape_url(url)
        return html

    def parse_jobs(self, html_content, source_url=""):
        """Legacy method for backward compatibility."""
        scraper = next((s for s in self.scrapers if s.can_handle(source_url)), self.scrapers[0])
        return scraper.parse(html_content, source_url)

    def save_jobs(self, jobs):
        """Saves parsed jobs to the database with descriptions and skill extraction."""
        if not jobs:
            self.logger.info("No jobs to save.")
            return

        conn = get_db_connection()
        c = conn.cursor()
        count = 0
        
        # Import here to avoid circular dependency
        from utils.llm_client import LLMClient
        import json
        
        llm_client = LLMClient()
        
        # Ensure company is not None
        for job in jobs:
            company = job['company'] if job['company'] else "Unknown Company"
            description = job.get('description', '')
            
            # Extract required skills from job description if available
            required_skills = []
            if description:
                try:
                    # Use LLM to extract skills from job description
                    system_prompt = """Extract technical skills and requirements from this job description.
Output strictly in JSON format: {"skills": ["skill1", "skill2", ...]}
Include programming languages, frameworks, tools, and technologies."""
                    
                    user_prompt = f"Extract skills from this job description:\n\n{description[:2000]}"
                    
                    response = llm_client.generate_response(user_prompt, system_prompt=system_prompt)
                    if response:
                        cleaned = response.replace("```json", "").replace("```", "").strip()
                        data = json.loads(cleaned)
                        required_skills = [s.strip().lower() for s in data.get("skills", [])]
                except Exception as e:
                    self.logger.error(f"Error extracting skills from job description: {e}")
            
            try:
                c.execute('''
                    INSERT OR IGNORE INTO jobs (title, company, location, url, description, required_skills)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (job['title'], company, job['location'], job['url'], description, json.dumps(required_skills)))
                if c.rowcount > 0:
                    count += 1
            except Exception as e:
                self.logger.error(f"Error saving job {job['title']}: {e}")

        conn.commit()
        conn.close()
        self.logger.info(f"Saved {count} new jobs to database.")

