from bs4 import BeautifulSoup
import logging
import json
from .base_scraper import BaseScraper

class LinkedInScraper(BaseScraper):
    """
    Scraper specialized for LinkedIn job postings.
    Expects HTML content fetched via Firecrawl or similar to bypass auth gates.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("LinkedInScraper")

    def can_handle(self, url: str) -> bool:
        return "linkedin.com/jobs" in url or "linkedin.com/search" in url

    def parse(self, html_content: str, source_url: str) -> list:
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # Attempt to parse JobPosting structured data
        json_ls = soup.find_all('script', type='application/ld+json')
        for tag in json_ls:
            try:
                data = json.loads(tag.string)
                # LinkedIn sometimes wraps it in a list or graph
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    items = []

                for item in items:
                    if item.get('@type') == 'JobPosting':
                        jobs.append({
                            "title": item.get('title'),
                            "company": item.get('hiringOrganization', {}).get('name'),
                            "location": item.get('jobLocation', {}).get('address', {}).get('addressLocality'),
                            "url": source_url
                        })
                        if jobs: return jobs
            except:
                continue

        # Fallback to selector-based (LinkedIn public layout)
        # Search results
        postings = soup.find_all('div', class_='base-search-card') or soup.find_all('li', class_='result-card')
        for post in postings:
            try:
                title_tag = post.find('h3', class_='base-search-card__title') or post.find('h3')
                company_tag = post.find('a', class_='hidden-nested-link') or post.find('h4')
                loc_tag = post.find('span', class_='job-search-card__location') or post.find('span', class_='job-result-card__location')
                link_tag = post.find('a', class_='base-card__full-link') or post.find('a')

                if title_tag:
                    jobs.append({
                        "title": title_tag.text.strip(),
                        "company": company_tag.text.strip() if company_tag else "Unknown",
                        "location": loc_tag.text.strip() if loc_tag else "Unknown",
                        "url": link_tag.get('href') if link_tag else source_url
                    })
            except Exception as e:
                self.logger.warning(f"Failed to parse LinkedIn job item: {e}")

        return jobs
