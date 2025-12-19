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
        if rss_url:
            self.fetch_from_rss(rss_url)
            # We can still run discovery in addition to RSS if desired, 
            # or just skip if RSS is provided.
            # For now, let's do both to maximize results.
        platforms = ["greenhouse.io", "naukri.com", "linkedin.com/jobs", "wellfound.com"]
        self.logger.info(f"Starting search for '{role}' in '{location}'...")
        
        # 1. Discover URLs via Firecrawl
        urls = self.firecrawl.search_jobs(role, location, platforms)
        
        if not urls:
            self.logger.warning("No URLs discovered.")
            return

        all_jobs = []
        for url in urls:
            # 2. Find a matching scraper
            scraper = next((s for s in self.scrapers if s.can_handle(url)), None)
            
            if scraper:
                # 3. Fetch content and parse
                html = self.firecrawl.scrape_url(url)
                if html:
                    jobs = scraper.parse(html, url)
                    for job in jobs:
                        # Add metadata
                        job['source_platform'] = scraper.__class__.__name__.replace("Scraper", "")
                        all_jobs.append(job)
            else:
                self.logger.info(f"No specific scraper for {url}, skipping.")

        # 4. Save to DB
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
        """Saves parsed jobs to the database."""
        if not jobs:
            self.logger.info("No jobs to save.")
            return

        conn = get_db_connection()
        c = conn.cursor()
        count = 0
        
        # Ensure company is not None
        for job in jobs:
            company = job.get('company') or "Unknown Company"
            try:
                c.execute('''
                    INSERT OR IGNORE INTO jobs (title, company, location, url)
                    VALUES (?, ?, ?, ?)
                ''', (job['title'], company, job['location'], job['url']))
                if c.rowcount > 0:
                    count += 1
            except Exception as e:
                self.logger.error(f"Error saving job {job['title']}: {e}")

        conn.commit()
        conn.close()
        self.logger.info(f"Saved {count} new jobs to database.")
