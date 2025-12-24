from bs4 import BeautifulSoup
import logging
import re
from .base_scraper import BaseScraper

class RSSScraper(BaseScraper):
    """
    Scraper specialized for parsing job postings from RSS feeds.
    Extracts company names from job titles.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("RSSScraper")

    def can_handle(self, url: str) -> bool:
        # This is a generic XML/RSS scraper
        return url.endswith(".xml") or "rss" in url.lower() or "feed" in url.lower()

    def extract_company_from_title(self, title: str) -> str:
        """
        Extracts company name from job title.
        Handles patterns like:
        - "Company hiring Role in Location"
        - "Company Name hiring Role"
        - "Role at Company"
        """
        # Pattern 1: "Company hiring..." or "Company Name hiring..."
        hiring_match = re.match(r'^(.+?)\s+hiring\s+', title, re.IGNORECASE)
        if hiring_match:
            company = hiring_match.group(1).strip()
            # Clean up common suffixes
            company = re.sub(r'\s+(Inc\.|Ltd\.|LLC|Corp\.|Corporation)$', '', company, flags=re.IGNORECASE)
            return company
        
        # Pattern 2: "Role at Company"
        at_match = re.search(r'\s+at\s+(.+?)(?:\s+in\s+|\s*$)', title, re.IGNORECASE)
        if at_match:
            company = at_match.group(1).strip()
            return company
        
        # Pattern 3: Try to extract from description or use first part before " - "
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) >= 2:
                # Often format is "Company - Role"
                potential_company = parts[0].strip()
                if len(potential_company) < 50:  # Reasonable company name length
                    return potential_company
        
        # Fallback: return "Unknown Company"
        return "Unknown Company"

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
                
                # Extract company from title
                company = self.extract_company_from_title(title)
                
                # Try to extract location from title
                location = "Remote / Multiple"
                
                # Pattern: "... in Location"
                location_match = re.search(r'\s+in\s+([^,]+(?:,\s*[^,]+)*)', title, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).strip()
                elif item.find('category'):
                    location = item.find('category').text.strip()

                # Try to extract description/content
                description = ""
                if item.find('description'):
                    description = item.find('description').text.strip()
                elif item.find('content'):
                    description = item.find('content').text.strip()
                elif item.find('summary'):
                    description = item.find('summary').text.strip()
                
                # Clean HTML tags from description if present
                if description:
                    desc_soup = BeautifulSoup(description, 'html.parser')
                    description = desc_soup.get_text(separator=' ', strip=True)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": link,
                    "description": description,
                    "source_platform": "RSS"
                })
                
                self.logger.debug(f"Extracted: {company} - {title}")
                
            except Exception as e:
                self.logger.warning(f"Failed to parse RSS item: {e}")

        self.logger.info(f"Parsed {len(jobs)} jobs from RSS feed")
        return jobs
