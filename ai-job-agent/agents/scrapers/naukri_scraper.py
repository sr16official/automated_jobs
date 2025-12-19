from bs4 import BeautifulSoup
import logging
import json
from .base_scraper import BaseScraper

class NaukriScraper(BaseScraper):
    """
    Scraper specialized for Naukri.com listings.
    Note: Naukri often uses JSON-LD or complex JS. This parser focuses on extracted HTML/Markdown.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("NaukriScraper")

    def can_handle(self, url: str) -> bool:
        return "naukri.com" in url

    def parse(self, html_content: str, source_url: str) -> list:
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # Naukri's layout is complex; this is a heuristic-based parser for search results or single pages
        # If firecrawl provides clean markdown, it's easier. But for HTML:
        
        # Look for script tags containing job data (common in Naukri)
        # Search for "application/ld+json" for JobPosting
        json_ls = soup.find_all('script', type='application/ld+json')
        for tag in json_ls:
            try:
                data = json.loads(tag.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    jobs.append({
                        "title": data.get('title'),
                        "company": data.get('hiringOrganization', {}).get('name'),
                        "location": data.get('jobLocation', {}).get('address', {}).get('addressLocality'),
                        "url": source_url
                    })
                    return jobs # If we found structured data, return it
            except:
                continue

        # Fallback to selector-based parsing (simplified)
        items = soup.find_all('div', class_='cust-job-tuple') or soup.find_all('article', class_='jobTuple')
        
        for item in items:
            try:
                title_tag = item.find('a', class_='title')
                company_tag = item.find('a', class_='comp-name') or item.find('div', class_='companyInfo')
                loc_tag = item.find('span', class_='locWraper') or item.find('li', class_='location')
                
                if title_tag:
                    jobs.append({
                        "title": title_tag.text.strip(),
                        "company": company_tag.text.strip() if company_tag else "Unknown",
                        "location": loc_tag.text.strip() if loc_tag else "Unknown",
                        "url": title_tag.get('href')
                    })
            except Exception as e:
                self.logger.warning(f"Failed to parse Naukri job item: {e}")

        return jobs
