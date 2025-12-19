from bs4 import BeautifulSoup
import logging
import json
from .base_scraper import BaseScraper

class WellfoundScraper(BaseScraper):
    """
    Scraper specialized for Wellfound (formerly AngelList).
    """
    
    def __init__(self):
        self.logger = logging.getLogger("WellfoundScraper")

    def can_handle(self, url: str) -> bool:
        return "wellfound.com" in url or "angel.co" in url

    def parse(self, html_content: str, source_url: str) -> list:
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # Wellfound often uses a NEXT_DATA script for its state
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            try:
                data = json.loads(next_data.string)
                # Note: Navigating __NEXT_DATA__ requires specific knowledge of the schema 
                # which changes often. This is a simplified fallback.
            except:
                pass

        # Selector-based fallback
        postings = soup.find_all('div', class_='styles_result__') or soup.find_all('div', class_='job-listing')
        for post in postings:
            try:
                title_tag = post.find('h4') or post.find('div', class_='styles_title__')
                company_tag = post.find('span', class_='styles_name__') or post.find('div', class_='styles_companyName__')
                loc_tag = post.find('span', class_='styles_location__')
                link_tag = post.find('a')

                if title_tag:
                    jobs.append({
                        "title": title_tag.text.strip(),
                        "company": company_tag.text.strip() if company_tag else "Unknown",
                        "location": loc_tag.text.strip() if loc_tag else "Unknown",
                        "url": link_tag.get('href') if link_tag else source_url
                    })
            except Exception as e:
                self.logger.warning(f"Failed to parse Wellfound job item: {e}")

        return jobs
