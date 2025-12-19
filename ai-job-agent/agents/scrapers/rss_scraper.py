from bs4 import BeautifulSoup
import logging
from .base_scraper import BaseScraper

class RSSScraper(BaseScraper):
    """
    Scraper specialized for parsing job postings from RSS feeds.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("RSSScraper")

    def can_handle(self, url: str) -> bool:
        # This is a generic XML/RSS scraper
        return url.endswith(".xml") or "rss" in url.lower() or "feed" in url.lower()

    def parse(self, xml_content: str, source_url: str) -> list:
        if not xml_content:
            return []

        # Use 'xml' parser if available, otherwise 'html.parser'
        soup = BeautifulSoup(xml_content, 'xml')
        items = soup.find_all('item')
        
        # Some feeds use 'entry' (Atom)
        if not items:
            items = soup.find_all('entry')

        jobs = []
        for item in items:
            try:
                # Standard RSS fields
                title = item.find('title').text.strip() if item.find('title') else "Unknown Title"
                link = item.find('link').text.strip() if item.find('link') else source_url
                
                # Try to extract company and location from title or description if possible
                # LinkedIn RSS often has "Role at Company" format
                company = "LinkedIn Job"
                if " at " in title:
                    parts = title.split(" at ")
                    title = parts[0].strip()
                    company = parts[1].split(" in ")[0].strip() if " in " in parts[1] else parts[1].strip()

                location = "Remote / Multiple"
                if " in " in title:
                    location = title.split(" in ")[-1].strip()
                elif item.find('category'):
                    location = item.find('category').text.strip()

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": link,
                    "source_platform": "RSS"
                })
            except Exception as e:
                self.logger.warning(f"Failed to parse RSS item: {e}")

        return jobs
